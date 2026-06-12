"""Check structure of currently-working OK files."""
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

ok_files = [
    "carcara_CreateTable_r03.ghuser",
    "carcara_Heatmap_rev00.ghuser",
    "carcara_Histogram_r01.ghuser",
    "carcara_LinePlot_r00.ghuser",
    "carcara_NurbsToSVG_rev03.ghuser",
    "carcara_QueryValues_rev03.ghuser",
    "carcara_ScatterPlot_r03.ghuser",
    "carcara_ValuesWithSpatialFilter_rev03.ghuser",
]

for fname in ok_files:
    path = LEGACY_DIR / fname
    name = fname.replace('carcara_', '').split('_r')[0].split('_rev')[0]

    raw = open(path, 'rb').read()
    archive = partial_inflate(raw)

    has_obj = b'\x06Object' in archive
    has_cd_direct = b'ClusterDocument' in archive
    has_inner_uo = False

    if has_obj:
        obj_idx = archive.find(b'\x06Object')
        for off in range(obj_idx, min(obj_idx + 400, len(archive))):
            cand = partial_inflate(archive[off:off+200])
            if len(cand) > 50 and b'UserObject' in cand[:30]:
                has_inner_uo = True
                break

    print(f"{name:40s} has_obj={has_obj} cd_direct={has_cd_direct} inner_uo={has_inner_uo}")
