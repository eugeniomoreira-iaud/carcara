"""Decode every legacy .ghuser in carcara-old/carcara/ into readable sources.

Read-only inspection tool for the rebuild (see specs/ghuser-decoding.md).
Outputs go to carcara-old/ghuser-metadata/scripts/:

  <Name>.py             embedded script source (script components)
  <Name>_cluster_N.py   embedded scripts found inside a ClusterDocument
  <Name>_interface.txt  cluster hook params + internal component names
                        (written for clusters, including script-free ones)

Stdlib only — no Rhino, no GH_IO.dll. Never writes into carcara-old/carcara/.

Usage (from repo root):
    python tools/decode_ghuser.py
"""

import base64
import re
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).parent
LEGACY_DIR = REPO_ROOT / "carcara-old" / "carcara"
OUT_DIR = REPO_ROOT / "carcara-old" / "ghuser-metadata" / "scripts"

PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")
BASE64_RUN = re.compile(rb"[A-Za-z0-9+/=]{100,}")

# Marker used to find the embedded component Object chunk.
# \x06 is the 7-bit length prefix for the 6-char string "Object".
# We search for this rather than plain b"Object" to avoid false-matching
# the longer string "UserObject" (which starts with a different length byte).
_OBJECT_CHUNK = b"\x06Object"

# Source code first-byte signatures that prove a base64 run decoded to script source.
# Covers: """ docstring, # comment, import keyword, using System (C#), \r\n blank line.
_SRC_FIRST_BYTES = (b'"', b"#", b"i", b"u", b"\r", b"\n")


def partial_inflate(buf: bytes, step: int = 64) -> bytes:
    """Raw-deflate inflate that tolerates running past the stream end.

    Feeds small chunks and keeps whatever decompressed before the error.
    """
    d = zlib.decompressobj(-15)
    out = bytearray()
    for i in range(0, len(buf), step):
        try:
            out += d.decompress(buf[i : i + step])
        except zlib.error:
            break
        if d.eof:
            break
    return bytes(out)


def _try_decode_run(run: bytes) -> str | None:
    """Try to base64-decode a run with trims 0..3 to correct length-prefix misalignment.

    The .NET string length-prefix byte often lands inside the base64 alphabet,
    so the raw regex match includes one extra leading character. Trying all four
    possible trim offsets and picking the result with the highest printable-ASCII
    ratio (>= 0.85) corrects the misalignment reliably.

    Returns the decoded UTF-8 string, or None if no trim produces valid source.
    """
    best_ratio = 0.0
    best_src: str | None = None
    for trim in range(4):
        r = run[trim:]
        if not r:
            continue
        try:
            decoded = base64.b64decode(r + b"=" * (-len(r) % 4))
        except Exception:
            continue
        if len(decoded) < 50:
            continue
        if decoded[:1] not in _SRC_FIRST_BYTES:
            continue
        ratio = sum(32 <= b <= 126 for b in decoded) / len(decoded)
        if ratio >= 0.85 and ratio > best_ratio:
            best_ratio = ratio
            best_src = decoded.decode("utf-8", errors="replace")
    return best_src


def extract_scripts(blob: bytes) -> list[str]:
    """Decode all long base64 runs that look like Python/C# source.

    Uses trim-0..3 alignment trials to handle the .NET length-prefix offset
    (see _try_decode_run).  Deduplicates identical decoded texts so the same
    script embedded at multiple nesting levels is not written twice.
    """
    seen: set[str] = set()
    scripts: list[str] = []
    for m in BASE64_RUN.finditer(blob):
        src = _try_decode_run(m.group())
        if src is not None and src not in seen:
            seen.add(src)
            scripts.append(src)
    return scripts


def _find_archive_at(buf: bytes, start: int, *, accept: bytes) -> bytes:
    """Scan forward from *start* looking for a deflate stream whose first
    ``accept``-length decompressed bytes contain the ``accept`` pattern.

    Returns the fully (partial) inflated stream, or b"" if not found.
    Limits the scan to 400 bytes past *start* to avoid runaway searches.

    Uses a 300-byte probe window instead of 200 — some embedded archives
    (e.g. large script components) have high compression ratios and require
    at least 250 compressed bytes before the output grows past 100 bytes.
    """
    for off in range(start, min(start + 400, len(buf))):
        cand = partial_inflate(buf[off : off + 300])
        if len(cand) > 100 and accept in cand[: len(accept) + 10]:
            return partial_inflate(buf[off:])
    return b""


def find_inner_userobject(archive: bytes) -> bytes:
    """Find and inflate the inner UserObject wrapped behind the Object chunk.

    Legacy .ghuser files that are "script component wrappers" embed the real
    component (a second UserObject) inside an Object chunk in the outer archive.
    The Object chunk is preceded by the byte \\x06 (7-bit encoded length = 6).

    Returns the inflated inner UserObject bytes, or b"" if not found.
    """
    idx = archive.find(_OBJECT_CHUNK)
    if idx == -1:
        return b""
    return _find_archive_at(archive, idx, accept=b"UserObject")


def find_cluster_document(archive: bytes) -> bytes:
    """Inflate the nested ClusterDocument stream, if present in *archive*.

    Searches for the literal b"ClusterDocument" and then scans forward for the
    deflate stream whose inflated content begins with b"Document" (the GH
    Document archive root chunk).

    Returns the inflated cluster document, or b"" if not found.
    """
    idx = archive.find(b"ClusterDocument")
    if idx == -1:
        return b""
    return _find_archive_at(archive, idx, accept=b"Document")


def cluster_interface(doc: bytes) -> str:
    """Recover hook params and internal component type names from a cluster doc."""
    lines = [(m.start(), m.group().decode()) for m in PRINTABLE.finditer(doc)]
    report = []

    report.append("== Hook params (CustomName / CustomNickName / CustomDescription) ==")
    for i, (_, s) in enumerate(lines):
        if s in ("CustomName", "CustomNickName", "CustomDescription"):
            value = lines[i + 1][1] if i + 1 < len(lines) else "?"
            report.append(f"{s}: {value}")

    report.append("")
    report.append("== Internal components (GUID -> Name) ==")
    for i, (_, s) in enumerate(lines):
        if s == "GUID" and i + 2 < len(lines) and lines[i + 1][1] == "Name":
            report.append(lines[i + 2][1])

    return "\n".join(report) + "\n"


def native_component_interface(blob: bytes) -> str:
    """Extract a human-readable summary from a native (non-script) GH component.

    Used for components like SRID which are native GH types (ValueList, etc.)
    with no embedded Python source.  Extracts description, type hint, and any
    list item expressions from the printable strings in the archive.
    """
    lines = [(m.start(), m.group().decode()) for m in PRINTABLE.finditer(blob)]
    report = ["== Native component (no embedded script) =="]

    # Description
    for i, (_, s) in enumerate(lines):
        if s == "Description" and i + 1 < len(lines):
            report.append(f"Description: {lines[i + 1][1]}")
            break

    # Name / NickName
    for i, (_, s) in enumerate(lines):
        if s in ("Name", "NickName") and i + 1 < len(lines):
            report.append(f"{s}: {lines[i + 1][1]}")

    # ListItem expressions (ValueList items)
    expressions = []
    for i, (_, s) in enumerate(lines):
        if s == "Expression" and i + 1 < len(lines):
            expressions.append(lines[i + 1][1])
    if expressions:
        report.append("")
        report.append("== ValueList items (Expression values) ==")
        for expr in expressions:
            report.append(expr)

    return "\n".join(report) + "\n"


def component_name(stem: str) -> str:
    """carcara_QueryValues_rev03 -> QueryValues."""
    m = re.match(r"carcara_(.+?)_(r|rev)\d+$", stem)
    return m.group(1) if m else stem


def decode_one(path: Path) -> tuple[list[str], str]:
    """Decode a single .ghuser.

    Returns ``(files_written, reason)`` where *reason* describes what was found
    (used in the printed status line).  *files_written* is a list of base-names
    of files written to OUT_DIR.
    """
    name = component_name(path.stem)

    # --- Level 1: inflate the outer UserObject archive ---
    outer = partial_inflate(path.read_bytes())
    if not outer.startswith(b"\nUserObject"):
        raise ValueError("outer inflate did not yield a UserObject archive")

    written: list[str] = []
    # Track distinct decoded script texts to avoid duplicates across levels.
    seen_scripts: set[str] = set()

    def _write_scripts(scripts: list[str], prefix: str) -> None:
        """Write a list of scripts, deduplicating against already-seen texts."""
        new = [s for s in scripts if s not in seen_scripts]
        for s in new:
            seen_scripts.add(s)
        if len(new) == 1:
            out = OUT_DIR / f"{prefix}.py"
            out.write_text(new[0], encoding="utf-8")
            written.append(out.name)
        else:
            for n, src in enumerate(new, 1):
                out = OUT_DIR / f"{prefix}_{n}.py"
                out.write_text(src, encoding="utf-8")
                written.append(out.name)

    def _process_archive(blob: bytes, label: str, depth: int = 0) -> None:
        """Recursively extract scripts and cluster documents from an archive blob.

        *label* is the name prefix to use for written files (e.g. "BuildingMeshes"
        or "BuildingMeshes_cluster").
        *depth* caps recursion to avoid pathological loops (max 5 levels).
        """
        if depth > 5:
            return

        # Extract scripts directly present in this blob.
        _write_scripts(extract_scripts(blob), label)

        # --- Inner UserObject (Object chunk wrapper) ---
        # Legacy .ghuser files that wrap a real component in an Object chunk embed
        # a second UserObject archive inside the outer one.  Inflate it and recurse
        # so scripts and clusters found at that level are extracted.
        inner = find_inner_userobject(blob)
        if inner:
            _process_archive(inner, label, depth + 1)

        # --- ClusterDocument ---
        doc = find_cluster_document(blob)
        if doc:
            cluster_label = f"{label}_cluster"
            _write_scripts(extract_scripts(doc), cluster_label)

            iface_path = OUT_DIR / f"{label}_interface.txt"
            if not iface_path.exists():  # don't clobber if already written at outer level
                iface_path.write_text(cluster_interface(doc), encoding="utf-8")
                written.append(iface_path.name)

            # Recurse into the cluster document — it may contain nested Object chunks too.
            inner_doc = find_inner_userobject(doc)
            if inner_doc:
                _process_archive(inner_doc, cluster_label, depth + 1)

    _process_archive(outer, name)

    # --- Native component fallback ---
    # If nothing was written yet, the component has no embedded script and no cluster.
    # It is a native GH component (e.g. ValueList). Extract whatever metadata is
    # readable and write an interface.txt so the file always produces at least one output.
    if not written:
        inner = find_inner_userobject(outer)
        target = inner if inner else outer
        iface_path = OUT_DIR / f"{name}_interface.txt"
        iface_path.write_text(native_component_interface(target), encoding="utf-8")
        written.append(iface_path.name)

    if any(f.endswith(".py") and "_cluster_" not in f for f in written):
        reason = "script component"
    elif any("_cluster_" in f for f in written):
        reason = "cluster"
    elif any(f.endswith("_interface.txt") for f in written):
        reason = "native component (no script) — interface written"
    else:
        reason = "no script/cluster found"
    return written, reason


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ghusers = sorted(LEGACY_DIR.glob("*.ghuser"))
    if not ghusers:
        raise SystemExit(f"no .ghuser files found in {LEGACY_DIR}")

    ok, empty, failed = 0, [], []
    for path in ghusers:
        try:
            written, reason = decode_one(path)
        except Exception as e:
            failed.append((path.name, str(e)))
            print(f"FAIL  {path.name}: {e}")
            continue
        ok += 1
        if written:
            print(f"OK    {path.name} -> {', '.join(written)}")
        else:
            empty.append((path.name, reason))
            print(f"EMPTY {path.name}: {reason}")

    print(f"\n{ok}/{len(ghusers)} decoded OK, {len(empty)} empty, {len(failed)} failed")
    if empty:
        print("Empty files:")
        for name, reason in empty:
            print(f"  {name}: {reason}")
    for name, err in failed:
        print(f"  FAIL {name}: {err}")


if __name__ == "__main__":
    main()
