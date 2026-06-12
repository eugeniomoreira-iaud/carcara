"""Line Plot - Simple Line Chart Generator

Ultra-thin wrapper around carcara_charts.create_lineplot().
All logic handled by library for easy maintenance and updates.
Supports both flat lists and DataTrees for plotting multiple lines.

Typical usage:
    X/Y Data (List or DataTree) -> Canvas Rectangle -> Styling -> Line Chart

Args (Component Inputs):
    cv: Canvas boundary rectangle
    x: X coordinates (list or DataTree - one series per branch)
    y: Y coordinates (list or DataTree - one series per branch)
    nx: Number of X-axis labels (default 5)
    ny: Number of Y-axis labels (default 5)
    d: Decimal places for labels (default 1)
    ext: Axis extension beyond canvas (default 0)
    dist: Label distance from axis (default 10.0)
    mx: Left margin - % of X range (default 0)
    my: Bottom margin - % of Y range (default 0)
    gx: Draw vertical grid lines (default False)
    gy: Draw horizontal grid lines (default False)

Returns (Component Outputs):
    out: Processing log
    lines: Line chart polylines
    axes: X and Y axis lines
    x_pts: X-axis label anchor points
    x_txt: X-axis label text
    y_pts: Y-axis label anchor points
    y_txt: Y-axis label text
    grid_x: Vertical grid lines (X)
    grid_y: Horizontal grid lines (Y)

Version: 2.0
Date: 2025/11/18
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

# Import library
user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_charts as charts
importlib.reload(charts)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "2.0"
COMPONENT_DATE = "2025/11/18"

ghenv.Component.Name = "Line Plot"
ghenv.Component.NickName = "lineplot.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '05.Charts'
ghenv.Component.Description = "Creates line charts with DataTree support for multiple series."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "cv"
ghenv.Component.Params.Input[0].NickName = "cv"
ghenv.Component.Params.Input[0].Description = "Canvas rectangle (default 100x100 at origin)."

ghenv.Component.Params.Input[1].Name = "x"
ghenv.Component.Params.Input[1].NickName = "x"
ghenv.Component.Params.Input[1].Description = "X coordinates (list or DataTree)."

ghenv.Component.Params.Input[2].Name = "y"
ghenv.Component.Params.Input[2].NickName = "y"
ghenv.Component.Params.Input[2].Description = "Y coordinates (list or DataTree)."

ghenv.Component.Params.Input[3].Name = "nx"
ghenv.Component.Params.Input[3].NickName = "nx"
ghenv.Component.Params.Input[3].Description = "Number of X-axis labels (default 5)."

ghenv.Component.Params.Input[4].Name = "ny"
ghenv.Component.Params.Input[4].NickName = "ny"
ghenv.Component.Params.Input[4].Description = "Number of Y-axis labels (default 5)."

ghenv.Component.Params.Input[5].Name = "d"
ghenv.Component.Params.Input[5].NickName = "d"
ghenv.Component.Params.Input[5].Description = "Decimal places for labels (default 1)."

ghenv.Component.Params.Input[6].Name = "ext"
ghenv.Component.Params.Input[6].NickName = "ext"
ghenv.Component.Params.Input[6].Description = "Axis extension (default 0)."

ghenv.Component.Params.Input[7].Name = "dist"
ghenv.Component.Params.Input[7].NickName = "dist"
ghenv.Component.Params.Input[7].Description = "Label distance from axis (default 10.0)."

ghenv.Component.Params.Input[8].Name = "mx"
ghenv.Component.Params.Input[8].NickName = "mx"
ghenv.Component.Params.Input[8].Description = "Left margin % (default 0)."

ghenv.Component.Params.Input[9].Name = "my"
ghenv.Component.Params.Input[9].NickName = "my"
ghenv.Component.Params.Input[9].Description = "Bottom margin % (default 0)."

ghenv.Component.Params.Input[10].Name = "gx"
ghenv.Component.Params.Input[10].NickName = "gx"
ghenv.Component.Params.Input[10].Description = "Draw vertical grid lines (default False)."

ghenv.Component.Params.Input[11].Name = "gy"
ghenv.Component.Params.Input[11].NickName = "gy"
ghenv.Component.Params.Input[11].Description = "Draw horizontal grid lines (default False)."


################
# OUTPUT METADATA
################
ghenv.Component.Params.Output[1].Name = "lines"
ghenv.Component.Params.Output[1].NickName = "lines"
ghenv.Component.Params.Output[1].Description = "Line chart polylines."

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

ghenv.Component.Params.Output[7].Name = "grid_x"
ghenv.Component.Params.Output[7].NickName = "grid_x"
ghenv.Component.Params.Output[7].Description = "Vertical grid lines."

ghenv.Component.Params.Output[8].Name = "grid_y"
ghenv.Component.Params.Output[8].NickName = "grid_y"
ghenv.Component.Params.Output[8].Description = "Horizontal grid lines."


################
# HIDE PREVIEW
################
ghenv.Component.Params.Output[1].Hidden = True  # lines
ghenv.Component.Params.Output[2].Hidden = True  # axes
ghenv.Component.Params.Output[3].Hidden = True  # x_pts
ghenv.Component.Params.Output[5].Hidden = True  # y_pts
ghenv.Component.Params.Output[7].Hidden = True  # grid_x
ghenv.Component.Params.Output[8].Hidden = True  # grid_y


################
# INPUT HANDLING
################
cv = globals().get('cv', None)
x = globals().get('x', None)
y = globals().get('y', None)
nx = globals().get('nx', 5)
ny = globals().get('ny', 5)
d = globals().get('d', 1)
ext = globals().get('ext', 0)
dist = globals().get('dist', 10.0)
mx = globals().get('mx', 0)
my = globals().get('my', 0)
gx = globals().get('gx', False)
gy = globals().get('gy', False)


################
# EXECUTION
################
lines = []
axes = []
x_pts = []
x_txt = []
y_pts = []
y_txt = []
grid_x = []
grid_y = []

try:
    # Default canvas
    if cv is None:
        cv = charts.create_default_canvas()
        print("Using default 100x100 canvas")
    
    # Validate inputs
    if x is None or y is None:
        print("Error: X and Y data required")
        ghenv.Component.AddRuntimeMessage(RML.Error, "X and Y data required")
    else:
        # Call library function - ONE CALL!
        result = charts.create_lineplot(
            canvas=cv,
            x_series=x,
            y_series=y,
            num_x_labels=nx if nx and nx > 0 else 5,
            num_y_labels=ny if ny and ny > 0 else 5,
            decimals=d if d is not None and d >= 0 else 1,
            extension=ext if ext else 0,
            label_distance=dist if dist else 10.0,
            margin_x=mx if mx and mx >= 0 else 0,
            margin_y=my if my and my >= 0 else 0,
            grid_x=gx if isinstance(gx, bool) else False,
            grid_y=gy if isinstance(gy, bool) else False
        )
        
        # Extract outputs from result dictionary
        lines = result['lines']
        axes = result['axes']
        x_pts = result['x_pts']
        x_txt = result['x_txt']
        y_pts = result['y_pts']
        y_txt = result['y_txt']
        grid_x = result['grid_x']
        grid_y = result['grid_y']
        
        # Log metadata
        meta = result['metadata']
        if meta:
            print("Processed {} line series".format(meta.get('num_series', 0)))
            x_range = meta.get('x_range', (0, 0))
            y_range = meta.get('y_range', (0, 0))
            print("X range: {:.2f} to {:.2f}".format(x_range[0], x_range[1]))
            print("Y range: {:.2f} to {:.2f}".format(y_range[0], y_range[1]))
            print("Line plot complete!")

except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
    ghenv.Component.AddRuntimeMessage(RML.Error, str(e))
