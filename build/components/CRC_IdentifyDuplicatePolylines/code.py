"""CRC_IdentifyDuplicatePolylines: Detect duplicate polylines by normalised geometric signature."""
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

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.wkt import wkt_to_shapely
from crc_modules.geometry.duplicates import identify_duplicates

duplicateIndices = DataTree[object]()
report = "Provide a list of polyline curves to polylines."

try:
    if not polylines:
        report = "ERROR: No polylines provided."
    else:
        # Convert Rhino geometry → coordinate rings (list of (x, y) tuples)
        rings = []
        invalid_count = 0
        for poly in polylines:
            if poly is None:
                rings.append(None)
                invalid_count += 1
                continue
            wkt_str = rh_geometry_to_wkt(poly)
            if wkt_str is None:
                rings.append(None)
                invalid_count += 1
                continue
            try:
                shp_geom = wkt_to_shapely(wkt_str)
                if shp_geom.geom_type == "Polygon":
                    coords = list(shp_geom.exterior.coords)
                elif shp_geom.geom_type == "LineString":
                    coords = [(c[0], c[1]) for c in shp_geom.coords]
                else:
                    coords = None
                rings.append([(c[0], c[1]) for c in coords] if coords else None)
            except Exception:
                rings.append(None)
                invalid_count += 1

        # Compute duplicate groups with default tolerance
        DEFAULT_TOLERANCE = 1e-6
        groups = identify_duplicates(rings, tolerance=DEFAULT_TOLERANCE)

        # Build DataTree output — one branch per duplicate group
        duplicateIndices = DataTree[object]()
        total_duplicates = 0
        for branch_idx, dup_list in enumerate(groups):
            path = GH_Path(branch_idx)
            duplicateIndices.EnsurePath(path)
            for dup_idx in dup_list:
                duplicateIndices.Add(dup_idx, path)
                total_duplicates += 1

        valid_count = sum(1 for r in rings if r is not None)
        unique_count = valid_count - total_duplicates
        report = (
            "OK — {unique} unique, {dups} duplicate(s) in {groups} group(s)"
            " from {total} total.".format(
                unique=unique_count,
                dups=total_duplicates,
                groups=len(groups),
                total=len(polylines),
            )
        )
        if invalid_count:
            report += " ({} could not be processed.)".format(invalid_count)

except Exception as e:
    report = "ERROR: {}".format(e)
