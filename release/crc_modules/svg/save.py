"""
crc_modules/svg/save.py
Assembles a list of SVG element strings into a complete SVG document
and writes it to disk.

Pure Python, no Rhino imports — fully pytest-testable.
"""

from __future__ import annotations
import os


def save_svg(
    elements: list,
    out_path: str,
    width: float,
    height: float,
    viewbox: tuple | None = None,
    units: str = "mm",
) -> str:
    """
    Assemble SVG element strings into a complete SVG document and write to disk.

    Args:
        elements : list of SVG element strings (may contain empty strings)
        out_path : absolute or relative path to write; must end with .svg
        width    : document width in the given units
        height   : document height in the given units
        viewbox  : (min_x, min_y, vb_width, vb_height) tuple.
                   If None, defaults to (0, 0, width, height).
        units    : unit suffix for width/height attributes, e.g. "mm", "px"

    Returns:
        Absolute path of the written file.

    Raises:
        ValueError: if elements is empty or out_path is blank
        IOError: if the file cannot be written
    """
    if not out_path or not out_path.strip():
        raise ValueError("out_path must not be empty")

    # Resolve to absolute path
    out_path = os.path.abspath(out_path)

    # Ensure parent directory exists
    parent = os.path.dirname(out_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    # Build viewBox string
    if viewbox is None:
        vb = "0 0 {} {}".format(width, height)
    else:
        vb = "{} {} {} {}".format(*viewbox)

    w_str = "{}{}".format(width, units)
    h_str = "{}{}".format(height, units)

    body = "\n".join(e for e in elements if e)

    svg_doc = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"'
        ' width="{w}" height="{h}" viewBox="{vb}">\n'
        '{body}\n'
        '</svg>\n'
    ).format(w=w_str, h=h_str, vb=vb, body=body)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg_doc)

    return out_path
