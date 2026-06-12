"""Compare GH_IO chunk structure between working and non-working files."""
import zlib
import struct
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

# Compare QuerySchemaNames (working in investigate2.py) with BuildingMeshes (still empty)
for fname in ["carcara_QuerySchemaNames_r03.ghuser", "carcara_BuildingMeshes_r03.ghuser"]:
    raw = open(LEGACY_DIR / fname, 'rb').read()
    archive = partial_inflate(raw)
    name = fname.split('_')[1]

    print(f"\n{'='*60}")
    print(f"{name}: archive={len(archive)} bytes")

    # Find Object chunk
    obj_pos = archive.find(b'\x06Object')
    print(f"  \\x06Object at offset {obj_pos}")

    if obj_pos == -1:
        print("  No Object chunk found!")
        continue

    # Look at the context around Object
    print(f"  Bytes before Object: {archive[obj_pos-5:obj_pos].hex()}")
    print(f"  Bytes after Object name: {archive[obj_pos+7:obj_pos+7+20].hex()}")

    # In the working QuerySchemaNames:
    # investigate2.py found inner UO at offset 630 in the 9758-byte archive
    # The '\x06Object' was at offset 611 according to investigation output
    # 630 - 611 = 19 bytes between Object and the start of the inner deflate stream

    # Let's try to inflate from various offsets after Object
    print(f"  Trying inflate from offsets {obj_pos} to {obj_pos+50}:")
    for off in range(obj_pos, min(obj_pos + 60, len(archive))):
        cand = partial_inflate(archive[off:off+300])
        if len(cand) > 200:
            print(f"    offset={off}: inflated={len(cand)} starts={cand[:30]}")
            if b'UserObject' in cand[:30]:
                full = partial_inflate(archive[off:])
                print(f"    INNER UO at offset {off}: {len(full)} bytes")
                break
