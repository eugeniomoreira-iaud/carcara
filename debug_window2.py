"""Check the minimum window size needed to detect inner UO for all empty files."""
import zlib
import re
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

_OBJECT_CHUNK = b"\x06Object"

for fname in still_empty:
    path = LEGACY_DIR / fname
    name = fname.replace('carcara_', '').split('_r')[0].split('_rev')[0]
    raw = open(path, 'rb').read()
    archive = partial_inflate(raw)

    obj_idx = archive.find(_OBJECT_CHUNK)
    if obj_idx == -1:
        print(f"{name}: NO Object chunk in archive!")
        continue

    # Find the actual working offset
    found_off = None
    found_window = None
    for off in range(obj_idx, min(obj_idx + 400, len(archive))):
        # Try window 300 (already works for QuerySchemaNames)
        cand = partial_inflate(archive[off:off+300])
        if len(cand) > 100 and b'UserObject' in cand[:30]:
            found_off = off
            # Find minimum window that works
            for w in [100, 150, 200, 250, 300, 400, 500]:
                c = partial_inflate(archive[off:off+w])
                if len(c) > 100 and b'UserObject' in c[:30]:
                    found_window = w
                    break
            break

    if found_off:
        inner = partial_inflate(archive[found_off:])
        print(f"{name:40s}: inner UO at +{found_off-obj_idx} from obj, min_window={found_window}, inner={len(inner)} bytes")
    else:
        print(f"{name:40s}: COULD NOT find inner UO even with window 300!")
