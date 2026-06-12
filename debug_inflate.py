"""Debug why inflate gives different sizes - issue with step sizes or caching."""
import zlib
from pathlib import Path

def partial_inflate_orig(buf, step=64):
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
print(f"Raw file size: {len(raw)}")

for step in [32, 64, 128, 256, 512, 1024, 4096]:
    result = partial_inflate_orig(raw, step=step)
    print(f"  step={step}: inflated={len(result)} starts_with={result[:20]}")

# Now check what investigate3.py was seeing - it was re-importing from the investigate module
# but running under a different path.
# Wait - investigate3.py imports partial_inflate fresh - so why would it give different results?
# Let me re-check exactly what investigate3.py does...
# In investigate3.py, find_inner_userobject searches the archive for '\x06Object'
# and the OUTER archive is only 12921 bytes, not 37258
# So investigate3.py must have been using archive (partial inflate of raw), and then
# calling partial_inflate(archive[off:]) for the inner UO
# But the outer archive (12921) and the inner UO (37258) - both are partial inflates from
# DIFFERENT starting positions in raw

# Hypothesis: when calling partial_inflate(raw), we get the outer archive
# When we call partial_inflate(archive[off:]) where off is within the outer archive,
# we're trying to inflate a SLICE OF ALREADY-INFLATED DATA, not compressed data!
#
# In investigate3.py, the inner UO search was done on the outer archive bytes, not on raw.
# The outer archive bytes themselves contain another compressed stream at offset 630
# (as confirmed in investigation2.py).
# So the outer archive IS the inflated outer UserObject, and within it, the Object chunk
# at offset 611-630 contains ANOTHER deflate stream that inflates to the inner UserObject.
#
# The issue in debug_empty.py: the outer archive is only 12921 bytes for BuildingMeshes
# but investigate3.py reported 37258 bytes inner UO with inner_UO=True
#
# Wait - let me recheck investigate3.py: it calls partial_inflate(archive[off:])
# where archive is partial_inflate(raw). So the inner UO size is from inflating
# archive[off:] where archive = outer inflate...
# That means the outer archive for BuildingMeshes must be much larger.

# Let me check with different steps for the outer

print()
print("=== Checking outer inflate size for BuildingMeshes ===")
for step in [1, 8, 16, 32, 64, 128, 512]:
    d = zlib.decompressobj(-15)
    out = bytearray()
    error_at = None
    for i in range(0, len(raw), step):
        try:
            chunk = d.decompress(raw[i:i+step])
            out += chunk
        except zlib.error as e:
            error_at = (i, str(e))
            break
        if d.eof:
            break
    print(f"  step={step}: size={len(out)} eof={d.eof} error_at={error_at}")
