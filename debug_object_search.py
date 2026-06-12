"""Search for Object chunk and inner deflate stream in BuildingMeshes."""
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
PRINTABLE = re.compile(rb'[\x20-\x7e]{4,}')

fname = "carcara_BuildingMeshes_r03.ghuser"
raw = open(LEGACY_DIR / fname, 'rb').read()
archive = partial_inflate(raw)
print(f"Archive size: {len(archive)}")

print("\n=== Printable strings in archive ===")
for m in PRINTABLE.finditer(archive):
    s = m.group().decode()
    if len(s) > 8:
        print(f"  {m.start()}: {s!r}")

print("\n=== Looking for Object chunk (\\x06Object) ===")
_OBJECT_CHUNK = b"\x06Object"
idx = 0
while True:
    pos = archive.find(_OBJECT_CHUNK, idx)
    if pos == -1:
        break
    print(f"  Found at offset {pos}: {archive[pos:pos+30]}")
    idx = pos + 1

print("\n=== All 'Object' occurrences ===")
for m in re.finditer(rb'Object', archive):
    print(f"  offset={m.start()}: context={archive[m.start()-3:m.start()+12]}")

# Check a wider range for the inner compressed stream
print("\n=== Trying to inflate each window of the archive ===")
for test_off in range(600, 700, 5):
    if test_off >= len(archive):
        break
    cand = partial_inflate(archive[test_off:test_off+300])
    if len(cand) > 200:
        print(f"  offset={test_off}: inflated {len(cand)} bytes: {cand[:30]}")
