# Decoding legacy `.ghuser` files (no Rhino required)

How to recover component metadata, parameter names/descriptions, and embedded Python/C# source
from the binary legacy `.ghuser` archives in `carcara-old/carcara/` using only CPython — no
Rhino, no Grasshopper, no `GH_IO.dll`. Verified working against the Carcara legacy set
(ScatterPlot, LinePlot, Heatmap recovered with this technique, 2026-06-11).

> Scope note: this is a **read-only inspection** technique for the rebuild. It never replaces
> the build pipeline — new `.ghuser` files are still produced exclusively by
> `build_userobjects.py` (see [`componentizer.md`](componentizer.md)). And `carcara-old/` stays
> untouched: copy bytes out, never write back.

---

## File format summary

A `.ghuser` is a binary `GH_Archive` (GH_IO serialization). Layered like an onion:

```
file bytes
└── raw DEFLATE stream (zlib wbits=-15), starts at byte 0
    └── GH_IO binary chunk tree, root chunk "UserObject"
        ├── plain items: Name, NickName, Description, Category, Exposure, icon PNG…
        │   (strings are .NET 7-bit-length-prefixed UTF-8 → readable after inflate)
        └── ONE of:
            ├── script component → source stored as ONE LONG BASE64 RUN in the archive
            └── "ClusterDocument" chunk → nested raw DEFLATE stream (a GH "Document"
                archive = a whole internalized GH definition) containing:
                ├── cluster hook params (CustomName/CustomNickName/CustomDescription)
                ├── native components (GUID + Name pairs)
                └── embedded script components → again base64 runs
```

Key facts learned the hard way:

- **Not a zip.** Don't try `unzip`/`tar`. Don't look for gzip magic (`\x1f\x8b`) — it's
  headerless raw deflate.
- The outer stream inflates cleanly from **offset 0** with `wbits=-15`.
- The nested `ClusterDocument` stream does **not** start right after the chunk name — scan
  forward byte-by-byte until a stream inflates to something starting with `\x08Document`.
- Nested streams often **error partway** ("invalid stored block lengths") because the byte-array
  slice runs past the stream end. Inflate in small steps and **keep the partial output** — it
  contains everything useful.
- Script source inside the archive (and inside cluster documents) is stored **base64-encoded**,
  so grepping the inflated bytes for `import` / `using System` finds nothing. Grep for long
  base64 runs instead and decode them.
- The chart-style legacy components (`ScatterPlot`, `LinePlot`, `Heatmap`) are **clusters**, not
  script components. `LinePlot`/`Heatmap` carry one embedded Python script each; `ScatterPlot`
  is pure native wiring (recover its interface from the hook params instead).

---

## Recipe

Run from the repo root with any CPython 3.x (stdlib only).

### Step 1 — inflate the outer archive

```python
import zlib

def partial_inflate(buf, step=64):
    """Raw-deflate inflate that tolerates running past the stream end.
    Feeds small chunks and keeps whatever decompressed before the error."""
    d = zlib.decompressobj(-15)
    out = bytearray()
    for i in range(0, len(buf), step):
        try:
            out += d.decompress(buf[i:i+step])
        except zlib.error:
            break
        if d.eof:
            break
    return bytes(out)

raw = open("carcara-old/carcara/carcara_<Name>_rXX.ghuser", "rb").read()
archive = partial_inflate(raw)          # starts with b'\nUserObject\xff\xff\xff\xff'
```

### Step 2 — read the plain metadata strings

Strings are length-prefixed UTF-8, so a printable-run scan is enough to read Name, NickName,
Description, Category, etc.:

```python
import re
for m in re.finditer(rb'[\x20-\x7e]{4,}', archive):
    print(m.start(), m.group().decode())
```

Useful markers in the output:
- `Description` followed by the component description (first byte of the value is the 7-bit
  length prefix — may render as a stray character like `Q` or `;` before the text).
- `ClusterDocument` present → it's a cluster, go to Step 4.
- `ScriptComponentVersion` / `ScriptParamAccess` / `TypeHintID` → script component params.

### Step 3 — extract embedded script source (base64)

Works on the outer archive AND on nested cluster documents:

```python
import base64
for run in re.findall(rb'[A-Za-z0-9+/=]{100,}', archive):
    src = base64.b64decode(run + b'=' * (-len(run) % 4))
    if src[:1] in (b'"', b'#', b'i', b'u'):      # docstring / comment / import / using
        print(src.decode('utf-8', errors='replace'))
```

The decoded text is the verbatim script (Python with `\r\n`, or C# for C# script components).
Icon PNGs also live in the archive but are binary items, not base64 — ignore them (they trip
up naive base64 scans only if you lower the run-length threshold too far; keep it ≥100).

### Step 4 — clusters: inflate the nested `ClusterDocument`

```python
idx = archive.find(b'ClusterDocument')
doc = b''
for off in range(idx, idx + 400):                     # stream starts ~27 bytes after the name
    cand = partial_inflate(archive[off:off + 200])
    if len(cand) > 100 and b'Document' in cand[:20]:  # found stream start
        doc = partial_inflate(archive[off:])          # now inflate everything (partial is OK)
        break
```

`doc` is a full GH "Document" archive. Apply Step 2 (strings) and Step 3 (base64 scripts) to it.

### Step 5 — clusters: recover the interface and internals

From the `doc` string dump:

- **Cluster input/output hooks** — look for `CustomName` / `CustomNickName` /
  `CustomDescription` items; the value string follows each marker. These give the exact
  user-facing param names and descriptions of the cluster.
- **Internal component types** — each `Object` chunk has a `GUID` item followed by a `Name`
  item whose value is the component's human name (`Merge`, `Clean Tree`, `Save SVG`,
  `Text to SVG`, native params like `Number`/`Colour`/`Rectangle`…). Sequence-scan:

```python
lines = [(m.start(), m.group().decode())
         for m in re.finditer(rb'[\x20-\x7e]{4,}', doc)]
for i, (_, s) in enumerate(lines):
    if s == "GUID" and i + 2 < len(lines) and lines[i+1][1] == "Name":
        print(lines[i+2][1])        # component type name
```

- **Embedded scripts** — Step 3 on `doc` recovers them verbatim (this is how the legacy
  LinePlot/Heatmap sources were extracted).

---

## Deeper nesting: Object → inner UserObject → ClusterDocument

Most legacy Carcara `.ghuser` files add one extra level of nesting that is **not** visible
in the file-format summary above. Instead of embedding the script or ClusterDocument
directly inside the outer UserObject, the outer archive contains a single `Object` chunk
whose payload is a second (inner) UserObject archive. The script source or ClusterDocument
lives inside that inner archive:

```
file bytes → raw deflate (wbits=-15)
└── outer UserObject archive
    └── Object chunk  (find via b'\x06Object' — plain b'Object' false-hits "UserObject")
        └── inner raw deflate stream  (scan forward; accept candidate that inflates to
            |                          something starting with b'\nUserObject')
            └── inner UserObject archive
                ├── ONE of:
                │   ├── script component → base64 run in the inner archive directly
                │   └── ClusterDocument chunk → scan forward for nested deflate that
                │       starts with b'\x08Document'
                └── (for clusters) GH Document archive — scripts as base64 runs
```

**Finding the Object chunk.** Search for the byte sequence `b'\x06Object'` (the `\x06` is
the 7-bit length prefix for the 6-character string). Do **not** use a plain `b'Object'`
search — it will match `UserObject` at offset 5 as a false positive.

**Probe window for stream detection.** When scanning forward from the `\x06Object` position
for the inner deflate stream, use a **300-byte probe window** for the candidate inflate
(not 200). Some embedded archives have high compression ratios and require at least 250
compressed bytes before the output grows past the 100-byte detection threshold.

Components already decoded by `tools/decode_ghuser.py` (like Heatmap, LinePlot,
ScatterPlot) happen to have `ClusterDocument` bytes that propagate into the outer inflate
output, so the old direct-search path found them. The remaining 24 components only expose
the inner archive via the `Object` chunk; they are silent to a `ClusterDocument` scan of
the outer archive.

---

## Base64 length-prefix misalignment

The .NET `GH_Archive` serializer stores each script as a base64-encoded string
with a **7-bit length-prefix byte** prepended. This prefix byte is itself in the
base64 alphabet (`A`–`z`, `0`–`9`, `+`, `/`, `=`), so a naïve regex match like
`[A-Za-z0-9+/=]{100,}` captures one extra leading character — the prefix byte —
and the subsequent `base64.b64decode` call produces bit-shifted garbage.

**Fix: try trims 0, 1, 2, 3 on each candidate run.** For each long base64 run, strip
0, 1, 2, or 3 leading characters, pad to a multiple of 4 with `=`, and decode. Accept
the trim that produces a result with ≥ 85 % printable-ASCII content whose first byte
looks like source code (`"`, `#`, `i` for `import`, `u` for `using`, `\r`/`\n`).

```python
_SRC_FIRST_BYTES = (b'"', b'#', b'i', b'u', b'\r', b'\n')

def _try_decode_run(run: bytes) -> str | None:
    best_ratio, best_src = 0.0, None
    for trim in range(4):
        r = run[trim:]
        try:
            decoded = base64.b64decode(r + b'=' * (-len(r) % 4))
        except Exception:
            continue
        if len(decoded) < 50 or decoded[:1] not in _SRC_FIRST_BYTES:
            continue
        ratio = sum(32 <= b <= 126 for b in decoded) / len(decoded)
        if ratio >= 0.85 and ratio > best_ratio:
            best_ratio, best_src = ratio, decoded.decode('utf-8', errors='replace')
    return best_src
```

Apply this to every level — the outer archive, the inner UserObject, and the
ClusterDocument — because the misalignment occurs at every level.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| No printable strings ≥40 chars in the raw file | Expected — file is deflate-compressed. Inflate first (Step 1). |
| `zlib.error: invalid stored block lengths` mid-inflate | Stream slice runs past its end. Use `partial_inflate` (small steps, keep partial output). |
| `gzip.decompress` fails / no `\x1f\x8b` magic | It's raw deflate (`wbits=-15`), not gzip. Any `\x1f\x8b` hits are coincidental binary noise. |
| `import` / `using System` not found anywhere | Source is base64-encoded — Step 3. |
| Nested stream not found right after `ClusterDocument` | Stream starts a couple dozen bytes later (after the item header). Scan offsets (Step 4). |
| Cluster found but no script inside | Pure native-GH cluster (e.g., legacy ScatterPlot). Recover the interface from hook params (Step 5) and describe the wiring as pseudocode. |
| `ClusterDocument` search finds nothing in the outer archive | The component uses the deeper Object→inner-UserObject nesting. Inflate the inner UserObject first (see [Deeper nesting](#deeper-nesting-object--inner-userobject--clusterdocument)), then search for `ClusterDocument` there. |
| Inner UserObject inflate returns 0 or < 100 bytes with a 200-byte probe window | The compressed inner archive is dense. Use a **300-byte probe window** for candidate detection. |
| Base64 decode produces binary garbage, not Python source | Off-by-one from the .NET length-prefix byte. Try trims 0–3 and pick the result with the highest printable-ASCII ratio (see [Base64 misalignment](#base64-length-prefix-misalignment)). |

---

## Where the results go

Decoded sources and interfaces are pasted into the per-subcategory capture files in
`carcara-old/ghuser-metadata/` (`01.Modeling.md` … `04.Dataviz.md`), which feed the
[Component Inventory](../CLAUDE.md#component-inventory) and the rebuild. Paste scripts
**verbatim**; for native-wiring clusters, record the hook table + a pseudocode block (see the
`ScatterPlot` section of `04.Dataviz.md` for the reference format).

Clean up any temp dump folders afterward — decoded blobs must not be committed.
