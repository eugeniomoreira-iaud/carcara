"""CRC_PointInsidePolygon: Find a guaranteed-inside point for a polygon curve."""
# r: shapely
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

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.polylabel import interior_point
from crc_modules.geometry.wkt import wkt_to_shapely

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
from Grasshopper import DataTree

def _unwrap(g):
    return g.Value if hasattr(g, "Value") else g

def _in_item(i):
    for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True):
        return _unwrap(g)
    return None

def _in_list(i):
    return [_unwrap(g) for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True)]

def _in_tree(i):
    src = ghenv.Component.Params.Input[i].VolatileData
    t = DataTree[object]()
    for p in src.Paths:
        for g in src[p]:
            t.Add(_unwrap(g), p)
    return t
# ========================================================================================

# INPUT MAPPING  0:pol:item
pol_int = _in_item(0)

interiorPoint = None
report = "Provide a closed polygon curve to polygon to compute its pole of inaccessibility (polylabel)."

try:
    if pol_int is None:
        report = "No polygon provided."
    else:
        # Convert Rhino curve → WKT (via rhino module, no direct Rhino import here)
        wkt_str = rh_geometry_to_wkt(pol_int)
        if wkt_str is None:
            report = "ERROR: Could not convert input to WKT. Ensure polygon is a closed planar curve."
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
                interiorPoint = rg.Point3d(ix, iy, 0.0)
                report = "OK — pole of inaccessibility (polylabel) at ({:.4f}, {:.4f}), dist to nearest edge: {:.4f}".format(
                    ix, iy, dist
                )

except Exception as e:
    report = "ERROR: {}".format(e)
