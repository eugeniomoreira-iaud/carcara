"""Custom viewport preview of curves — CPython SDK-mode (advanced) component.

Runs as a Rhino 8 Script component in SDK / advanced mode: a subclass of
``ghpythonlib.componentbase.executingcomponent`` that overrides
``DrawViewportWires`` / ``get_ClippingBox`` so the curves are drawn into Rhino's
viewport with a custom lineweight, color, and dash pattern. Display-only: the
component declares no outputs.

Accepts lists of Curve, Colour, Width, Dash — one entry per curve. If any list
is shorter than Curve, the last value is repeated for remaining curves.

NOTE: Unlike normal Carcara ``code.py`` files, an SDK preview component MUST
import Rhino — the preview overrides live in the component class and cannot be
isolated into ``crc_modules``. This is an accepted, documented exception (the
same one granted to the C# CurveDisplay). All pure dash math still lives in
``crc_modules`` (``geometry.dash`` + ``rhino.curve_display``).
"""
import sys
import os
import Grasshopper

# Dynamically route to the user objects folder via the Grasshopper API
_carcara_path = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder, "carcara")

if os.path.isdir(_carcara_path) and _carcara_path not in sys.path:
    sys.path.insert(0, _carcara_path)

try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
except Exception:
    pass

from ghpythonlib.componentbase import executingcomponent as component
import Rhino
import rhinoscriptsyntax as rs
import System
from System.Drawing import Color

from crc_modules.geometry.dash import parse_dash_pattern
from crc_modules.rhino.curve_display import apply_dash_pattern


def _get(seq, i, default):
    """Return seq[i] or last element if i >= len; handles .NET List[T] via len()."""
    if seq is None:
        return default
    if isinstance(seq, str):
        return seq
    try:
        n = len(seq)
    except TypeError:
        return seq  # scalar: Color, number, single geometry
    if n == 0:
        return default
    return seq[i] if i < n else seq[n - 1]


class CurveDisplay(component):

    def RunScript(self, curves, colours, widths, dashes):
        self.Message = "v{{component_version}}-{{date}}"
        self._entries = []   # list of (segments, color, width)
        self._bbox = Rhino.Geometry.BoundingBox.Empty
        self.Hidden = True

        if not curves:
            return

        # Iterate curve list; scalar input wrapped automatically by GHPython as list[1]
        try:
            n_curves = len(curves)
        except TypeError:
            # single item handed as non-list
            curves = [curves]
            n_curves = 1

        bbox = Rhino.Geometry.BoundingBox.Empty
        entries = []

        for i in range(n_curves):
            crv_raw = _get(curves, i, None)
            crv = rs.coercecurve(crv_raw) if crv_raw is not None else None
            if crv is None:
                continue

            color = _get(colours, i, Color.Black)
            if color is None:
                color = Color.Black

            width_raw = _get(widths, i, 1)
            try:
                width = int(float(width_raw)) if width_raw is not None else 1
            except (TypeError, ValueError):
                width = 1
            if width < 1:
                width = 1

            dash_raw = _get(dashes, i, None)

            try:
                pattern = parse_dash_pattern(dash_raw)
                segments = apply_dash_pattern(crv, pattern)
            except ValueError:
                segments = [crv]

            entries.append((segments, color, width))
            bbox = Rhino.Geometry.BoundingBox.Union(bbox, crv.GetBoundingBox(False))

        self._entries = entries
        self._bbox = bbox

    def DrawViewportWires(self, args):
        for segments, color, width in getattr(self, "_entries", []):
            for seg in segments:
                args.Display.DrawCurve(seg, color, width)

    def get_ClippingBox(self):
        return getattr(self, "_bbox", Rhino.Geometry.BoundingBox.Empty)
