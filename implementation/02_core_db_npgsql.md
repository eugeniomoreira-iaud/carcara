# C# Migration — Phase 02: csharp_shared/Db.cs — Npgsql Port

## Goal

Port all database logic from `carcara/crc_modules/db/` into the shared C# source file
`grasshopper/csharp_shared/Db.cs`. This file is concatenated into every C# component
that needs DB access at build time — no compiled DLL, no project reference. The Python
source files are the authoritative behavioral spec; port logic and SQL templates
verbatim.

## Depends on

- Phase 01 complete (`componentize_cs.py` extended; `#r "nuget: Npgsql"` confirmed
  working in Rhino 8 via the `CRC_HelloDB` validation gate).

## Python behavioral specs (read these before writing C#)

| C# location in Db.cs | Python spec |
|---|---|
| `ConnectionString` static class | `carcara/crc_modules/db/connection.py` |
| `QueryRunner` static class | `carcara/crc_modules/db/query.py` |
| `SpatialQuery` static class | `carcara/crc_modules/db/spatial_query.py` |
| `Writer` static class | `carcara/crc_modules/db/writer.py` |

---

## Scope

`Db.cs` is a **standalone C# file** (no `using` at file top — those are hoisted by
the concat step, or included inside the file after a convention established in Phase 02).
It declares `#r "nuget: Npgsql, 8.*"` at the very top (the concat step deduplicates).

### `ConnectionString` class

Public API mirrors `connection.py`:
```csharp
static class ConnectionString
{
    public static string Build(string host, int port, string database,
                               string user, string password);
    public static NpgsqlConnectionStringBuilder Parse(string cstring);
    public static (bool ok, string message) TestConnection(string cstring);
}
```
`Build` produces a libpq-style conninfo string with the password encoded (base64
obfuscation — same scheme as the Python version; must round-trip with `Parse`).
`TestConnection` opens and immediately closes a connection; returns
`(true, "Connection successful")` or `(false, error_message)`.

### `QueryRunner` class

```csharp
static class QueryRunner
{
    public static (List<object[]> rows, List<string> columns)
        RunQuery(string cstring, string sql);

    public static int RunCommand(string cstring, string sql);
}
```
`RunQuery` executes a SELECT; returns rows as `List<object[]>` and column names as
`List<string>`. `RunCommand` executes non-SELECT; returns affected row count. Both
throw `NpgsqlException` on DB failure (the GH component layer catches).
Connection-per-call model: open, execute, close — same as Python. No pooling.

### `SpatialQuery` class

Port `spatial_query.py` functions:
```csharp
static class SpatialQuery
{
    public static (List<string> wktGeometries, List<object> primaryKeys)
        GetGeometries(string cstring, string schema, string table,
                      string cx = "0", string cy = "0",
                      string where = null, int srid = 4326);

    public static (List<string> wktGeometries, List<object> primaryKeys)
        GetGeometriesWithSpatialFilter(string cstring, string schema, string table,
                                       string filterWkt,
                                       string cx = "0", string cy = "0",
                                       int srid = 4326, string sqlFilter = null);

    public static (List<object[]> rows, List<string> columnNames)
        GetValuesWithSpatialFilter(string cstring, string schema, string table,
                                   List<string> columns, string filterWkt,
                                   string cx = "0", string cy = "0",
                                   int srid = 4326, string sqlFilter = null);
}
```
SQL templates are ported verbatim from `spatial_query.py`. Auto-detection of geometry
column uses the `geometry_columns` view. PK detection uses
`information_schema.table_constraints` + `key_column_usage`. `ORDER BY` PK applied
where detected.

Coordinate correction: `ST_Translate(<geom_expr>, -cx, -cy)` on read, injected as
text — **never** `double.Parse(cx)`. Call `Utils.ValidateOffset(cx)` (Phase 07,
but write a local stub in this file until Utils.cs exists) before SQL injection.

### `Writer` class

Port `writer.py`:
```csharp
static class Writer
{
    public static (bool ok, string message)
        CreateTable(string cstring, string schema, string table,
                    List<(string name, string type)> columns);

    public static (bool ok, string message)
        CreateShapefile(string cstring, string schema, string table,
                        List<string> localWktGeometries,
                        List<object[]> attributeRows,
                        List<string> attributeColumns,
                        string cx = "0", string cy = "0", int srid = 4326);
}
```
`CreateShapefile` applies `ST_Translate(ST_GeomFromText(<wkt>, srid), cx, cy)` on
write (add correction back to projected). `cx`/`cy` are text, never parsed to double.

---

## Key Decisions

- **Npgsql version**: declare `#r "nuget: Npgsql, 8.*"` (latest stable 8.x confirmed
  working in Phase 01). If Phase 01 found a different version that works, use that.
- **Password encoding**: `Convert.ToBase64String(Encoding.UTF8.GetBytes(password))`.
  `Parse` decodes before handing to `NpgsqlConnectionStringBuilder`. Same
  encode/decode symmetry as `connection.py`.
- **SQL injection safety**: `cx`/`cy` validated as numeric text via `ValidateOffset`
  before embedding. Column/schema/table names quoted with `"` (double quotes).
  Row filter values go through Npgsql `@param` parameterization — never string-formatted.
- **`Utils` dependency**: `Db.cs` calls `ValidateOffset` and `TranslateExpr` from
  `Utils.cs` (Phase 07). During Phase 02, write a local stub with the same signature;
  replace with the real call once `Utils.cs` is written in Phase 07.

---

## Steps

1. Read `carcara/crc_modules/db/connection.py` — implement `ConnectionString` class
   in `Db.cs`. Run Python tests (`test_connection.py`) to confirm what the contract is.

2. Read `carcara/crc_modules/db/query.py` — implement `QueryRunner`.

3. Read `carcara/crc_modules/db/spatial_query.py` line by line — implement
   `SpatialQuery`. Port SQL templates verbatim.

4. Read `carcara/crc_modules/db/writer.py` — implement `Writer`.

5. Wire `Db.cs` into `CRC_HelloDB` (or a new throwaway `CRC_DBSmoke` component)
   to smoke-test the classes without a full component port. The component can call
   `QueryRunner.RunQuery(CString, "SELECT current_database()")` and output the result.

6. Once Phases 02–07 are all written, replace the `ValidateOffset` stub with the
   real `Utils.ValidateOffset` call.

---

## Validation

No .NET unit tests at this phase. Validation paths:

**Python oracle**: run the Python pytest suite (which exercises `crc_modules/db/`)
to understand expected behavior. Port assertions to manual canvas tests.

**Canvas smoke test**: build a throwaway component (or extend `CRC_HelloDB`) that:
- Calls `ConnectionString.Build(...)` → outputs the CString.
- Calls `QueryRunner.RunQuery(cstring, "SELECT schema_name FROM information_schema.schemata")`
  → outputs schema list.
- Calls `SpatialQuery.GetGeometries(...)` on a known table → outputs WKT list.

**pytest**:
```powershell
conda run -n carcara pytest tests/test_connection.py tests/test_query.py -v
```
These test the Python spec; use them as the behavioral oracle for parity checks.

---

## Done when

- [ ] `grasshopper/csharp_shared/Db.cs` written with `ConnectionString`, `QueryRunner`,
      `SpatialQuery`, `Writer` classes.
- [ ] `#r "nuget: Npgsql, 8.*"` declared at top of `Db.cs`.
- [ ] `ConnectionString.Build/Parse/TestConnection` logic matches `connection.py`.
- [ ] `QueryRunner.RunQuery/RunCommand` logic matches `query.py`.
- [ ] `SpatialQuery` SQL templates match `spatial_query.py` originals.
- [ ] `Writer.CreateTable/CreateShapefile` logic matches `writer.py`.
- [ ] `cx`/`cy` are never `double.Parse`d anywhere in `Db.cs`.
- [ ] Canvas smoke test passes on a live PostGIS connection.
- [ ] Python pytest suite still passes (no regressions in crc_modules).
