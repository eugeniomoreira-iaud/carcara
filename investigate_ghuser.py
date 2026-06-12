"""Investigation script for ghuser binary structure."""
import zlib
import re
import sys

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

filename = sys.argv[1] if len(sys.argv) > 1 else 'carcara-old/carcara/carcara_QuerySchemaNames_r03.ghuser'
raw = open(filename, 'rb').read()
print(f'File size: {len(raw)}')
archive = partial_inflate(raw)
print(f'Outer inflate size: {len(archive)}')
print(f'Starts with: {archive[:30]}')
print()

PRINTABLE = re.compile(rb'[\x20-\x7e]{4,}')

# Look for various markers
print("=== Key markers in outer archive ===")
for marker in [b'Object', b'UserObject', b'ClusterDocument', b'ScriptComponent']:
    for m in re.finditer(re.escape(marker), archive):
        print(f"  '{marker.decode()}' at offset {m.start()}")

# Extract printable strings from first 1000 bytes
print()
print("=== Printable strings (first 1500 bytes) ===")
for m in PRINTABLE.finditer(archive[:1500]):
    print(f"  {m.start()}: {repr(m.group().decode())}")

# Base64 runs in outer archive
BASE64_RUN = re.compile(rb'[A-Za-z0-9+/=]{100,}')
print()
print("=== Long base64 runs in outer archive (first 5) ===")
for i, run in enumerate(BASE64_RUN.finditer(archive)):
    if i >= 5:
        break
    print(f"  offset={run.start()} len={len(run.group())} first20={run.group()[:20]}")
    # Try with trims 0..3
    for trim in range(4):
        r = run.group()[trim:]
        try:
            decoded = __import__('base64').b64decode(r + b'=' * (-len(r) % 4))
            printable_ratio = sum(32 <= b <= 126 for b in decoded) / max(len(decoded), 1)
            print(f"    trim={trim} decoded_len={len(decoded)} printable={printable_ratio:.2f} first50={decoded[:50]}")
        except Exception as e:
            print(f"    trim={trim} error: {e}")

# Try to find nested deflate stream after Object chunk
print()
print("=== Searching for nested deflate after first Object occurrence ===")
obj_matches = list(re.finditer(rb'\x06Object(?!\x04User)', archive))
print(f"  Found {len(obj_matches)} standalone 'Object' occurrences")
for match in obj_matches[:3]:
    print(f"  At offset {match.start()}, trying inflate candidates...")
    for off in range(match.start(), min(match.start() + 400, len(archive))):
        cand = partial_inflate(archive[off:off+200])
        if len(cand) > 100 and archive[off:off+2] not in (b'', b'\x00\x00'):
            # Check if it looks like a UserObject archive
            if b'UserObject' in cand[:50]:
                print(f"    Found inner UserObject at offset {off}: {cand[:50]}")
                break
            elif b'Document' in cand[:30]:
                print(f"    Found Document at offset {off}: {cand[:50]}")
                break
