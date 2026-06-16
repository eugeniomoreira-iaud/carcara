"""Heatmap - 2D Matrix Heatmap Chart Generator

Ultra-thin wrapper around carcara_charts.create_heatmap().
All logic handled by library for easy maintenance and updates.

Typical usage:
    Data Matrix + Color Gradient -> Canvas Rectangle -> Styling -> Heatmap

Args (Component Inputs):
    cv: Canvas boundary rectangle
    data: 2D matrix (DataTree or nested list) - REQUIRED
    colors: Color gradient (list of colors, min 2) - REQUIRED
    rows: Row labels (optional)
    cols: Column labels (optional)
    vals: Show values in cells (default False)
    d: Decimal places (default 1)
    n_leg: Number of legend steps (default 5)
    dist: Label distance from canvas (default 10)
    leg_w: Legend bar width (default 5% of canvas)
    leg_dist: Distance from canvas to legend (default 20)
    leg_l_dist: Distance from legend to legend labels (default 5)
    leg_orient: Legend orientation 'vertical' or 'horizontal' (default 'vertical')

Returns (Component Outputs):
    out: Processing log
    cells: Grid rectangles
    clrs: Cell colors (R,G,B tuples)
    row_pts: Row label points
    row_txt: Row label text
    col_pts: Column label points
    col_txt: Column label text
    val_pts: Value label points (if vals=True)
    val_txt: Value label text (if vals=True)
    leg_cells: Legend rectangles
    leg_clrs: Legend colors
    leg_pts: Legend label points
    leg_txt: Legend labels

Version: 1.1
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
COMPONENT_VERSION = "1.1"
COMPONENT_DATE = "2025/11/19"

ghenv.Component.Name = "Heatmap"
ghenv.Component.NickName = "heatmap.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '05.Charts'
ghenv.Component.Description = "Creates heatmap charts from 2D matrix data with custom color gradient."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "cv"
ghenv.Component.Params.Input[0].NickName = "cv"
ghenv.Component.Params.Input[0].Description = "Canvas rectangle (default 200x200 at origin)."

ghenv.Component.Params.Input[1].Name = "data"
ghenv.Component.Params.Input[1].NickName = "data"
ghenv.Component.Params.Input[1].Description = "2D matrix (DataTree or nested list)."

ghenv.Component.Params.Input[2].Name = "colors"
ghenv.Component.Params.Input[2].NickName = "colors"
ghenv.Component.Params.Input[2].Description = "Color gradient (list of colors, min 2)."

ghenv.Component.Params.Input[3].Name = "rows"
ghenv.Component.Params.Input[3].NickName = "rows"
ghenv.Component.Params.Input[3].Description = "Row labels (optional)."

ghenv.Component.Params.Input[4].Name = "cols"
ghenv.Component.Params.Input[4].NickName = "cols"
ghenv.Component.Params.Input[4].Description = "Column labels (optional)."

ghenv.Component.Params.Input[5].Name = "vals"
ghenv.Component.Params.Input[5].NickName = "vals"
ghenv.Component.Params.Input[5].Description = "Show values in cells (default False)."

ghenv.Component.Params.Input[6].Name = "d"
ghenv.Component.Params.Input[6].NickName = "d"
ghenv.Component.Params.Input[6].Description = "Decimal places for values (default 1)."

ghenv.Component.Params.Input[7].Name = "n_leg"
ghenv.Component.Params.Input[7].NickName = "n_leg"
ghenv.Component.Params.Input[7].Description = "Number of legend steps (default 5)."

ghenv.Component.Params.Input[8].Name = "dist"
ghenv.Component.Params.Input[8].NickName = "dist"
ghenv.Component.Params.Input[8].Description = "Label distance from canvas (default 10.0)."

ghenv.Component.Params.Input[9].Name = "leg_w"
ghenv.Component.Params.Input[9].NickName = "leg_w"
ghenv.Component.Params.Input[9].Description = "Legend bar width (default 5% of canvas)."

ghenv.Component.Params.Input[10].Name = "leg_dist"
ghenv.Component.Params.Input[10].NickName = "leg_dist"
ghenv.Component.Params.Input[10].Description = "Distance from canvas to legend (default 20)."

ghenv.Component.Params.Input[11].Name = "leg_l_dist"
ghenv.Component.Params.Input[11].NickName = "leg_l_dist"
ghenv.Component.Params.Input[11].Description = "Distance from legend to legend labels (default 5)."

ghenv.Component.Params.Input[12].Name = "leg_orient"
ghenv.Component.Params.Input[12].NickName = "leg_orient"
ghenv.Component.Params.Input[12].Description = "Legend orientation: 'vertical' or 'horizontal' (default 'vertical')."


################
# OUTPUT METADATA
################
ghenv.Component.Params.Output[1].Name = "cells"
ghenv.Component.Params.Output[1].NickName = "cells"
ghenv.Component.Params.Output[1].Description = "Grid rectangles."

ghenv.Component.Params.Output[2].Name = "clrs"
ghenv.Component.Params.Output[2].NickName = "clrs"
ghenv.Component.Params.Output[2].Description = "Cell colors (R,G,B tuples)."

ghenv.Component.Params.Output[3].Name = "row_pts"
ghenv.Component.Params.Output[3].NickName = "row_pts"
ghenv.Component.Params.Output[3].Description = "Row label anchor points."

ghenv.Component.Params.Output[4].Name = "row_txt"
ghenv.Component.Params.Output[4].NickName = "row_txt"
ghenv.Component.Params.Output[4].Description = "Row label text."

ghenv.Component.Params.Output[5].Name = "col_pts"
ghenv.Component.Params.Output[5].NickName = "col_pts"
ghenv.Component.Params.Output[5].Description = "Column label anchor points."

ghenv.Component.Params.Output[6].Name = "col_txt"
ghenv.Component.Params.Output[6].NickName = "col_txt"
ghenv.Component.Params.Output[6].Description = "Column label text."

ghenv.Component.Params.Output[7].Name = "val_pts"
ghenv.Component.Params.Output[7].NickName = "val_pts"
ghenv.Component.Params.Output[7].Description = "Value label points (if vals=True)."

ghenv.Component.Params.Output[8].Name = "val_txt"
ghenv.Component.Params.Output[8].NickName = "val_txt"
ghenv.Component.Params.Output[8].Description = "Value label text (if vals=True)."

ghenv.Component.Params.Output[9].Name = "leg_cells"
ghenv.Component.Params.Output[9].NickName = "leg_cells"
ghenv.Component.Params.Output[9].Description = "Legend rectangles."

ghenv.Component.Params.Output[10].Name = "leg_clrs"
ghenv.Component.Params.Output[10].NickName = "leg_clrs"
ghenv.Component.Params.Output[10].Description = "Legend colors."

ghenv.Component.Params.Output[11].Name = "leg_pts"
ghenv.Component.Params.Output[11].NickName = "leg_pts"
ghenv.Component.Params.Output[11].Description = "Legend label points."

ghenv.Component.Params.Output[12].Name = "leg_txt"
ghenv.Component.Params.Output[12].NickName = "leg_txt"
ghenv.Component.Params.Output[12].Description = "Legend labels."


################
# HIDE PREVIEW
################
ghenv.Component.Params.Output[1].Hidden = True  # cells
ghenv.Component.Params.Output[3].Hidden = True  # row_pts
ghenv.Component.Params.Output[5].Hidden = True  # col_pts
ghenv.Component.Params.Output[7].Hidden = True  # val_pts
ghenv.Component.Params.Output[9].Hidden = True  # leg_cells
ghenv.Component.Params.Output[11].Hidden = True  # leg_pts


################
# INPUT HANDLING
################
cv = globals().get('cv', None)
data = globals().get('data', None)
colors = globals().get('colors', None)
rows = globals().get('rows', None)
cols = globals().get('cols', None)
vals = globals().get('vals', False)
d = globals().get('d', 1)
n_leg = globals().get('n_leg', 5)
dist = globals().get('dist', 10.0)
leg_w = globals().get('leg_w', None)
leg_dist = globals().get('leg_dist', 20.0)
leg_l_dist = globals().get('leg_l_dist', 5.0)
leg_orient = globals().get('leg_orient', 'vertical')


################
# EXECUTION
################
cells = []
clrs = []
row_pts = []
row_txt = []
col_pts = []
col_txt = []
val_pts = []
val_txt = []
leg_cells = []
leg_clrs = []
leg_pts = []
leg_txt = []

try:
    # Default canvas
    if cv is None:
        cv = charts.create_default_canvas(width=200, height=200)
        print("Using default 200x200 canvas")
    
    # Validate required inputs
    if data is None:
        print("Error: No data provided")
        ghenv.Component.AddRuntimeMessage(RML.Error, "No data provided")
    elif colors is None:
        print("Error: No color gradient provided")
        ghenv.Component.AddRuntimeMessage(RML.Error, "Color gradient required (min 2 colors)")
    else:
        # Validate colors
        is_valid, error_msg = charts.validate_color_list(colors)
        if not is_valid:
            print("Error: {}".format(error_msg))
            ghenv.Component.AddRuntimeMessage(RML.Error, error_msg)
        else:
            # Parse matrix data
            data_matrix = charts.parse_data_input(data)
            
            if not data_matrix:
                print("Error: Data is empty")
                ghenv.Component.AddRuntimeMessage(RML.Error, "Data is empty")
            else:
                # Validate orientation
                if leg_orient not in ['vertical', 'horizontal']:
                    leg_orient = 'vertical'
                
                # Call library function - ONE CALL!
                result = charts.create_heatmap(
                    canvas=cv,
                    data_matrix=data_matrix,
                    color_gradient=colors,
                    row_labels=rows,
                    col_labels=cols,
                    show_values=vals if isinstance(vals, bool) else False,
                    decimals=d if d is not None and d >= 0 else 1,
                    num_legend_steps=n_leg if n_leg and n_leg > 0 else 5,
                    label_distance=dist if dist else 10.0,
                    legend_width=leg_w,
                    legend_label_distance=leg_l_dist if leg_l_dist else 5.0,
                    legend_orientation=leg_orient,
                    legend_distance=leg_dist if leg_dist else 20.0
                )

                
                
                # Extract outputs from result dictionary
                cells = result['cells']
                clrs = result['colors']
                row_pts = result['row_pts']
                row_txt = result['row_txt']
                col_pts = result['col_pts']
                col_txt = result['col_txt']
                val_pts = result['value_pts']
                val_txt = result['value_txt']
                leg_cells = result['legend_cells']
                leg_clrs = result['legend_colors']
                leg_pts = result['legend_pts']
                leg_txt = result['legend_txt']
                
                # Log metadata
                meta = result['metadata']
                if meta:
                    print("Processed {} colors into gradient".format(meta.get('num_colors', 0)))
                    print("Created {}×{} heatmap".format(meta.get('num_rows', 0), meta.get('num_cols', 0)))
                    value_range = meta.get('value_range', (0, 0))
                    print("Value range: {:.2f} to {:.2f}".format(value_range[0], value_range[1]))
                    print("Legend: {}".format(meta.get('legend_orientation', 'vertical')))
                    print("Heatmap complete!")

except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
    ghenv.Component.AddRuntimeMessage(RML.Error, str(e))


