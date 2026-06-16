"""Custom viewport preview of curves — CPython SDK-mode (advanced) component.

Runs as a Rhino 8 Script component in SDK / advanced mode: a subclass of
``ghpythonlib.componentbase.executingcomponent`` that overrides
``DrawViewportWires`` / ``get_ClippingBox`` so the curves are drawn into Rhino's
viewport with a custom lineweight, color, and dash pattern. Display-only: the
component declares no outputs.

NOTE: Unlike normal Carcara ``code.py`` files, an SDK preview component MUST
import Rhino — the preview overrides live in the component class and cannot be
isolated into ``crc_modules``. This is an accepted, documented exception (the
same one granted to the C# CurveDisplay). All pure dash math still lives in
``crc_modules`` (``geometry.dash`` + ``rhino.curve_display``).
"""
import sys
import os

# Make the crc_modules package importable from a Grasshopper Script component.
# The installer copies the deployable folder to .../UserObjects/carcara/ with the
# package at .../carcara/crc_modules. Put the PARENT (.../carcara) on sys.path.
_bases = []
_appdata = os.environ.get("APPDATA")
if _appdata:
    _bases.append(os.path.join(_appdata, "Grasshopper", "UserObjects", "carcara"))
_bases.append(os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "McNeel",
    "Rhinoceros", "8.0", "Plug-ins", "Grasshopper", "UserObjects", "carcara"))
for _b in _bases:
    if os.path.isdir(_b) and _b not in sys.path:
        sys.path.insert(0, _b)

from ghpythonlib.componentbase import executingcomponent as component
import Rhino
import rhinoscriptsyntax as rs
import System
from System.Drawing import Color

from crc_modules.geometry.dash import parse_dash_pattern
from crc_modules.rhino.curve_display import apply_dash_pattern


class CurveDisplay(component):

    def RunScript(self, Curve, Width, Colour, Dash):
        # rs.coercecurve safely converts a Guid/GH wrapper into a Rhino curve.
        crv = rs.coercecurve(Curve) if Curve else None

        self._color = Colour if Colour else Color.Black
        self._width = int(Width) if Width else 1
        self._segments = []
        self._bbox = Rhino.Geometry.BoundingBox.Empty

        if crv:
            try:
                pattern = parse_dash_pattern(Dash)
                self._segments = apply_dash_pattern(crv, pattern)
                self.Message = None
            except ValueError as e:
                # Bad dash pattern → fall back to a solid line and surface why.
                self._segments = [crv]
                self.Message = str(e)
            self._bbox = crv.GetBoundingBox(False)

        # Suppress the default param preview; we draw our own wires.
        self.Hidden = True

    def DrawViewportWires(self, args):
        if not getattr(self, "_segments", None):
            return
        for segment in self._segments:
            args.Display.DrawCurve(segment, self._color, self._width)

    def get_ClippingBox(self):
        return getattr(self, "_bbox", Rhino.Geometry.BoundingBox.Empty)
