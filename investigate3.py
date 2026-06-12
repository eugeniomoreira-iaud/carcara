"""Check all EMPTY ghusers to understand their structure."""
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

# List of EMPTY files from the current run
empty_files = [
    "carcara_BuildingMeshes_r03.ghuser",
    "carcara_CircletoSVG_r03.ghuser",
    "carcara_ColorCalculator_r00.ghuser",
    "carcara_ConnectionString_r03.ghuser",
    "carcara_CreateShapefile_r03.ghuser",
    "carcara_CurveDisplay_r02.ghuser",
    "carcara_FindCorrectionParameters_r03.ghuser",
    "carcara_GeometriesWithSpatialFilter_r03.ghuser",
    "carcara_GeometryEntities_r03.ghuser",
    "carcara_GrasshopperGeometryToWKT_r02.ghuser",
    "carcara_IdentifyDuplicatePolylines_r03.ghuser",
    "carcara_OffsetPython_r03.ghuser",
    "carcara_PointInsidePolygon_rev03.ghuser",
    "carcara_PolylineToSVG_r03.ghuser",
    "carcara_QueryColumnNames_rev03.ghuser",
    "carcara_QuerySchemaNames_r03.ghuser",
    "carcara_QueryTableNames_rev03.ghuser",
    "carcara_RunODBCCommand_rev01.ghuser",
    "carcara_RunODBCQuery_rev03.ghuser",
    "carcara_SaveSVG_r03.ghuser",
    "carcara_SortByContainer_rev03.ghuser",
    "carcara_SQLComposer_rev02.ghuser",
    "carcara_SRID_r00.ghuser",
    "carcara_TextToSVG_rev03.ghuser",
    "carcara_WKTtoGrasshopperGeometry_r02.ghuser",
]

def analyze(filepath):
    raw = open(filepath, 'rb').read()
    archive = partial_inflate(raw)

    # Check for Object chunk
    has_obj = b'\x06Object' in archive
    has_cd_direct = b'ClusterDocument' in archive

    # Try to find inner UserObject via Object chunk
    inner = None
    if has_obj:
        obj_idx = archive.find(b'\x06Object')
        for off in range(obj_idx, min(obj_idx + 400, len(archive))):
            cand = partial_inflate(archive[off:off+200])
            if len(cand) > 50 and b'UserObject' in cand[:30]:
                inner = partial_inflate(archive[off:])
                break

    # Check if inner has ClusterDocument
    inner_has_cd = inner and b'ClusterDocument' in inner if inner else False

    return {
        'has_obj': has_obj,
        'has_cd_direct': has_cd_direct,
        'has_inner_uo': inner is not None,
        'inner_has_cd': inner_has_cd,
        'inner_len': len(inner) if inner else 0,
    }

for fname in empty_files:
    path = LEGACY_DIR / fname
    if not path.exists():
        print(f"MISSING: {fname}")
        continue
    result = analyze(path)
    name = fname.replace('carcara_', '').split('_r')[0].split('_rev')[0]
    flags = []
    if result['has_obj']: flags.append('has_obj')
    if result['has_cd_direct']: flags.append('cd_direct')
    if result['has_inner_uo']: flags.append(f"inner_UO({result['inner_len']})")
    if result['inner_has_cd']: flags.append('inner_CD')
    print(f"{name:40s} {' '.join(flags) if flags else 'no markers'}")
