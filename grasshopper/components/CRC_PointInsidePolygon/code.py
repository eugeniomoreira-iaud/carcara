"""CRC_PointInsidePolygon: Find a guaranteed-inside point for a polygon curve."""
import sys
import os

# Make crc_modules importable from Grasshopper UserObjects path.
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

try:
    ghenv.Component.Message = "v{{version}}"
except Exception:
    pass

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.polylabel import interior_point
from crc_modules.geometry.wkt import wkt_to_shapely

pt = None
report = "Provide a closed polygon curve to pol."

try:
    if pol is None:
        report = "No polygon provided."
    else:
        # Convert Rhino curve → WKT (via rhino module, no direct Rhino import here)
        wkt_str = rh_geometry_to_wkt(pol)
        if wkt_str is None:
            report = "ERROR: Could not convert input to WKT. Ensure pol is a closed planar curve."
        else:
            # Extract ring coordinates from WKT via shapely
            shp_geom = wkt_to_shapely(wkt_str)
            if shp_geom.geom_type == "Polygon":
                ring = list(shp_geom.exterior.coords)
            elif shp_geom.geom_type == "LineString":
                ring = list(shp_geom.coords)
            else:
                ring = None

            if ring is None or len(ring) < 3:
                report = "ERROR: Polygon ring could not be extracted from input curve."
            else:
                (ix, iy), dist = interior_point(ring, tolerance=0.01)

                # Build Rhino Point3d via RhinoCommon (imported inside rhino module scope,
                # but we need it here for the output — import is GH-side only)
                import Rhino.Geometry as rg
                pt = rg.Point3d(ix, iy, 0.0)
                report = "OK — interior point found at ({:.4f}, {:.4f}), dist to edge: {:.4f}".format(
                    ix, iy, dist
                )

except Exception as e:
    report = "ERROR: {}".format(e)
