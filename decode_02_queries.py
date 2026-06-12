"""Decode all 02.Queries .ghuser files, extract embedded source + interface."""

import base64
import re
import sys
import zlib
from pathlib import Path

GHUSER_DIR = Path("carcara-old/carcara")
OUTPUT_DIR = Path("carcara-old/ghuser-metadata/scripts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMPONENTS_02_QUERIES = [
    "QuerySchemaNames",
    "QueryTableNames",
    "QueryColumnNames",
    "QueryValues",
    "GeometryEntities",
    "GeometriesWithSpatialFilter",
    "ValuesWithSpatialFilter",
    "CreateTable",
    "CreateShapefile",
]


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


def get_string_item_offset(archive, key):
    """Find the offset of a top-level string key (e.g., 'Name')."""
    m = re.search(re.escape(key.encode()), archive)
    return m.start() if m else -1


def extract_metadata(archive):
    """Pull Name, NickName, Description, Category from inflated archive."""
    result = {}
    lines = [(m.start(), m.group().decode()) for m in re.finditer(rb'[\x20-\x7e]{4,}', archive)]

    for i, (_, s) in enumerate(lines):
        if s in ("Name", "NickName", "Description"):
            if i + 1 < len(lines):
                result[s] = lines[i + 1][1]
    # Category and SubCategory have long gaps before value, scan more ahead
    for i, (_, s) in enumerate(lines):
        if s == "Category":
            for j in range(i+1, min(i+500, len(lines))):
                g = lines[j][0] - lines[i][0]
                val = lines[j][1]
                if 2 < g < 60 and (val.startswith('car') or '.' in val):
                    result[s] = val
                    break
            continue
        elif s == "SubCategory":
            for j in range(i+1, min(i+500, len(lines))):
                g = lines[j][0] - lines[i][0]
                val = lines[j][1]
                if 2 < g < 60 and '.' in val:
                    result[s] = val
                    break
            continue
    return result


def extract_scripts(archive, label="archive"):
    """Find and base64-decode embedded script source."""
    scripts = []
    for run in re.findall(rb'[A-Za-z0-9+/=]{100,}', archive):
        try:
            src = base64.b64decode(run + b'=' * (-len(run) % 4))
        except Exception:
            continue
        if src[:1] in (b'"', b'#', b'i', b'u'):
            text = src.decode('utf-8', errors='replace')
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            scripts.append(text)
    return scripts


def find_cluster_docs(archive):
    """Find all nested ClusterDocument deflate streams."""
    results = []
    for m in re.finditer(b'ClusterDocument', archive):
        start = m.start()
        for off in range(start, min(start + 400, len(archive))):
            cand = partial_inflate(archive[off:off + 200])
            if len(cand) > 100 and b'Document' in cand[:20]:
                inner = partial_inflate(archive[off:])
                results.append(inner)
                break
    return results


def extract_params_from_docs(docs):
    """Extract CustomName/CustomNickName pairs from cluster docs (input/output hooks)."""
    params = []
    seen_names = set()

    for doc in docs:
        lines = [(m.start(), m.group().decode()) for m in re.finditer(rb'[\x20-\x7e]{4,}', doc)]
        for i, (_, s) in enumerate(lines):
            if s == "CustomName":
                # Value should follow within a few bytes (length-prefixed string)
                for j in range(i+1, min(i+30, len(lines))):
                    gap = lines[j][0] - lines[i][0]
                    val = lines[j][1]
                    if 2 < gap < 50 and not '.' in val:
                        if val not in seen_names and len(val) >= 2:
                            params.append(f"In : {val}")
                            seen_names.add(val)
                        break
            elif s == "CustomNickName":
                for j in range(i+1, min(i+30, len(lines))):
                    gap = lines[j][0] - lines[i][0]
                    val = lines[j][1]
                    if 2 < gap < 50 and not '.' in val:
                        # try to match with a preceding CustomName
                        param = f"In : "  # default, will fix below
                        for k in range(j-1, max(i-30, 0), -1):
                            if lines[k][1] == "CustomName":
                                for l in range(k+1, min(k+30, len(lines))):
                                    g2 = lines[l][0] - lines[k][0]
                                    if 2 < g2 < 50 and not '.' in lines[l][1]:
                                        param = f"In : {lines[l][1]}"
                                        break
                                break
                        # check if this name was already added as In or Out
                        combined = f"{param} / {val}"
                        if combined not in seen_names:
                            params.append(combined)
                            seen_names.add(combined)
                        break

    # De-duplicate while preserving order, fix In/Out pattern later by searching GUID/Name pairs
    return params


def extract_internal_components(doc):
    """Extract native component types from a cluster doc (GUID + Name sequences)."""
    comps = []
    seen_guids = set()
    lines = [(m.start(), m.group().decode()) for m in re.finditer(rb'[\x20-\x7e]{4,}', doc)]

    for i, (_, s) in enumerate(lines):
        if s == "GUID":
            # next GUID value
            if i + 1 < len(lines):
                guid = lines[i+1][1]
                if guid not in seen_guids:
                    seen_guids.add(guid)
                    # look for Name key before/after GUID
                    comp_name = None
                    for k in range(max(i-5, 0), min(i+30, len(lines))):
                        if lines[k][1] == "Name":
                            for l in range(k+1, min(k+20, len(lines))):
                                g = lines[l][0] - lines[k][0]
                                val = lines[l][1]
                                if 2 < g < 50 and '.' not in val:
                                    comp_name = val
                                    break
                            break
                    if comp_name:
                        comps.append(comp_name)
    return comps


def decode_ghuser(path):
    raw = open(path, "rb").read()
    archive = partial_inflate(raw)
    meta = extract_metadata(archive)
    scripts_outer = extract_scripts(archive)

    # Check for embedded script component (has ScriptComponentVersion marker)
    has_script_component = bool(re.search(b'ScriptComponentVersion', archive)) or \
                           bool(re.search(b'ScriptParamAccess', archive))

    if not has_script_component:
        # These are clusters — try to extract the interface
        cluster_docs = find_cluster_docs(archive)
        hooks = []
        all_internals = []
        for cd in cluster_docs:
            subscripts = extract_scripts(cd)
            hooks.extend(subscripts[:1])  # at most 1 script per doc
            internals = extract_internal_components(cd)
            all_internals.extend(internals)

        return meta, scripts_outer + hooks, has_script_component, archive, all_internals
    else:
        return meta, scripts_outer, True, archive, []


def main():
    for comp_name in COMPONENTS_02_QUERIES:
        pattern = GHUSER_DIR / f"carcara_{comp_name}_*.ghuser"
        files = list(pattern.parent.glob(pattern.name))
        if not files:
            print(f"[SKIP] No .ghuser found for {comp_name}")
            continue

        path = files[0]
        meta, scripts, is_script, archive, internals = decode_ghuser(path)

        nick = meta.get("NickName", comp_name)
        desc = meta.get("Description", "No description")
        category = meta.get("Category", "")
        subcategory = meta.get("SubCategory", "")
        comp_label = f"{comp_name} ({nick})"
        has_python = is_script or bool(scripts)

        output_path = OUTPUT_DIR / f"CRC_{comp_name}.py"
        lines = []
        lines.append(f"# === {comp_label} ===")
        lines.append(f"# Description: {desc}")
        lines.append(f"# Source: {path.name}")
        lines.append(f"# Type: {'ScriptComponent' if is_script else 'Cluster (native architecture)'}")
        if category:
            lines.append(f"# Category: {category}")
        if subcategory:
            lines.append(f"# SubCategory: {subcategory}")
        lines.append("")

        # Check for interface info from hooks
        if not has_python and internals:
            lines.append("# Native architecture cluster — no embedded Python.")
            lines.append("# Internal components used (native GH/RC):")
            for comp in internals[:3]:
                lines.append(f"#   - {comp}")
            # Try to find CustomName list more carefully
            all_custom_names = set()
            for cd in find_cluster_docs(archive)[:2]:  # top 2 docs
                for m in re.finditer(rb'CustomName', cd):
                    base = m.start()
                    for j in range(base+10, min(base+300, len(cd))):
                        chunk = cd[j:j+40]
                        if all(32 <= b < 127 for b in chunk[:min(15,len(chunk))]):
                            try:
                                val = chunk[:min(15,len(chunk))].decode('ascii', errors='replace')
                                if len(val) >= 2 and not '.' in val and not any(kw in val for kw in ['Custom','GUID','Name']):
                                    all_custom_names.add(val.strip().strip('"'))
                            except:
                                pass

            if all_custom_names:
                lines.append("# Parameters (inferred from cluster hooks):")
                for i, name in enumerate(sorted(all_custom_names), 1):
                    is_in = any(kw in name.lower() for kw in ['schema', 'table', 'column', 'x_col', 'cx', 'cy', 'conn'])
                    prefix = "In:  " if is_in else "Out: "
                    lines.append(f"#   {i} {prefix}{name}")

        if scripts:
            lines.append("# Embedded script source:")
            for idx, script in enumerate(scripts):
                if len(scripts) > 1:
                    lines.append(f"\n# --- Script #{idx + 1} ---")
                lines.append(script)
                lines.append("")
        else:
            lines.append("# NOTE: This component is a native cluster (no Python source).")
            lines.append("# Its behavior was defined by wiring of Rhino/GH native components.")

        output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

        if has_python:
            print(f"[OK] {comp_label}: script component -> saved Python source to {output_path.name}")
        else:
            print(f"[SKIP] {comp_label}: native cluster (no embedded Python)")


if __name__ == "__main__":
    main()
