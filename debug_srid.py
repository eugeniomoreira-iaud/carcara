"""Debug SRID - inner UO found but no scripts."""
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
PRINTABLE = re.compile(rb'[\x20-\x7e]{4,}')
BASE64_RUN = re.compile(rb'[A-Za-z0-9+/=]{100,}')
_OBJECT_CHUNK = b"\x06Object"

fname = "carcara_SRID_r00.ghuser"
raw = open(LEGACY_DIR / fname, 'rb').read()
archive = partial_inflate(raw)
print(f"Outer archive: {len(archive)} bytes")
print(f"Starts with: {archive[:30]}")

# Find Object
obj_idx = archive.find(_OBJECT_CHUNK)
print(f"Object at: {obj_idx}")

# Find inner UO
inner = None
for off in range(obj_idx, min(obj_idx + 400, len(archive))):
    cand = partial_inflate(archive[off:off+200])
    if len(cand) > 100 and b'UserObject' in cand[:30]:
        inner = partial_inflate(archive[off:])
        print(f"Inner UO at offset {off}: {len(inner)} bytes")
        break

if inner:
    print(f"Inner UO starts: {inner[:50]}")
    print()
    print("Printable strings in inner UO:")
    for m in PRINTABLE.finditer(inner):
        if len(m.group()) > 6:
            print(f"  {m.start()}: {m.group().decode()!r}")

    print()
    print(f"BASE64 runs in inner UO: {len(list(BASE64_RUN.finditer(inner)))}")
    for m in BASE64_RUN.finditer(inner):
        run = m.group()
        print(f"  len={len(run)} first20={run[:20]}")
        for trim in range(4):
            r = run[trim:]
            try:
                decoded = base64.b64decode(r + b'=' * (-len(r) % 4))
                ratio = sum(32 <= b <= 126 for b in decoded) / max(len(decoded), 1)
                print(f"    trim={trim} decoded_len={len(decoded)} ratio={ratio:.2f} first50={decoded[:50]}")
            except Exception as e:
                print(f"    trim={trim} error: {e}")
else:
    print("Inner UO not found with window=200")
    # Try window 100
    for off in range(obj_idx, min(obj_idx + 400, len(archive))):
        cand = partial_inflate(archive[off:off+100])
        if len(cand) > 50 and b'UserObject' in cand[:30]:
            inner = partial_inflate(archive[off:])
            print(f"Inner UO at offset {off} (window=100): {len(inner)} bytes")
            print(f"  starts: {inner[:40]}")
            break
