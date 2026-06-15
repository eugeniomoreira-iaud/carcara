"""CRC_CurveDisplay: SDK-mode Grasshopper component for custom curve preview.

Reproduces the C# GH_ScriptInstance behaviour (BeforeRunScript, RunScript,
DrawViewportWires, ClippingBox) in Rhino 8 Python 3 SDK mode.
SDK mode is triggered by Rhino detecting a class that subclasses
Grasshopper.Kernel.GH_ScriptInstance — no extra flag needed in the archive.
"""
import sys
import os

# Make the crc_modules package importable from a Grasshopper Python 3 component.
# GHPython runs this code from an in-memory string, so __file__ is undefined.
# The installer copies the whole deployable folder to:
#   %APPDATA%\Grasshopper\UserObjects\carcara\   (Windows)
# with the package at .../carcara/crc_modules. Put the PARENT (.../carcara) on
# sys.path so `import crc_modules` resolves.
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

import Rhino.Geometry as rg
import Grasshopper.Kernel as ghk
import System.Drawing

from crc_modules.geometry.dash import parse_dash_pattern
from crc_modules.rhino.curve_display import apply_dash_pattern


class CurveDisplay(ghk.GH_ScriptInstance):
    """SDK-mode GH_ScriptInstance: custom viewport curve display with dash support."""

    def __init__(self):
        self._curves = []
        self._colors = []
        self._widths = []
        self._clip = rg.BoundingBox.Empty

    def BeforeRunScript(self):
        self._clip = rg.BoundingBox.Empty
        self._curves = []
        self._colors = []
        self._widths = []

    def RunScript(self, Curve, Width, Colour, Dash):
        if Curve is None:
            return
        if Width <= 0:
            return

        dash_str = str(Dash) if Dash is not None else ""
        pattern = parse_dash_pattern(dash_str)
        segments = apply_dash_pattern(Curve, pattern)

        self._clip = rg.BoundingBox.Union(self._clip, Curve.GetBoundingBox(False))
        for seg in segments:
            self._curves.append(seg)
            self._colors.append(Colour)
            self._widths.append(Width)

    @property
    def ClippingBox(self):
        return self._clip

    def DrawViewportWires(self, args):
        for i in range(len(self._curves)):
            args.Display.DrawCurve(self._curves[i], self._colors[i], self._widths[i])
