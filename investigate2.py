"""Deep investigation of nested ghuser structure."""
import zlib
import re
import base64
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
archive = partial_inflate(raw)
print(f"Outer archive ({len(archive)} bytes) starts with: {archive[:30]}")

# Find Object chunk (not UserObject)
# Use \x06Object to find standalone - \x06 is the 7-bit encoded length=6
obj_idx = archive.find(b'\x06Object')
print(f"\n'Object' chunk at offset {obj_idx}")

# Inflate from there
inner = None
for off in range(obj_idx, min(obj_idx + 400, len(archive))):
    cand = partial_inflate(archive[off:off+200])
    if len(cand) > 50 and b'UserObject' in cand[:30]:
        inner = partial_inflate(archive[off:])
        print(f"Inner UserObject archive found at offset {off} ({len(inner)} bytes)")
        print(f"Inner starts with: {inner[:60]}")
        break

if not inner:
    print("No inner UserObject found")
    sys.exit(1)

# Now find ClusterDocument inside the inner archive
cd_idx = inner.find(b'ClusterDocument')
print(f"\nClusterDocument at offset {cd_idx} in inner archive")
print(f"Context: {inner[cd_idx-5:cd_idx+40]}")

# Inflate the ClusterDocument
doc = None
for off in range(cd_idx, min(cd_idx + 400, len(inner))):
    cand = partial_inflate(inner[off:off+200])
    if len(cand) > 100 and b'Document' in cand[:20]:
        doc = partial_inflate(inner[off:])
        print(f"ClusterDocument inflated at offset {off} ({len(doc)} bytes)")
        break

if not doc:
    print("ClusterDocument inflate failed")
    sys.exit(1)

print(f"Doc starts with: {doc[:60]}")

# Look for base64 runs in the doc
BASE64_RUN = re.compile(rb'[A-Za-z0-9+/=]{100,}')
print(f"\n=== Base64 runs in cluster document ===")
for i, m in enumerate(BASE64_RUN.finditer(doc)):
    run = m.group()
    print(f"\nRun {i+1}: offset={m.start()}, len={len(run)}")
    # Try trims 0..3
    best = None
    for trim in range(4):
        r = run[trim:]
        try:
            decoded = base64.b64decode(r + b'=' * (-len(r) % 4))
            printable_ratio = sum(32 <= b <= 126 for b in decoded) / max(len(decoded), 1)
            if best is None or printable_ratio > best[0]:
                best = (printable_ratio, trim, decoded)
        except Exception:
            pass
    if best:
        ratio, trim, decoded = best
        print(f"  Best trim={trim}, printable={ratio:.2f}, len={len(decoded)}")
        print(f"  First 100 chars: {decoded[:100]}")
        if ratio > 0.9:
            print("  -> Looks like valid source!")

# Also check for printable strings in doc
print()
print("=== Printable strings in cluster doc (first 500 bytes) ===")
PRINTABLE = re.compile(rb'[\x20-\x7e]{4,}')
for m in PRINTABLE.finditer(doc[:500]):
    print(f"  {m.start()}: {repr(m.group().decode())}")
