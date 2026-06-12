"""Verify window=300 fixes all the empty files that have inner UOs."""
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
BASE64_RUN = re.compile(rb'[A-Za-z0-9+/=]{100,}')
_SRC_FIRST_BYTES = (b'"', b"#", b"i", b"u", b"\r", b"\n")
_OBJECT_CHUNK = b"\x06Object"

def find_inner_userobject_v2(archive, window=300):
    """Find inner UserObject with larger window."""
    idx = archive.find(_OBJECT_CHUNK)
    if idx == -1:
        return b""
    for off in range(idx, min(idx + 400, len(archive))):
        cand = partial_inflate(archive[off:off+window])
        if len(cand) > 100 and b'UserObject' in cand[:30]:
            return partial_inflate(archive[off:])
    return b""

def try_extract(blob):
    scripts = []
    for m in BASE64_RUN.finditer(blob):
        run = m.group()
        for trim in range(4):
            r = run[trim:]
            try:
                decoded = base64.b64decode(r + b'=' * (-len(r) % 4))
                if len(decoded) < 50: continue
                if decoded[:1] not in _SRC_FIRST_BYTES: continue
                ratio = sum(32 <= b <= 126 for b in decoded) / len(decoded)
                if ratio >= 0.85:
                    scripts.append(decoded[:80])
                    break
            except: pass
    return scripts

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
    raw = open(path, 'rb').read()
    archive = partial_inflate(raw)

    inner = find_inner_userobject_v2(archive, window=300)
    if not inner:
        print(f"{name:40s}: NO INNER UO EVEN WITH WINDOW 300")
        continue

    scripts = try_extract(inner)
    has_cd = b'ClusterDocument' in inner

    print(f"{name:40s}: inner={len(inner)}, scripts={len(scripts)}, has_cd={has_cd}")
    for s in scripts[:1]:
        print(f"    first script: {s}")
