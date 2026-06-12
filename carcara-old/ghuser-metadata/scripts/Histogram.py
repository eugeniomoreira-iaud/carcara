"""Histogram - Simple Histogram Chart Generator

Creates a histogram chart entirely in Grasshopper using Rhino geometry.
No external dependencies - pure Python implementation with full control
over all visual aspects including grid lines and extended axes.

Typical usage:
    Data -> Canvas Rectangle -> Styling Parameters -> Histogram Geometry

Logic:
    1. Calculate histogram bins from data
    2. Map bins to canvas rectangle dimensions
    3. Generate bar rectangles for each bin
    4. Create axis lines with optional extension
    5. Calculate anchor points for labels with alignment offsets
    6. Generate label text strings at specified intervals
    7. Create optional grid lines

Args (Component Inputs):
    cv: (Rectangle3d) Canvas boundary rectangle
        - Type: Rectangle3d
        - Access: item
        - Optional: Yes (defaults to 100x100 at origin)
    
    v: (List[Float]) Data values to histogram
        - Type: list[float]
        - Access: list
        - Optional: No
    
    b: (Integer) Number of histogram bins
        - Type: int
        - Access: item
        - Optional: Yes (defaults to 10)
    
    nx: (Integer) Number of X-axis labels
        - Type: int
        - Access: item
        - Optional: Yes (defaults to bins+1, showing all bin edges)
    
    ny: (Integer) Number of Y-axis labels
        - Type: int
        - Access: item
        - Optional: Yes (defaults to 5)
    
    d: (Integer) Decimal places for all labels
        - Type: int
        - Access: item
        - Optional: Yes (defaults to 1)
    
    ext: (Float) Extension of axes beyond canvas
        - Type: float
        - Access: item
        - Optional: Yes (defaults to 0)
    
    dist: (Float) Distance from axis for both axes
        - Type: float
        - Access: item
        - Optional: Yes (defaults to 10.0)
    
    gy: (Boolean) Draw horizontal grid lines at Y labels
        - Type: bool
        - Access: item
        - Optional: Yes (defaults to False)

Returns (Component Outputs):
    out: (str) Processing log
    bars: (List[Rectangle3d]) Histogram bar rectangles
    axes: (List[Line]) X and Y axis lines
    x_pts: (List[Point3d]) X-axis label anchor points
    x_txt: (List[String]) X-axis label text
    y_pts: (List[Point3d]) Y-axis label anchor points
    y_txt: (List[String]) Y-axis label text
    grid: (List[Line]) Grid lines (if enabled)

Version: 2.1
Date: 2025/11/14
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
import Rhino.Geometry as rg
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML
import System.Drawing

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_charts as charts
importlib.reload(charts)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "2.1"
COMPONENT_DATE = "2025/11/14"

ghenv.Component.Name = "Histogram"
ghenv.Component.NickName = "histogram.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '05.Charts'
ghenv.Component.Description = "Creates histogram charts with full control over styling and grid."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "cv"
ghenv.Component.Params.Input[0].NickName = "cv"
ghenv.Component.Params.Input[0].Description = "Canvas rectangle (default 100x100 at origin)."

ghenv.Component.Params.Input[1].Name = "v"
ghenv.Component.Params.Input[1].NickName = "v"
ghenv.Component.Params.Input[1].Description = "Data values to histogram."

ghenv.Component.Params.Input[2].Name = "b"
ghenv.Component.Params.Input[2].NickName = "b"
ghenv.Component.Params.Input[2].Description = "Number of histogram bins (default 10)."

ghenv.Component.Params.Input[3].Name = "nx"
ghenv.Component.Params.Input[3].NickName = "nx"
ghenv.Component.Params.Input[3].Description = "Number of X-axis labels (default all bin edges)."

ghenv.Component.Params.Input[4].Name = "ny"
ghenv.Component.Params.Input[4].NickName = "ny"
ghenv.Component.Params.Input[4].Description = "Number of Y-axis labels (default 5)."

ghenv.Component.Params.Input[5].Name = "d"
ghenv.Component.Params.Input[5].NickName = "d"
ghenv.Component.Params.Input[5].Description = "Decimal places for labels (default 1)."

ghenv.Component.Params.Input[6].Name = "ext"
ghenv.Component.Params.Input[6].NickName = "ext"
ghenv.Component.Params.Input[6].Description = "Axis extension beyond canvas (default 0)."

ghenv.Component.Params.Input[7].Name = "dist"
ghenv.Component.Params.Input[7].NickName = "dist"
ghenv.Component.Params.Input[7].Description = "Label distance from axis for both axes (default 10.0)."

ghenv.Component.Params.Input[8].Name = "gy"
ghenv.Component.Params.Input[8].NickName = "gy"
ghenv.Component.Params.Input[8].Description = "Draw horizontal grid lines at Y labels (default False)."



################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "bars"
ghenv.Component.Params.Output[1].NickName = "bars"
ghenv.Component.Params.Output[1].Description = "Histogram bar rectangles."

ghenv.Component.Params.Output[2].Name = "axes"
ghenv.Component.Params.Output[2].NickName = "axes"
ghenv.Component.Params.Output[2].Description = "X and Y axis lines."

ghenv.Component.Params.Output[3].Name = "x_pts"
ghenv.Component.Params.Output[3].NickName = "x_pts"
ghenv.Component.Params.Output[3].Description = "X-axis label anchor points."

ghenv.Component.Params.Output[4].Name = "x_txt"
ghenv.Component.Params.Output[4].NickName = "x_txt"
ghenv.Component.Params.Output[4].Description = "X-axis label text."

ghenv.Component.Params.Output[5].Name = "y_pts"
ghenv.Component.Params.Output[5].NickName = "y_pts"
ghenv.Component.Params.Output[5].Description = "Y-axis label anchor points."

ghenv.Component.Params.Output[6].Name = "y_txt"
ghenv.Component.Params.Output[6].NickName = "y_txt"
ghenv.Component.Params.Output[6].Description = "Y-axis label text."

ghenv.Component.Params.Output[7].Name = "grid"
ghenv.Component.Params.Output[7].NickName = "grid"
ghenv.Component.Params.Output[7].Description = "Grid lines."


################
# HIDE PREVIEW
################
ghenv.Component.Params.Output[1].Hidden = True  # bars
ghenv.Component.Params.Output[2].Hidden = True  # axes
ghenv.Component.Params.Output[3].Hidden = True  # x_pts
ghenv.Component.Params.Output[5].Hidden = True  # y_pts
ghenv.Component.Params.Output[7].Hidden = True  # grid


################
# EXECUTION
################
bars = []
axes = []
x_pts = []
x_txt = []
y_pts = []
y_txt = []
grid = []

try:
    # Default canvas
    if cv is None:
        cv = charts.create_default_canvas()
    
    # Call library function - ONE LINE!
    result = charts.create_histogram(
        canvas=cv,
        values=v,
        bins=b if b else 10,
        num_x_labels=nx,
        num_y_labels=ny if ny else 5,
        decimals=d if d is not None else 1,
        extension=ext if ext else 0,
        label_distance=dist if dist else 10.0,
        grid_y=gy if isinstance(gy, bool) else False
    )
    
    # Extract outputs from result dictionary
    bars = result['bars']
    axes = result['axes']
    x_pts = result['x_pts']
    x_txt = result['x_txt']
    y_pts = result['y_pts']
    y_txt = result['y_txt']
    grid = result['grid']
    
    # Log metadata
    meta = result['metadata']
    if meta:
        print("Processed {} values into {} bins".format(meta['num_values'], meta['num_bins']))
        print("Range: {:.2f} to {:.2f}".format(*meta['data_range']))
        print("Max count: {}".format(meta['max_count']))

except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
    ghenv.Component.AddRuntimeMessage(RML.Error, str(e))