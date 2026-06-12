"""Investigate inner UserObject for files without inner ClusterDocument."""
import zlib
import re
import base64
from pathlib import Path

def partial_inflate(buf, step=64):
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

LEGACY_DIR = Path("carcara-old/carcara")

# Files without inner ClusterDocument - check what's actually in inner UO
no_cd_files = [
    "carcara_BuildingMeshes_r03.ghuser",
    "carcara_ColorCalculator_r00.ghuser",
    "carcara_ConnectionString_r03.ghuser",
    "carcara_CurveDisplay_r02.ghuser",
    "carcara_GrasshopperGeometryToWKT_r02.ghuser",
    "carcara_IdentifyDuplicatePolylines_r03.ghuser",
    "carcara_OffsetPython_r03.ghuser",
    "carcara_PointInsidePolygon_rev03.ghuser",
    "carcara_RunODBCCommand_rev01.ghuser",
    "carcara_RunODBCQuery_rev03.ghuser",
    "carcara_SaveSVG_r03.ghuser",
    "carcara_SortByContainer_rev03.ghuser",
    "carcara_SQLComposer_rev02.ghuser",
    "carcara_SRID_r00.ghuser",
    "carcara_WKTtoGrasshopperGeometry_r02.ghuser",
]

BASE64_RUN = re.compile(rb'[A-Za-z0-9+/=]{100,}')
PRINTABLE = re.compile(rb'[\x20-\x7e]{4,}')

def try_decode_scripts(blob):
    """Try to extract scripts with trim 0..3."""
    results = []
    for m in BASE64_RUN.finditer(blob):
        run = m.group()
        best = None
        for trim in range(4):
            r = run[trim:]
            try:
                decoded = base64.b64decode(r + b'=' * (-len(r) % 4))
                if len(decoded) < 50:
                    continue
                printable_ratio = sum(32 <= b <= 126 for b in decoded) / len(decoded)
                first_byte = decoded[:1]
                if printable_ratio > 0.85 and first_byte in (b'"', b'#', b'i', b'u', b'\r', b'\n'):
                    if best is None or printable_ratio > best[0]:
                        best = (printable_ratio, trim, decoded)
            except Exception:
                pass
        if best:
            results.append(best)
    return results

for fname in no_cd_files[:5]:  # just first 5 to keep output manageable
    path = LEGACY_DIR / fname
    name = fname.replace('carcara_', '').split('_r')[0].split('_rev')[0]

    raw = open(path, 'rb').read()
    archive = partial_inflate(raw)

    obj_idx = archive.find(b'\x06Object')
    inner = None
    for off in range(obj_idx, min(obj_idx + 400, len(archive))):
        cand = partial_inflate(archive[off:off+200])
        if len(cand) > 50 and b'UserObject' in cand[:30]:
            inner = partial_inflate(archive[off:])
            break

    if not inner:
        print(f"{name}: no inner UO found")
        continue

    print(f"\n{name} - inner UO ({len(inner)} bytes):")
    print(f"  Starts with: {inner[:50]}")

    # Check for more markers in inner
    for marker in [b'ClusterDocument', b'ScriptComponent', b'GH_PythonScript']:
        if marker in inner:
            print(f"  Contains: '{marker.decode()}'")

    # Look at printable strings in inner
    print("  Printable strings in inner (first 1000 bytes):")
    for m in PRINTABLE.finditer(inner[:1000]):
        s = m.group().decode()
        if len(s) > 6:
            print(f"    {m.start()}: {s!r}")

    # Try base64 scripts directly in inner
    scripts = try_decode_scripts(inner)
    print(f"  Scripts found in inner UO (direct): {len(scripts)}")
    for ratio, trim, decoded in scripts[:2]:
        print(f"    trim={trim}, ratio={ratio:.2f}: {decoded[:80]}")

    # Check if inner has Object chunk itself (more nesting)
    inner_obj = inner.find(b'\x06Object')
    if inner_obj != -1:
        print(f"  Inner UO has 'Object' at {inner_obj}, checking deeper nesting...")
        for off in range(inner_obj, min(inner_obj + 400, len(inner))):
            cand = partial_inflate(inner[off:off+200])
            if len(cand) > 50 and (b'UserObject' in cand[:30] or b'Document' in cand[:20]):
                deep = partial_inflate(inner[off:])
                print(f"  Found deeper archive at offset {off} ({len(deep)} bytes): {deep[:40]}")
                deep_scripts = try_decode_scripts(deep)
                print(f"  Scripts in deeper archive: {len(deep_scripts)}")
                for ratio, trim, decoded in deep_scripts[:2]:
                    print(f"    trim={trim}, ratio={ratio:.2f}: {decoded[:80]}")
                break
