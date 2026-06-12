"""Debug why 9 files are still EMPTY after the fix."""
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

_OBJECT_CHUNK = b"\x06Object"
BASE64_RUN = re.compile(rb'[A-Za-z0-9+/=]{100,}')
_SRC_FIRST_BYTES = (b'"', b"#", b"i", b"u", b"\r", b"\n")

def find_inner_userobject(archive):
    idx = archive.find(_OBJECT_CHUNK)
    if idx == -1:
        return b""
    for off in range(idx, min(idx + 400, len(archive))):
        cand = partial_inflate(archive[off:off+200])
        if len(cand) > 100 and b"UserObject" in cand[:30]:
            return partial_inflate(archive[off:])
    return b""

def try_extract_scripts(blob):
    results = []
    for m in BASE64_RUN.finditer(blob):
        run = m.group()
        for trim in range(4):
            r = run[trim:]
            try:
                decoded = base64.b64decode(r + b'=' * (-len(r) % 4))
                if len(decoded) < 50:
                    continue
                if decoded[:1] not in _SRC_FIRST_BYTES:
                    continue
                ratio = sum(32 <= b <= 126 for b in decoded) / len(decoded)
                if ratio >= 0.85:
                    results.append((trim, ratio, decoded[:80]))
                    break
            except Exception:
                pass
    return results

LEGACY_DIR = Path("carcara-old/carcara")

still_empty = [
    "carcara_BuildingMeshes_r03.ghuser",
    "carcara_ColorCalculator_r00.ghuser",
    "carcara_ConnectionString_r03.ghuser",
    "carcara_CurveDisplay_r02.ghuser",
    "carcara_GrasshopperGeometryToWKT_r02.ghuser",
    "carcara_IdentifyDuplicatePolylines_r03.ghuser",
    "carcara_RunODBCQuery_rev03.ghuser",
    "carcara_SRID_r00.ghuser",
    "carcara_WKTtoGrasshopperGeometry_r02.ghuser",
]

for fname in still_empty:
    path = LEGACY_DIR / fname
    name = fname.replace('carcara_', '').split('_r')[0].split('_rev')[0]
    print(f"\n{'='*60}")
    print(f"DEBUG: {name}")

    raw = open(path, 'rb').read()
    outer = partial_inflate(raw)
    print(f"Outer ({len(outer)} bytes): {outer[:20]}")

    # Scripts in outer
    outer_scripts = try_extract_scripts(outer)
    print(f"Scripts in outer: {len(outer_scripts)}")

    # Inner UO
    inner = find_inner_userobject(outer)
    print(f"Inner UO ({len(inner)} bytes): {inner[:30] if inner else 'NOT FOUND'}")

    if inner:
        # Scripts in inner
        inner_scripts = try_extract_scripts(inner)
        print(f"Scripts in inner: {len(inner_scripts)}")
        for trim, ratio, first80 in inner_scripts[:3]:
            print(f"  trim={trim} ratio={ratio:.2f}: {first80}")

        # Any Object chunk in inner?
        inner_obj = inner.find(_OBJECT_CHUNK)
        print(f"Object chunk in inner at: {inner_obj}")
        if inner_obj != -1:
            print(f"  Context around Object: {inner[inner_obj-5:inner_obj+30]}")
            # Try to inflate inner UO from inner
            inner2 = find_inner_userobject(inner)
            print(f"Inner2 UO ({len(inner2)} bytes): {inner2[:30] if inner2 else 'NOT FOUND'}")
            if inner2:
                inner2_scripts = try_extract_scripts(inner2)
                print(f"Scripts in inner2: {len(inner2_scripts)}")
                for trim, ratio, first80 in inner2_scripts[:3]:
                    print(f"  trim={trim} ratio={ratio:.2f}: {first80}")

        # ClusterDocument in inner?
        cd_in_inner = b'ClusterDocument' in inner
        print(f"ClusterDocument in inner: {cd_in_inner}")
