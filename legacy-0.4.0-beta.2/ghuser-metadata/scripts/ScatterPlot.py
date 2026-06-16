"""Scatterplot - Simple Scatter Plot Chart Generator

Ultra-thin wrapper around carcara_charts.create_scatterplot().
All logic handled by library for easy maintenance and updates.
Supports optional color legend based on custom values or Y values.

Typical usage:
    X/Y Data -> Canvas Rectangle -> Styling Parameters -> Scatterplot Geometry

Args (Component Inputs):
    cv: Canvas boundary rectangle
    x: X coordinates of data points
    y: Y coordinates of data points
    r: Dot radius (single value or list for variable sizes, default 2.0)
    nx: Number of X-axis labels (default 5)
    ny: Number of Y-axis labels (default 5)
    d: Decimal places for labels (default 1)
    ext: Axis extension beyond canvas (default 0)
    dist: Label distance from axis (default 10.0)
    mx: Left margin - % of X range (default 0)
    my: Bottom margin - % of Y range (default 0)
    gx: Draw vertical grid lines (default False)
    gy: Draw horizontal grid lines (default False)
    show_leg: Generate color legend (default False)
    col_vals: Values for color mapping (if None, uses Y values)
    colors: Color gradient for legend (required if show_leg=True)
    n_leg: Number of legend steps (default 5)
    leg_w: Legend bar width (default 5% of canvas)
    leg_dist: Distance from canvas to legend (default 20)
    leg_l_dist: Distance from legend to labels (default 5)
    leg_orient: Legend orientation 'vertical' or 'horizontal' (default 'vertical')

Returns (Component Outputs):
    out: Processing log
    dots: Scatter plot circles
    colors_out: Dot colors (if legend enabled)
    axes: X and Y axis lines
    x_pts: X-axis label anchor points
    x_txt: X-axis label text
    y_pts: Y-axis label anchor points
    y_txt: Y-axis label text
    grid_x: Vertical grid lines (X)
    grid_y: Horizontal grid lines (Y)
    leg_cells: Legend rectangles
    leg_clrs: Legend colors
    leg_pts: Legend label points
    leg_txt: Legend labels

Version: 3.0
Date: 2025/11/19
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
COMPONENT_VERSION = "3.0"
COMPONENT_DATE = "2025/11/19"

ghenv.Component.Name = "Scatterplot"
ghenv.Component.NickName = "scatter.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '05.Charts'
ghenv.Component.Description = "Creates scatter plots with variable dot sizes, optional color legend, margins, styling and grid."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "cv"
ghenv.Component.Params.Input[0].NickName = "cv"
ghenv.Component.Params.Input[0].Description = "Canvas rectangle (default 100x100 at origin)."

ghenv.Component.Params.Input[1].Name = "x"
ghenv.Component.Params.Input[1].NickName = "x"
ghenv.Component.Params.Input[1].Description = "X coordinates of data points."

ghenv.Component.Params.Input[2].Name = "y"
ghenv.Component.Params.Input[2].NickName = "y"
ghenv.Component.Params.Input[2].Description = "Y coordinates of data points."

ghenv.Component.Params.Input[3].Name = "r"
ghenv.Component.Params.Input[3].NickName = "r"
ghenv.Component.Params.Input[3].Description = "Dot radius (single value or list, default 2.0)."

ghenv.Component.Params.Input[4].Name = "nx"
ghenv.Component.Params.Input[4].NickName = "nx"
ghenv.Component.Params.Input[4].Description = "Number of X-axis labels (default 5)."

ghenv.Component.Params.Input[5].Name = "ny"
ghenv.Component.Params.Input[5].NickName = "ny"
ghenv.Component.Params.Input[5].Description = "Number of Y-axis labels (default 5)."

ghenv.Component.Params.Input[6].Name = "d"
ghenv.Component.Params.Input[6].NickName = "d"
ghenv.Component.Params.Input[6].Description = "Decimal places for labels (default 1)."

ghenv.Component.Params.Input[7].Name = "ext"
ghenv.Component.Params.Input[7].NickName = "ext"
ghenv.Component.Params.Input[7].Description = "Axis extension (default 0)."

ghenv.Component.Params.Input[8].Name = "dist"
ghenv.Component.Params.Input[8].NickName = "dist"
ghenv.Component.Params.Input[8].Description = "Label distance from axis (default 10.0)."

ghenv.Component.Params.Input[9].Name = "mx"
ghenv.Component.Params.Input[9].NickName = "mx"
ghenv.Component.Params.Input[9].Description = "Left margin % (default 0)."

ghenv.Component.Params.Input[10].Name = "my"
ghenv.Component.Params.Input[10].NickName = "my"
ghenv.Component.Params.Input[10].Description = "Bottom margin % (default 0)."

ghenv.Component.Params.Input[11].Name = "gx"
ghenv.Component.Params.Input[11].NickName = "gx"
ghenv.Component.Params.Input[11].Description = "Draw vertical grid lines (default False)."

ghenv.Component.Params.Input[12].Name = "gy"
ghenv.Component.Params.Input[12].NickName = "gy"
ghenv.Component.Params.Input[12].Description = "Draw horizontal grid lines (default False)."

ghenv.Component.Params.Input[13].Name = "show_leg"
ghenv.Component.Params.Input[13].NickName = "show_leg"
ghenv.Component.Params.Input[13].Description = "Generate color legend (default False)."

ghenv.Component.Params.Input[14].Name = "col_vals"
ghenv.Component.Params.Input[14].NickName = "col_vals"
ghenv.Component.Params.Input[14].Description = "Values for color mapping (if None, uses Y values)."

ghenv.Component.Params.Input[15].Name = "colors"
ghenv.Component.Params.Input[15].NickName = "colors"
ghenv.Component.Params.Input[15].Description = "Color gradient for legend (required if show_leg=True)."

ghenv.Component.Params.Input[16].Name = "n_leg"
ghenv.Component.Params.Input[16].NickName = "n_leg"
ghenv.Component.Params.Input[16].Description = "Number of legend steps (default 5)."

ghenv.Component.Params.Input[17].Name = "leg_w"
ghenv.Component.Params.Input[17].NickName = "leg_w"
ghenv.Component.Params.Input[17].Description = "Legend bar width (default 5% of canvas)."

ghenv.Component.Params.Input[18].Name = "leg_dist"
ghenv.Component.Params.Input[18].NickName = "leg_dist"
ghenv.Component.Params.Input[18].Description = "Distance from canvas to legend (default 20)."

ghenv.Component.Params.Input[19].Name = "leg_l_dist"
ghenv.Component.Params.Input[19].NickName = "leg_l_dist"
ghenv.Component.Params.Input[19].Description = "Distance from legend to labels (default 5)."

ghenv.Component.Params.Input[20].Name = "leg_orient"
ghenv.Component.Params.Input[20].NickName = "leg_orient"
ghenv.Component.Params.Input[20].Description = "Legend orientation: 'vertical' or 'horizontal' (default 'vertical')."


################
# OUTPUT METADATA
################
ghenv.Component.Params.Output[1].Name = "dots"
ghenv.Component.Params.Output[1].NickName = "dots"
ghenv.Component.Params.Output[1].Description = "Scatter plot circles."

ghenv.Component.Params.Output[2].Name = "colors_out"
ghenv.Component.Params.Output[2].NickName = "colors_out"
ghenv.Component.Params.Output[2].Description = "Dot colors (if legend enabled)."

ghenv.Component.Params.Output[3].Name = "axes"
ghenv.Component.Params.Output[3].NickName = "axes"
ghenv.Component.Params.Output[3].Description = "X and Y axis lines."

ghenv.Component.Params.Output[4].Name = "x_pts"
ghenv.Component.Params.Output[4].NickName = "x_pts"
ghenv.Component.Params.Output[4].Description = "X-axis label anchor points."

ghenv.Component.Params.Output[5].Name = "x_txt"
ghenv.Component.Params.Output[5].NickName = "x_txt"
ghenv.Component.Params.Output[5].Description = "X-axis label text."

ghenv.Component.Params.Output[6].Name = "y_pts"
ghenv.Component.Params.Output[6].NickName = "y_pts"
ghenv.Component.Params.Output[6].Description = "Y-axis label anchor points."

ghenv.Component.Params.Output[7].Name = "y_txt"
ghenv.Component.Params.Output[7].NickName = "y_txt"
ghenv.Component.Params.Output[7].Description = "Y-axis label text."

ghenv.Component.Params.Output[8].Name = "grid_x"
ghenv.Component.Params.Output[8].NickName = "grid_x"
ghenv.Component.Params.Output[8].Description = "Vertical grid lines."

ghenv.Component.Params.Output[9].Name = "grid_y"
ghenv.Component.Params.Output[9].NickName = "grid_y"
ghenv.Component.Params.Output[9].Description = "Horizontal grid lines."

ghenv.Component.Params.Output[10].Name = "leg_cells"
ghenv.Component.Params.Output[10].NickName = "leg_cells"
ghenv.Component.Params.Output[10].Description = "Legend rectangles."

ghenv.Component.Params.Output[11].Name = "leg_clrs"
ghenv.Component.Params.Output[11].NickName = "leg_clrs"
ghenv.Component.Params.Output[11].Description = "Legend colors."

ghenv.Component.Params.Output[12].Name = "leg_pts"
ghenv.Component.Params.Output[12].NickName = "leg_pts"
ghenv.Component.Params.Output[12].Description = "Legend label points."

ghenv.Component.Params.Output[13].Name = "leg_txt"
ghenv.Component.Params.Output[13].NickName = "leg_txt"
ghenv.Component.Params.Output[13].Description = "Legend labels."


################
# HIDE PREVIEW
################
ghenv.Component.Params.Output[1].Hidden = True  # dots
ghenv.Component.Params.Output[3].Hidden = True  # axes
ghenv.Component.Params.Output[4].Hidden = True  # x_pts
ghenv.Component.Params.Output[6].Hidden = True  # y_pts
ghenv.Component.Params.Output[8].Hidden = True  # grid_x
ghenv.Component.Params.Output[9].Hidden = True  # grid_y
ghenv.Component.Params.Output[10].Hidden = True  # leg_cells
ghenv.Component.Params.Output[12].Hidden = True  # leg_pts


################
# INPUT HANDLING
################
cv = globals().get('cv', None)
x = globals().get('x', None)
y = globals().get('y', None)
r = globals().get('r', 2.0)
nx = globals().get('nx', 5)
ny = globals().get('ny', 5)
d = globals().get('d', 1)
ext = globals().get('ext', 0)
dist = globals().get('dist', 10.0)
mx = globals().get('mx', 0)
my = globals().get('my', 0)
gx = globals().get('gx', False)
gy = globals().get('gy', False)
show_leg = globals().get('show_leg', False)
col_vals = globals().get('col_vals', None)
colors = globals().get('colors', None)
n_leg = globals().get('n_leg', 5)
leg_w = globals().get('leg_w', None)
leg_dist = globals().get('leg_dist', 20.0)
leg_l_dist = globals().get('leg_l_dist', 5.0)
leg_orient = globals().get('leg_orient', 'vertical')


################
# EXECUTION
################
dots = []
colors_out = []
axes = []
x_pts = []
x_txt = []
y_pts = []
y_txt = []
grid_x = []
grid_y = []
leg_cells = []
leg_clrs = []
leg_pts = []
leg_txt = []

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
        # Validate legend setup
        if show_leg and colors is None:
            print("Warning: Legend enabled but no colors provided")
            ghenv.Component.AddRuntimeMessage(RML.Warning, "Color gradient required for legend")
        
        # Call library function - ONE CALL!
        result = charts.create_scatterplot(
            canvas=cv,
            x_values=x,
            y_values=y,
            radii=r if r is not None else 2.0,
            num_x_labels=nx if nx and nx > 0 else 5,
            num_y_labels=ny if ny and ny > 0 else 5,
            decimals=d if d is not None and d >= 0 else 1,
            extension=ext if ext else 0,
            label_distance=dist if dist else 10.0,
            margin_x=mx if mx and mx >= 0 else 0,
            margin_y=my if my and my >= 0 else 0,
            grid_x=gx if isinstance(gx, bool) else False,
            grid_y=gy if isinstance(gy, bool) else False,
            show_legend=show_leg if isinstance(show_leg, bool) else False,
            color_values=col_vals,
            color_gradient=colors,
            num_legend_steps=n_leg if n_leg and n_leg > 0 else 5,
            legend_width=leg_w,
            legend_label_distance=leg_l_dist if leg_l_dist else 5.0,
            legend_orientation=leg_orient if leg_orient in ['vertical', 'horizontal'] else 'vertical',
            legend_distance=leg_dist if leg_dist else 20.0
        )
        
        # Extract outputs from result dictionary
        dots = result['dots']
        colors_out = result['colors']
        axes = result['axes']
        x_pts = result['x_pts']
        x_txt = result['x_txt']
        y_pts = result['y_pts']
        y_txt = result['y_txt']
        grid_x = result['grid_x']
        grid_y = result['grid_y']
        leg_cells = result['legend_cells']
        leg_clrs = result['legend_colors']
        leg_pts = result['legend_pts']
        leg_txt = result['legend_txt']
        
        # Log metadata
        meta = result['metadata']
        if meta:
            print("Processed {} data points".format(meta.get('num_points', 0)))
            x_range = meta.get('x_range', (0, 0))
            y_range = meta.get('y_range', (0, 0))
            print("X range: {:.2f} to {:.2f}".format(x_range[0], x_range[1]))
            print("Y range: {:.2f} to {:.2f}".format(y_range[0], y_range[1]))
            
            if meta.get('has_legend'):
                color_range = meta.get('color_range', (0, 0))
                print("Legend: Color range {:.2f} to {:.2f}".format(color_range[0], color_range[1]))
            
            print("Scatterplot complete!")

except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
    ghenv.Component.AddRuntimeMessage(RML.Error, str(e))
