"""Check why find_inner_userobject fails for BuildingMeshes."""
import zlib
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
print(f"Archive: {len(archive)} bytes")

# Object at offset 1142, inner UO at offset 1161
# The find_inner_userobject scans from obj_idx to obj_idx+400
# obj_idx = 1142, so it scans offsets 1142..1542
# At each offset it tries: partial_inflate(archive[off:off+200])
# and checks len(cand) > 100 and b"UserObject" in cand[:30]

print("\nScanning from 1142 to 1250 (first 30 that matter):")
for off in range(1142, 1200):
    cand = partial_inflate(archive[off:off+200])
    marker = "< FOUND" if len(cand) > 100 and b"UserObject" in cand[:30] else ""
    if len(cand) > 0 or marker:
        print(f"  off={off}: inflated={len(cand)} b'UserObject' in cand[:30]={b'UserObject' in cand[:30]} {marker}")

# Let's check what partial_inflate produces at offset 1161 with window 200
cand = partial_inflate(archive[1161:1161+200])
print(f"\nAt offset 1161 with window 200: inflated={len(cand)}")
print(f"  starts with: {cand[:40]}")
print(f"  b'UserObject' in cand[:30]: {b'UserObject' in cand[:30]}")

# Why is it failing? Let me check individual deflate offsets
# The current code requires len(cand) > 100 - maybe the window is too small
# to get 100 bytes of output?
for window in [100, 150, 200, 300, 500]:
    cand = partial_inflate(archive[1161:1161+window])
    print(f"  window={window}: inflated={len(cand)}")
