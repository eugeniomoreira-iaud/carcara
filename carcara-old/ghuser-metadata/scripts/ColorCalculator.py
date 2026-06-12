"""Color Calculation - Data-Driven Color Assignment with Legend

This component calculates colors for mesh volumes based on numerical values.
Supports continuous gradients, fixed class count, or custom class boundaries
(as a list of range breaks). Outputs colors as a tree matching input value
structure for use with Custom Preview components. Generates legend geometry
and supplies text anchor points and sizes for direct use with Grasshopper's
Text Tag 3D or similar annotation components.

Typical usage:
    Values -> Color Calc -> Colors -> Custom Preview (meshes)
    Legend outputs -> Text Tag 3D (for legend labels)

Segments Logic:
    - If classes = 0: Uses segments for continuous gradient
    - If integer and classes < segments: legend has classes segments
    - If integer and classes >= segments: legend has segments segments (capped)
    - If cls is a list/array: Treated as class boundaries; legend matches (up to segments cap)

Classes input (`cls`) can be:
    - Integer (single value): Number of classes (auto-binned)
    - List (multiple values): List of numeric class boundaries e.g. [0, 3, 5, 7]
      (this creates classes for [0–3), [3–5), [5–7])

Configuration Keys (leg_cfg):
    - title: Legend title text (string)
    - title_size: Title text height multiplier (float, default: 1.5)
    - min: Minimum value for legend range (float, auto-calculated if omitted)
    - max: Maximum value for legend range (float, auto-calculated if omitted)
    - segments: Maximum number of legend segments (int, default: 11)
    - decimals: Decimal places for value labels (int, default: 2)
    - vertical: Legend orientation (True=vertical, False=horizontal)
    - seg_height: Height of each legend segment (float, default: 1.0)
    - seg_width: Width of legend bar (float, default: 1.0)
    - text_height: Value label height (float, default: 0.5)
    - scale: Multiplier for all legend sizes (float, default: 1.0)
    - title_offset: Distance from legend top to title (float, default: 1.0 segment units)
    - label_offset: Distance from legend bar to value labels (default: 0.5)

Args (Component Inputs):
    val: (Tree[float]) Tree of values for color mapping. One value per mesh.
    col: (List[Color]) Color gradient or list of colors (min 2, default: Ladybug gradient)
    cls: (int or list[float]) Number of classes (int) OR boundaries (list of floats)
        - Integer: auto-classifies to this count.
        - List: explicit bin boundaries, e.g. [0, 5, 10] means two classes [0-5), [5-10].
    lin: (bool) True for linear intervals, False for percentile-based (default: True)
    leg_cfg: (string) Legend config. Key-value pairs, one per line, see above
    leg_pln: (Plane) Base plane for the legend geometry (default: World XY)

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    col: (Tree[Color]) Colors for each value (tree structure matches input values)
    leg_geo: (Mesh) Legend gradient bar mesh (with vertex colors)
    txt_loc: (List[Point3d]) Text anchor points (first is title, if any, rest are value labels) [Hidden]
    txt_con: (List[str]) Text strings (first is title, if any, rest are value labels)
    txt_siz: (List[float]) Text heights (first is title, if any, rest are values)
    stats: (str) Statistical summary of input values

Configuration Format Example:
    title: Building Height Analysis
    title_size: 1.8
    title_offset: 1.2
    label_offset: 0.6
    min: 0
    max: 10
    segments: 10
    decimals: 1
    vertical: True
    seg_height: 2.0
    seg_width: 1.0
    text_height: 0.6
    scale: 1.2

Version: 1.1
Date: 2025/11/13
"""

################
# IMPORTS
################
import sys
import math
import clr
clr.AddReference("Grasshopper")
clr.AddReference("System.Drawing")
clr.AddReference("RhinoCommon")

from System.Drawing import Color
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML
import Rhino.Geometry as rg

# Store built-in functions before any variable shadowing
_max = max
_min = min


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "1.1"
COMPONENT_DATE = "2025/11/13"

ghenv.Component.Name = "Color Calculator"
ghenv.Component.NickName = "ColorCalc.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '01.Modeling'
ghenv.Component.Description = (
    "Colors mesh volumes by value. Manual or auto-classification; custom legend layout & breaks.")
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "val"
ghenv.Component.Params.Input[0].NickName = "val"
ghenv.Component.Params.Input[0].Description = "Tree of values for color mapping (one value per mesh)."

ghenv.Component.Params.Input[1].Name = "col"
ghenv.Component.Params.Input[1].NickName = "col"
ghenv.Component.Params.Input[1].Description = "List of colors defining the gradient (min 2 colors required)."

ghenv.Component.Params.Input[2].Name = "cls"
ghenv.Component.Params.Input[2].NickName = "cls"
ghenv.Component.Params.Input[2].Description = (
    "Classification bins for coloring. Use:\n"
    "  - 0: Continuous color distribution (gradient for each value, no discrete bins)\n"
    "  - Integer > 0: Fixed number of classes (auto-splits data range)\n"
    "  - List[float]: Explicit class breakpoints (e.g. [0,5,10,14] makes bins: 0-5, 5-10, 10-14)\n"
    "The legend adapts to match your choice. (Default: 0 = continuous mode)."
)

ghenv.Component.Params.Input[3].Name = "lin"
ghenv.Component.Params.Input[3].NickName = "lin"
ghenv.Component.Params.Input[3].Description = "True=linear intervals, False=percentile breakpoints (auto only)."

ghenv.Component.Params.Input[4].Name = "leg_cfg"
ghenv.Component.Params.Input[4].NickName = "leg_cfg"
ghenv.Component.Params.Input[4].Description = (
    "Legend config as 'key: value' pairs, multiline panel. Keys: "
    "title, title_size, min, max, segments, decimals, vertical, seg_height, seg_width, "
    "text_height, scale, title_offset, label_offset."
)

ghenv.Component.Params.Input[5].Name = "leg_pln"
ghenv.Component.Params.Input[5].NickName = "leg_pln"
ghenv.Component.Params.Input[5].Description = "Base plane for legend positioning (default: World XY)."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "col"
ghenv.Component.Params.Output[1].NickName = "col"
ghenv.Component.Params.Output[1].Description = "Tree of colors matching input value structure."

ghenv.Component.Params.Output[2].Name = "leg_geo"
ghenv.Component.Params.Output[2].NickName = "leg_geo"
ghenv.Component.Params.Output[2].Description = "Legend mesh (colored, for Custom Preview)."

ghenv.Component.Params.Output[3].Name = "txt_loc"
ghenv.Component.Params.Output[3].NickName = "txt_loc"
ghenv.Component.Params.Output[3].Description = "Text anchor points (title first, label per segment)."
ghenv.Component.Params.Output[3].Hidden = True

ghenv.Component.Params.Output[4].Name = "txt_con"
ghenv.Component.Params.Output[4].NickName = "txt_con"
ghenv.Component.Params.Output[4].Description = "Text content (title first, then per legend bin)."

ghenv.Component.Params.Output[5].Name = "txt_siz"
ghenv.Component.Params.Output[5].NickName = "txt_siz"
ghenv.Component.Params.Output[5].Description = "Text heights (title first, then labels); matches text_loc and txt_con."

ghenv.Component.Params.Output[6].Name = "stats"
ghenv.Component.Params.Output[6].NickName = "stats"
ghenv.Component.Params.Output[6].Description = "Statistical summary (min, max, mean, median, valid count)."


################
# LEGEND CONFIGURATION CLASS
################
class LegendConfig(object):
    """Configuration for legend visualization."""
    
    def __init__(self):
        self.min = None
        self.max = None
        self.segments = 11
        self.decimals = 2
        self.vertical = True
        self.seg_height = 1.0
        self.seg_width = 1.0
        self.text_height = 0.5
        self.title = None
        self.title_size = 1.5
        self.scale = 1.0
        self.title_offset = 1.0
        self.label_offset = 0.5
    
    def __repr__(self):
        return "LegendConfig(min={}, max={}, segments={}, title='{}', scale={})".format(
            self.min, self.max, self.segments, self.title, self.scale
        )


################
# HELPER FUNCTIONS
################
def log(message):
    """
    Print message to default 'out' output.
    
    Args:
        message (str): Message text to log
    """
    print(message)


def report(level, message):
    """
    Send runtime message to Grasshopper component (warnings/errors only).
    
    Args:
        level (GH_RuntimeMessageLevel): Message severity level
        message (str): Message text to display
    """
    ghenv.Component.AddRuntimeMessage(level, message)
    log(message)


def get_input_value(param_names):
    """Get input value by checking multiple possible parameter names."""
    for name in param_names:
        value = globals().get(name, None)
        if value is not None:
            return value
    return None


def parse_legend_config(config_text):
    """Parse legend configuration from text."""
    config = LegendConfig()
    
    if config_text is None:
        return config
    
    try:
        if not isinstance(config_text, str):
            config_text = str(config_text)
    except:
        return config
    
    config_text = config_text.strip()
    if not config_text:
        return config
    
    try:
        for line in config_text.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'title':
                config.title = value
            elif key == 'title_size' or key == 'titlesize':
                config.title_size = _max(0.1, float(value))
            elif key == 'title_offset' or key == 'titleoffset':
                config.title_offset = _max(0.0, float(value))
            elif key == 'label_offset' or key == 'labeloffset':
                config.label_offset = _max(0.0, float(value))
            elif key == 'min':
                config.min = float(value)
            elif key == 'max':
                config.max = float(value)
            elif key == 'segments' or key == 'segment_count' or key == 'seg_count':
                config.segments = _max(2, int(value))
            elif key == 'decimals' or key == 'decimal_places':
                config.decimals = _max(0, int(value))
            elif key == 'vertical':
                config.vertical = value.lower() in ('true', 'yes', '1', 't', 'y')
            elif key == 'seg_height' or key == 'segment_height':
                config.seg_height = _max(0.1, float(value))
            elif key == 'seg_width' or key == 'segment_width':
                config.seg_width = _max(0.1, float(value))
            elif key == 'text_height':
                config.text_height = _max(0.1, float(value))
            elif key == 'scale':
                config.scale = _max(0.1, float(value))
    
    except Exception as e:
        log("Warning: Error parsing legend config: {}. Using defaults.".format(e))
    
    return config


def flatten_tree(tree):
    """Flatten a DataTree into a list of (path, branch_data) tuples."""
    result = []
    for i in range(tree.BranchCount):
        path = tree.Path(i)
        branch = list(tree.Branch(i))
        result.append((path, branch))
    return result


def validate_inputs(value_tree, color_list):
    """Validate all input parameters before processing."""
    if value_tree is None or value_tree.BranchCount == 0:
        return False, "No values provided.", 0, 0
    
    if color_list is None or len(color_list) < 2:
        return False, "At least 2 colors required for gradient.", 0, 0
    
    value_branches = flatten_tree(value_tree)
    
    value_count = 0
    null_count = 0
    for _, branch in value_branches:
        for item in branch:
            if item is not None:
                try:
                    float(item)
                    value_count += 1
                except (ValueError, TypeError):
                    null_count += 1
            else:
                null_count += 1
    
    if null_count > 0:
        log("Note: {} null/invalid items detected (will be assigned gray)".format(null_count))
    
    return True, None, value_count, null_count


def calculate_statistics(all_values):
    """Calculate statistics for all values."""
    valid_values = [v for v in all_values if v is not None and not math.isnan(float(v)) and not math.isinf(float(v))]
    
    if len(valid_values) == 0:
        return {
            'min': 0.0,
            'max': 0.0,
            'mean': 0.0,
            'median': 0.0,
            'valid_count': 0
        }
    
    sorted_values = sorted(valid_values)
    
    return {
        'min': sorted_values[0],
        'max': sorted_values[-1],
        'mean': sum(sorted_values) / len(sorted_values),
        'median': sorted_values[len(sorted_values) // 2],
        'valid_count': len(sorted_values)
    }


def interpolate_color(color_list, t):
    """Interpolate color from gradient at position t (0-1)."""
    if len(color_list) == 1:
        return color_list[0]
    
    t = _max(0.0, _min(1.0, t))
    scaled = t * (len(color_list) - 1)
    
    i1 = int(math.floor(scaled))
    i2 = int(math.ceil(scaled))
    
    i1 = _max(0, _min(len(color_list) - 1, i1))
    i2 = _max(0, _min(len(color_list) - 1, i2))
    
    if i1 == i2:
        return color_list[i1]
    
    local_t = scaled - i1
    c1 = color_list[i1]
    c2 = color_list[i2]
    
    return Color.FromArgb(
        int(c1.A + (c2.A - c1.A) * local_t),
        int(c1.R + (c2.R - c1.R) * local_t),
        int(c1.G + (c2.G - c1.G) * local_t),
        int(c1.B + (c2.B - c1.B) * local_t)
    )


def get_continuous_color(value, min_bound, max_bound, color_list):
    """Get color for continuous gradient mode."""
    if value is None or math.isnan(float(value)) or math.isinf(float(value)):
        return Color.Gray
    
    value_range = max_bound - min_bound
    if value_range < 0.0001:
        return color_list[0]
    
    value = _max(min_bound, _min(max_bound, float(value)))
    
    t = (value - min_bound) / value_range
    return interpolate_color(color_list, t)


def create_linear_classes(min_val, max_val, num_classes):
    """Create linear classification ranges."""
    value_range = max_val - min_val
    
    if value_range < 0.0001:
        return [{'min': min_val, 'max': max_val, 'count': 0}]
    
    class_size = value_range / num_classes
    classes = []
    
    for i in range(num_classes):
        classes.append({
            'min': min_val + i * class_size,
            'max': max_val if i == num_classes - 1 else min_val + (i + 1) * class_size,
            'count': 0
        })
    
    return classes


def create_percentile_classes(all_values, num_classes):
    """Create percentile-based classification ranges."""
    valid_values = [v for v in all_values if v is not None and not math.isnan(float(v)) and not math.isinf(float(v))]
    sorted_values = sorted(valid_values)
    
    if len(sorted_values) == 0:
        return []
    
    classes = []
    per_class = len(sorted_values) // num_classes
    
    for i in range(num_classes):
        start = i * per_class
        end = len(sorted_values) - 1 if i == num_classes - 1 else (i + 1) * per_class - 1
        
        classes.append({
            'min': sorted_values[start],
            'max': sorted_values[end],
            'count': 0
        })
    
    return classes


def find_class_index(value, class_ranges):
    """Find which class a value belongs to."""
    for i, class_range in enumerate(class_ranges):
        if i == len(class_ranges) - 1:
            if value >= class_range['min'] and value <= class_range['max']:
                return i
        else:
            if value >= class_range['min'] and value < class_range['max']:
                return i
    
    return 0 if value < class_ranges[0]['min'] else len(class_ranges) - 1


def map_colors_to_classes(color_list, num_classes):
    """Map color gradient to discrete class colors."""
    result = []
    for i in range(num_classes):
        t = 0.0 if num_classes == 1 else float(i) / (num_classes - 1)
        result.append(interpolate_color(color_list, t))
    return result


def generate_legend_geometry(legend_cfg, class_ranges, class_colors, base_plane):
    """Generate legend mesh geometry and text parameters."""
    # Apply scale to all dimensions
    scaled_seg_height = legend_cfg.seg_height * legend_cfg.scale
    scaled_seg_width = legend_cfg.seg_width * legend_cfg.scale
    scaled_text_height = legend_cfg.text_height * legend_cfg.scale
    scaled_title_height = scaled_text_height * legend_cfg.title_size
    scaled_title_offset = legend_cfg.title_offset * scaled_seg_height
    scaled_label_offset = legend_cfg.label_offset * scaled_seg_height
    
    num_segments = len(class_ranges)
    
    # Create legend mesh
    legend_mesh = rg.Mesh()
    
    # Text parameters lists
    text_locations = []
    text_contents = []
    text_sizes = []
    
    if legend_cfg.vertical:
        # Vertical legend
        for i, (class_range, color) in enumerate(zip(class_ranges, class_colors)):
            y_start = i * scaled_seg_height
            y_end = (i + 1) * scaled_seg_height
            
            pt0 = base_plane.PointAt(0, y_start, 0)
            pt1 = base_plane.PointAt(scaled_seg_width, y_start, 0)
            pt2 = base_plane.PointAt(scaled_seg_width, y_end, 0)
            pt3 = base_plane.PointAt(0, y_end, 0)
            
            v0 = legend_mesh.Vertices.Add(pt0)
            v1 = legend_mesh.Vertices.Add(pt1)
            v2 = legend_mesh.Vertices.Add(pt2)
            v3 = legend_mesh.Vertices.Add(pt3)
            
            legend_mesh.Faces.AddFace(v0, v1, v2, v3)
            for _ in range(4):
                legend_mesh.VertexColors.Add(color)
        
        # Add title first if specified
        if legend_cfg.title:
            title_pt = base_plane.PointAt(
                0,
                num_segments * scaled_seg_height + scaled_title_offset,
                0
            )
            text_locations.append(title_pt)
            text_contents.append(legend_cfg.title)
            text_sizes.append(scaled_title_height)
        
        # Add value labels
        for i, class_range in enumerate(class_ranges):
            y_mid = (i + 0.5) * scaled_seg_height
            
            label_pt = base_plane.PointAt(
                scaled_seg_width + scaled_label_offset,
                y_mid,
                0
            )
            
            label_text = "{0:.{2}f} - {1:.{2}f}".format(
                class_range['min'], 
                class_range['max'], 
                legend_cfg.decimals
            )
            
            text_locations.append(label_pt)
            text_contents.append(label_text)
            text_sizes.append(scaled_text_height)
    
    else:
        # Horizontal legend
        for i, (class_range, color) in enumerate(zip(class_ranges, class_colors)):
            x_start = i * scaled_seg_height
            x_end = (i + 1) * scaled_seg_height
            
            pt0 = base_plane.PointAt(x_start, 0, 0)
            pt1 = base_plane.PointAt(x_end, 0, 0)
            pt2 = base_plane.PointAt(x_end, scaled_seg_width, 0)
            pt3 = base_plane.PointAt(x_start, scaled_seg_width, 0)
            
            v0 = legend_mesh.Vertices.Add(pt0)
            v1 = legend_mesh.Vertices.Add(pt1)
            v2 = legend_mesh.Vertices.Add(pt2)
            v3 = legend_mesh.Vertices.Add(pt3)
            
            legend_mesh.Faces.AddFace(v0, v1, v2, v3)
            for _ in range(4):
                legend_mesh.VertexColors.Add(color)
        
        # Add title first if specified
        if legend_cfg.title:
            title_pt = base_plane.PointAt(
                0,
                scaled_seg_width + scaled_title_offset,
                0
            )
            text_locations.append(title_pt)
            text_contents.append(legend_cfg.title)
            text_sizes.append(scaled_title_height)
        
        # Add value labels
        for i, class_range in enumerate(class_ranges):
            x_mid = (i + 0.5) * scaled_seg_height
            
            label_pt = base_plane.PointAt(
                x_mid,
                scaled_seg_width + scaled_label_offset,
                0
            )
            
            label_text = "{0:.{1}f}-{2:.{1}f}".format(
                class_range['min'], legend_cfg.decimals, class_range['max']
            )
            
            text_locations.append(label_pt)
            text_contents.append(label_text)
            text_sizes.append(scaled_text_height)
    
    # Compute normals
    legend_mesh.FaceNormals.ComputeFaceNormals()
    legend_mesh.Normals.ComputeNormals()
    legend_mesh.UnifyNormals()
    legend_mesh.Compact()
    
    return legend_mesh, text_locations, text_contents, text_sizes


def format_statistics(stats_dict):
    """Format statistics for output."""
    return "Min: {:.2f}\nMax: {:.2f}\nMean: {:.2f}\nMedian: {:.2f}\nValid: {}".format(
        stats_dict['min'],
        stats_dict['max'],
        stats_dict['mean'],
        stats_dict['median'],
        stats_dict['valid_count']
    )


def default_colors():
    """Generate Ladybug-style default gradient."""
    return [
        Color.FromArgb(0, 0, 255),
        Color.FromArgb(0, 255, 255),
        Color.FromArgb(0, 255, 0),
        Color.FromArgb(255, 255, 0),
        Color.FromArgb(255, 128, 0),
        Color.FromArgb(255, 0, 0)
    ]


def is_number(x):
    try:
        float(x)
        return True
    except Exception:
        return False


################
# INPUT HANDLING & VALIDATION
################
input_values = get_input_value(['val', 'Values',])
input_colors = get_input_value(['col', 'ColorGradient'])
input_classes_raw = get_input_value(['cls', 'Classes'])
input_use_linear = get_input_value(['lin', 'UseLinear'])
input_legend_cfg = get_input_value(['leg_cfg', 'Legend Config'])
input_legend_plane = get_input_value(['leg_pln', 'LegendPlane'])

if input_colors is None or len(input_colors) == 0:
    input_colors = default_colors()
if input_classes_raw is None:
    input_classes_raw = 0
if input_use_linear is None:
    input_use_linear = True
if input_legend_plane is None:
    input_legend_plane = rg.Plane.WorldXY

# Detect if classes is int or list of breaks
custom_bins = None
actual_classes = None
if hasattr(input_classes_raw, '__iter__') and not isinstance(input_classes_raw, str):
    custom_bins = sorted([float(x) for x in input_classes_raw if is_number(x)])
    if len(custom_bins) >= 2:
        actual_classes = len(custom_bins) - 1
    else:
        custom_bins = None
        actual_classes = int(input_classes_raw[0]) if len(input_classes_raw) > 0 and is_number(input_classes_raw[0]) else 0
else:
    custom_bins = None
    actual_classes = int(input_classes_raw) if is_number(input_classes_raw) else 0


################
# EXECUTION
################
col = DataTree[object]()
leg_geo = None
txt_loc = []
txt_con = []
txt_siz = []
stats = ""

try:
    is_valid, error_msg, value_count, null_count = validate_inputs(input_values, input_colors)
    
    if not is_valid:
        report(RML.Error, error_msg)
    else:
        log("Processing {} values...".format(value_count))
        
        value_branches = flatten_tree(input_values)
        
        all_values = []
        for _, branch in value_branches:
            for v in branch:
                if v is not None:
                    try:
                        all_values.append(float(v))
                    except (ValueError, TypeError):
                        pass
        
        stats_dict = calculate_statistics(all_values)
        legend_cfg = parse_legend_config(input_legend_cfg)
        
        if legend_cfg.min is None:
            legend_cfg.min = stats_dict['min']
        if legend_cfg.max is None:
            legend_cfg.max = stats_dict['max']
        
        log("Value range: {:.2f} to {:.2f}".format(legend_cfg.min, legend_cfg.max))
        
        # Effective segments calculation
        if custom_bins is not None:
            effective_segments = actual_classes
            log("Using custom bins: {} classes".format(actual_classes))
        elif actual_classes == 0:
            effective_segments = legend_cfg.segments
            log("Continuous mode: {} legend segments".format(effective_segments))
        else:
            effective_segments = _min(actual_classes, legend_cfg.segments)
            log("Auto classification: {} classes, {} legend segments".format(actual_classes, effective_segments))
        
        # Classification and coloring
        processed_count = 0
        
        if custom_bins is not None:
            # Custom breaks mode
            class_ranges = []
            for i in range(len(custom_bins) - 1):
                class_ranges.append({
                    'min': custom_bins[i],
                    'max': custom_bins[i+1],
                    'count': 0
                })
            class_colors = map_colors_to_classes(input_colors, len(class_ranges))
            
            for value_path, value_branch in value_branches:
                for value in value_branch:
                    if value is None or not is_number(value):
                        color = Color.Gray
                    else:
                        try:
                            value_float = float(value)
                            color = Color.Gray
                            for i, r in enumerate(class_ranges):
                                if value_float >= r['min'] and (value_float <= r['max'] if i == len(class_ranges)-1 else value_float < r['max']):
                                    class_ranges[i]['count'] += 1
                                    color = class_colors[i]
                                    processed_count += 1
                                    break
                        except Exception:
                            color = Color.Gray
                    col.Add(color, value_path)
            
            # Legend generation
            if len(class_ranges) > legend_cfg.segments:
                step = float(len(class_ranges)) / legend_cfg.segments
                legend_ranges = []
                legend_colors = []
                for i in range(legend_cfg.segments):
                    start_idx = int(i * step)
                    end_idx = int((i + 1) * step) - 1 if i < legend_cfg.segments - 1 else len(class_ranges) - 1
                    legend_ranges.append({
                        'min': class_ranges[start_idx]['min'],
                        'max': class_ranges[end_idx]['max'],
                        'count': sum(class_ranges[j]['count'] for j in range(start_idx, end_idx + 1))
                    })
                    legend_colors.append(class_colors[start_idx])
            else:
                legend_ranges = class_ranges
                legend_colors = class_colors
            
            leg_geo, txt_loc, txt_con, txt_siz = generate_legend_geometry(
                legend_cfg, legend_ranges, legend_colors, input_legend_plane
            )
        
        elif actual_classes == 0:
            # Continuous mode
            for value_path, value_branch in value_branches:
                for value in value_branch:
                    if value is None:
                        color = Color.Gray
                    else:
                        try:
                            color = get_continuous_color(
                                float(value), legend_cfg.min, legend_cfg.max, input_colors
                            )
                            processed_count += 1
                        except (ValueError, TypeError):
                            color = Color.Gray
                    col.Add(color, value_path)
            
            continuous_ranges = []
            continuous_colors = map_colors_to_classes(input_colors, effective_segments)
            class_size = (legend_cfg.max - legend_cfg.min) / effective_segments
            for i in range(effective_segments):
                continuous_ranges.append({
                    'min': legend_cfg.min + i * class_size,
                    'max': legend_cfg.max if i == effective_segments - 1 else legend_cfg.min + (i + 1) * class_size,
                    'count': 0
                })
            
            leg_geo, txt_loc, txt_con, txt_siz = generate_legend_geometry(
                legend_cfg, continuous_ranges, continuous_colors, input_legend_plane
            )
        
        else:
            # Auto classification mode
            if input_use_linear:
                full_class_ranges = create_linear_classes(legend_cfg.min, legend_cfg.max, actual_classes)
                log("Using linear classification")
            else:
                bounded_values = [v for v in all_values if v >= legend_cfg.min and v <= legend_cfg.max]
                if len(bounded_values) == 0:
                    bounded_values = all_values
                full_class_ranges = create_percentile_classes(bounded_values, actual_classes)
                log("Using percentile classification")
            
            full_class_colors = map_colors_to_classes(input_colors, actual_classes)
            
            for value_path, value_branch in value_branches:
                for value in value_branch:
                    if value is None:
                        color = Color.Gray
                    else:
                        try:
                            value_float = float(value)
                            if math.isnan(value_float) or math.isinf(value_float):
                                color = Color.Gray
                            elif value_float < legend_cfg.min or value_float > legend_cfg.max:
                                color = Color.Gray
                            else:
                                class_idx = find_class_index(value_float, full_class_ranges)
                                full_class_ranges[class_idx]['count'] += 1
                                color = full_class_colors[class_idx]
                                processed_count += 1
                        except (ValueError, TypeError):
                            color = Color.Gray
                    col.Add(color, value_path)
            
            # Legend with capped segments if needed
            if effective_segments < actual_classes:
                step = float(actual_classes) / effective_segments
                legend_ranges = []
                legend_colors = []
                for i in range(effective_segments):
                    start_idx = int(i * step)
                    end_idx = int((i + 1) * step) - 1 if i < effective_segments - 1 else actual_classes - 1
                    legend_ranges.append({
                        'min': full_class_ranges[start_idx]['min'],
                        'max': full_class_ranges[end_idx]['max'],
                        'count': sum(full_class_ranges[j]['count'] for j in range(start_idx, end_idx + 1))
                    })
                    legend_colors.append(full_class_colors[start_idx])
            else:
                legend_ranges = full_class_ranges
                legend_colors = full_class_colors
            
            leg_geo, txt_loc, txt_con, txt_siz = generate_legend_geometry(
                legend_cfg, legend_ranges, legend_colors, input_legend_plane
            )
        
        stats = format_statistics(stats_dict)
        log("Colored {} values | {} legend segments".format(processed_count, effective_segments))

except Exception as e:
    import traceback
    error_trace = traceback.format_exc()
    report(RML.Error, "Unexpected error - see 'out' for details.")
    log("Error: {} ({})\n{}".format(e, type(e).__name__, error_trace))
    col = DataTree[object]()
    leg_geo = None
    txt_loc = []
    txt_con = []
    txt_siz = []
    stats = ""
