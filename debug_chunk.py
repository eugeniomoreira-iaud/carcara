"""Understand the GH_IO chunk structure after Object."""
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

fname = "carcara_BuildingMeshes_r03.ghuser"
raw = open(LEGACY_DIR / fname, 'rb').read()
archive = partial_inflate(raw)
print(f"Archive size: {len(archive)}")

# Object chunk is at 1142
obj_offset = 1142
print(f"\nBytes around Object chunk (offset {obj_offset}):")
print(f"  Raw hex: {archive[obj_offset:obj_offset+50].hex()}")

# After \x06Object: what follows?
# GH_IO chunk layout: [length-prefixed name][item_count int32][byte_count int32][data...]
# The name is already in 'Object' at offset obj_offset
# After the name: item_count (int32) then byte_count (int32)
# \xff\xff\xff\xff = -1 (dynamic/unknown item count)
# \x14\x00\x00\x00 = 20 (byte count? But that seems too small)

after_obj = obj_offset + 7  # skip \x06Object = 7 bytes
print(f"\nAfter 'Object' name (offset {after_obj}):")
print(f"  Hex: {archive[after_obj:after_obj+20].hex()}")
print(f"  item_count: {struct.unpack('<i', archive[after_obj:after_obj+4])[0]}")
print(f"  byte_count: {struct.unpack('<i', archive[after_obj+4:after_obj+8])[0]}")

# The byte_count tells us how many bytes the compressed stream occupies
byte_count_offset = after_obj + 4
byte_count = struct.unpack('<i', archive[byte_count_offset:byte_count_offset+4])[0]
data_start = after_obj + 8
print(f"\nData starts at offset {data_start}, byte_count = {byte_count}")
print(f"So data ends at offset {data_start + byte_count}")

# The data (archive[data_start:data_start+byte_count]) should be the compressed inner UO
data = archive[data_start:data_start + byte_count]
print(f"Data slice length: {len(data)}")
print(f"First 20 bytes of data: {data[:20].hex()}")

# This data is the inner compressed content - try to inflate it
inner = partial_inflate(data)
print(f"\nInflated inner: {len(inner)} bytes")
print(f"Starts with: {inner[:50]}")

# Try inflating different offsets within the data
print("\n=== Trying offsets within data slice ===")
for off in range(0, min(50, len(data))):
    cand = partial_inflate(data[off:off+200])
    if len(cand) > 100 and b'UserObject' in cand[:30]:
        full = partial_inflate(data[off:])
        print(f"  offset={off}: inner UO {len(full)} bytes: {full[:40]}")
        break
