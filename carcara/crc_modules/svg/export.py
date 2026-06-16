"""
crc_modules/svg/export.py
SVG element generators — pure Python, no Rhino imports.

Each function accepts pre-transformed SVG coordinates (Y already flipped)
and returns an SVG markup string snippet (element only, not a full document).

Style kwargs accepted by all shape functions:
  stroke        : str   — CSS color string, default "none"
  stroke_width  : float — default 0
  fill          : str   — CSS color string, default "none"
  fill_opacity  : float — 0.0–1.0, default 1.0
  stroke_opacity: float — 0.0–1.0, default 1.0

Additional for polyline/polygon:
  dash          : str   — SVG stroke-dasharray value, e.g. "5,5"

Additional for nurbs (path):
  (same as polyline, no dash in base signature — pass via **style)

Additional for text:
  font_family     : str   — default "Arial"
  font_size       : float — default 12
  text_anchor     : str   — "start" | "middle" | "end", default "start"
  dominant_baseline: str  — "auto" | "hanging" | "middle" | "baseline", default "auto"
  rotation        : float — degrees, default 0
"""

from __future__ import annotations
import html


def _attr(name: str, value) -> str:
    """Return a single XML attribute string."""
    return ' {}="{}"'.format(name, value)


def _style_attrs(stroke="none", stroke_width=0, fill="none",
                 fill_opacity=1.0, stroke_opacity=1.0, **_ignored) -> str:
    """Build common SVG style attribute string."""
    parts = []
    parts.append(_attr("stroke", stroke))
    parts.append(_attr("stroke-width", stroke_width))
    parts.append(_attr("fill", fill))
    if fill_opacity is not None and float(fill_opacity) != 1.0:
        parts.append(_attr("fill-opacity", fill_opacity))
    if stroke_opacity is not None and float(stroke_opacity) != 1.0:
        parts.append(_attr("stroke-opacity", stroke_opacity))
    return "".join(parts)


def _points_str(points: list) -> str:
    """Convert list of (x, y) tuples to SVG points attribute string."""
    return " ".join("{},{}".format(round(x, 4), round(y, 4)) for x, y in points)


def polyline_to_svg(points: list, **style) -> str:
    """
    Convert a list of (x, y) coordinate tuples to an SVG <polyline> or
    <polygon> element string.

    Points are expected to be already in SVG coordinate space (Y-down).
    Closed detection: if first point == last point the list is treated as
    closed and a <polygon> is emitted (first == last duplicate dropped).

    Args:
        points: list of (x, y) tuples in SVG coords
        **style: stroke, stroke_width, fill, fill_opacity, stroke_opacity, dash

    Returns:
        SVG element string.
    """
    if not points or len(points) < 2:
        return ""

    dash = style.pop("dash", "") or ""

    # Detect closed polyline
    is_closed = (
        len(points) >= 3
        and abs(points[0][0] - points[-1][0]) < 1e-9
        and abs(points[0][1] - points[-1][1]) < 1e-9
    )

    if is_closed:
        tag = "polygon"
        pts = points[:-1]  # drop duplicate closing vertex
    else:
        tag = "polyline"
        pts = points

    pts_str = _points_str(pts)
    attrs = _style_attrs(**style)
    if dash:
        attrs += _attr("stroke-dasharray", dash)

    return '<{tag}{attrs} points="{pts}"/>'.format(
        tag=tag, attrs=attrs, pts=pts_str
    )


def circle_to_svg(cx: float, cy: float, r: float, **style) -> str:
    """
    Convert circle parameters to an SVG <circle> element string.

    Args:
        cx: center X in SVG coords
        cy: center Y in SVG coords (Y-down, already flipped)
        r : radius
        **style: stroke, stroke_width, fill, fill_opacity, stroke_opacity, dash

    Returns:
        SVG element string.
    """
    dash = style.pop("dash", "") or ""
    attrs = _style_attrs(**style)
    if dash:
        attrs += _attr("stroke-dasharray", dash)
    return '<circle cx="{cx}" cy="{cy}" r="{r}"{attrs}/>'.format(
        cx=round(cx, 4), cy=round(cy, 4), r=round(r, 4), attrs=attrs
    )


def nurbs_to_svg(sampled_points: list, **style) -> str:
    """
    Convert a list of sampled (x, y) points to an SVG <path> element using
    M (moveto) + L (lineto) commands.

    Points are expected to already be in SVG coordinate space (Y-down).
    Uses the same sample list as the polyline variant; the caller is
    responsible for sampling the NURBS curve before calling this function.

    Args:
        sampled_points: list of (x, y) tuples in SVG coords
        **style: stroke, stroke_width, fill, fill_opacity, stroke_opacity, dash

    Returns:
        SVG element string.
    """
    if not sampled_points or len(sampled_points) < 2:
        return ""

    dash = style.pop("dash", "") or ""

    coords = ["M {},{} ".format(round(sampled_points[0][0], 4),
                                round(sampled_points[0][1], 4))]
    for x, y in sampled_points[1:]:
        coords.append("L {},{} ".format(round(x, 4), round(y, 4)))

    d = "".join(coords).strip()
    attrs = _style_attrs(**style)
    if dash:
        attrs += _attr("stroke-dasharray", dash)

    return '<path d="{d}"{attrs}/>'.format(d=d, attrs=attrs)


def text_to_svg(x: float, y: float, text: str, **style) -> str:
    """
    Convert a text string with position to an SVG <text> element.

    Supports optional rotation via a transform="rotate(deg, x, y)" attribute.

    Args:
        x: insertion X in SVG coords
        y: insertion Y in SVG coords (Y-down, already flipped)
        text: the text content (will be HTML-escaped)
        **style:
            fill           : CSS color, default "black"
            fill_opacity   : float, default 1.0
            font_family    : str, default "Arial"
            font_size      : float, default 12
            text_anchor    : "start" | "middle" | "end", default "start"
            dominant_baseline: "auto" | "hanging" | "middle" | "baseline", default "auto"
            rotation       : float degrees, default 0

    Returns:
        SVG element string.
    """
    fill = style.get("fill", "black") or "black"
    fill_opacity = style.get("fill_opacity", 1.0)
    font_family = style.get("font_family", "Arial") or "Arial"
    font_size = style.get("font_size", 12) or 12
    text_anchor = style.get("text_anchor", "start") or "start"
    dominant_baseline = style.get("dominant_baseline", "auto") or "auto"
    rotation = style.get("rotation", 0) or 0

    x_r = round(x, 4)
    y_r = round(y, 4)

    attrs = (
        ' x="{x}" y="{y}"'
        ' font-family="{ff}" font-size="{fs}"'
        ' fill="{fill}"'
        ' text-anchor="{anchor}"'
        ' dominant-baseline="{baseline}"'
    ).format(
        x=x_r, y=y_r,
        ff=font_family, fs=font_size,
        fill=fill,
        anchor=text_anchor,
        baseline=dominant_baseline,
    )

    if fill_opacity is not None and float(fill_opacity) != 1.0:
        attrs += ' fill-opacity="{}"'.format(fill_opacity)

    if rotation and float(rotation) != 0:
        attrs += ' transform="rotate({},{},{})"'.format(
            round(float(rotation), 4), x_r, y_r
        )

    escaped = html.escape(str(text))
    return '<text{attrs}>{text}</text>'.format(attrs=attrs, text=escaped)
