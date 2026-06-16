"""Pure color-space conversion and gradient utilities for CRC_ColorCalculator.

The legacy ColorCalculator works with ARGB integer tuples (0-255 range) for
color interchange and internally uses a linear gradient interpolation model.
All functions here are pure Python — no Rhino, no GH, no DB.

Color representation: (R, G, B) or (A, R, G, B) as integers 0-255.
Gradient position t: float in [0.0, 1.0].
"""

import math


# ---------------------------------------------------------------------------
# Color-space conversions
# ---------------------------------------------------------------------------

def rgb_to_hsv(r: int, g: int, b: int) -> tuple:
    """Convert RGB (0-255 ints) to HSV.

    Returns (h, s, v) where:
        h in [0.0, 360.0)  — hue in degrees
        s in [0.0, 1.0]    — saturation
        v in [0.0, 1.0]    — value (brightness)
    """
    r_f = r / 255.0
    g_f = g / 255.0
    b_f = b / 255.0

    cmax = max(r_f, g_f, b_f)
    cmin = min(r_f, g_f, b_f)
    delta = cmax - cmin

    # Value
    v = cmax

    # Saturation
    if cmax == 0.0:
        s = 0.0
    else:
        s = delta / cmax

    # Hue
    if delta == 0.0:
        h = 0.0
    elif cmax == r_f:
        h = 60.0 * (((g_f - b_f) / delta) % 6)
    elif cmax == g_f:
        h = 60.0 * (((b_f - r_f) / delta) + 2)
    else:
        h = 60.0 * (((r_f - g_f) / delta) + 4)

    if h < 0:
        h += 360.0

    return (h, s, v)


def hsv_to_rgb(h: float, s: float, v: float) -> tuple:
    """Convert HSV to RGB (0-255 ints).

    Args:
        h: hue in degrees [0.0, 360.0)
        s: saturation [0.0, 1.0]
        v: value [0.0, 1.0]

    Returns (r, g, b) as integers 0-255.
    """
    if s == 0.0:
        val = int(round(v * 255))
        return (val, val, val)

    h = h % 360.0
    hi = int(math.floor(h / 60.0)) % 6
    f = (h / 60.0) - math.floor(h / 60.0)

    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    if hi == 0:
        r_f, g_f, b_f = v, t, p
    elif hi == 1:
        r_f, g_f, b_f = q, v, p
    elif hi == 2:
        r_f, g_f, b_f = p, v, t
    elif hi == 3:
        r_f, g_f, b_f = p, q, v
    elif hi == 4:
        r_f, g_f, b_f = t, p, v
    else:
        r_f, g_f, b_f = v, p, q

    return (
        max(0, min(255, int(round(r_f * 255)))),
        max(0, min(255, int(round(g_f * 255)))),
        max(0, min(255, int(round(b_f * 255)))),
    )


# ---------------------------------------------------------------------------
# Gradient interpolation (core of ColorCalculator)
# ---------------------------------------------------------------------------

def interpolate_color_argb(color_list: list, t: float) -> tuple:
    """Interpolate between ARGB tuples in color_list at position t in [0,1].

    Each color in color_list must be a tuple (A, R, G, B) with integer values
    0-255. Returns an interpolated (A, R, G, B) tuple.
    """
    if not color_list:
        return (255, 128, 128, 128)

    t = max(0.0, min(1.0, t))

    if len(color_list) == 1:
        return tuple(color_list[0])

    scaled = t * (len(color_list) - 1)
    i1 = int(math.floor(scaled))
    i2 = int(math.ceil(scaled))
    i1 = max(0, min(len(color_list) - 1, i1))
    i2 = max(0, min(len(color_list) - 1, i2))

    if i1 == i2:
        return tuple(color_list[i1])

    local_t = scaled - i1
    c1 = color_list[i1]
    c2 = color_list[i2]

    return tuple(
        max(0, min(255, int(round(c1[ch] + (c2[ch] - c1[ch]) * local_t))))
        for ch in range(len(c1))
    )


def interpolate_color_rgb(color_list: list, t: float) -> tuple:
    """Interpolate between RGB tuples in color_list at position t in [0,1].

    Each color must be a tuple (R, G, B) with integer values 0-255.
    Returns an interpolated (R, G, B) tuple.
    """
    argb_list = [(255,) + tuple(c) for c in color_list]
    result = interpolate_color_argb(argb_list, t)
    return result[1:]  # strip alpha


def value_to_color(value: float, min_val: float, max_val: float,
                   color_list: list) -> tuple:
    """Map a scalar value to an ARGB color via linear gradient.

    Args:
        value:      the numeric value to map
        min_val:    minimum of the data range
        max_val:    maximum of the data range
        color_list: list of (A,R,G,B) or (R,G,B) tuples defining the gradient

    Returns an (A, R, G, B) tuple. Falls back to gray (255,128,128,128) on NaN/inf.
    """
    try:
        if math.isnan(float(value)) or math.isinf(float(value)):
            return (255, 128, 128, 128)
    except (TypeError, ValueError):
        return (255, 128, 128, 128)

    value_range = max_val - min_val
    if value_range < 1e-10:
        t = 0.0
    else:
        t = (float(value) - min_val) / value_range

    # Normalize color tuples to ARGB
    if color_list and len(color_list[0]) == 3:
        argb_list = [(255,) + tuple(c) for c in color_list]
    else:
        argb_list = [tuple(c) for c in color_list]

    return interpolate_color_argb(argb_list, t)


def default_gradient_argb() -> list:
    """Return the default Ladybug-style 6-stop ARGB gradient used by ColorCalculator."""
    return [
        (255, 0,   0,   255),   # blue
        (255, 0,   255, 255),   # cyan
        (255, 0,   255, 0),     # green
        (255, 255, 255, 0),     # yellow
        (255, 255, 128, 0),     # orange
        (255, 255, 0,   0),     # red
    ]


def map_values_to_classes(values: list, num_classes: int,
                          min_val: float = None, max_val: float = None,
                          linear: bool = True) -> list:
    """Assign each value to a class index (0-based).

    Args:
        values:     flat list of floats
        num_classes: number of discrete classes
        min_val:    override minimum (defaults to data min)
        max_val:    override maximum (defaults to data max)
        linear:     True = equal-width bins; False = percentile bins

    Returns a list of integers (class indices), one per value.
    Same length as values; None values map to -1.
    """
    valid = [v for v in values if v is not None and not math.isnan(float(v))]
    if not valid or num_classes < 1:
        return [-1] * len(values)

    lo = min_val if min_val is not None else min(valid)
    hi = max_val if max_val is not None else max(valid)

    if linear:
        width = (hi - lo) / num_classes if (hi - lo) > 1e-10 else 1.0
        result = []
        for v in values:
            if v is None:
                result.append(-1)
                continue
            try:
                fv = float(v)
                if math.isnan(fv) or math.isinf(fv):
                    result.append(-1)
                else:
                    idx = int((fv - lo) / width)
                    result.append(max(0, min(num_classes - 1, idx)))
            except (TypeError, ValueError):
                result.append(-1)
        return result
    else:
        # Percentile bins
        sorted_valid = sorted(valid)
        n = len(sorted_valid)
        result = []
        for v in values:
            if v is None:
                result.append(-1)
                continue
            try:
                fv = float(v)
                if math.isnan(fv) or math.isinf(fv):
                    result.append(-1)
                else:
                    # find rank position
                    rank = sum(1 for x in sorted_valid if x <= fv)
                    idx = int((rank / n) * num_classes)
                    result.append(max(0, min(num_classes - 1, idx)))
            except (TypeError, ValueError):
                result.append(-1)
        return result


# ---------------------------------------------------------------------------
# Legend config
# ---------------------------------------------------------------------------

class LegendConfig(object):
    """Holds parsed legend display parameters."""
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


def parse_legend_config(config_text) -> LegendConfig:
    """Parse a multiline 'key: value' string into a LegendConfig.

    Supported keys (case-insensitive):
        title, title_size / titlesize, title_offset / titleoffset,
        label_offset / labeloffset, min, max, segments / segment_count / seg_count,
        decimals / decimal_places, vertical, seg_height / segment_height,
        seg_width / segment_width, text_height, scale.

    Bad/blank lines are silently ignored. Parse errors print a warning.
    Returns a LegendConfig with defaults for any key not supplied.
    """
    cfg = LegendConfig()
    if not config_text:
        return cfg
    try:
        text = str(config_text).strip()
        for line in text.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, val = line.split(':', 1)
            key = key.strip().lower()
            val = val.strip()
            if key == 'title':
                cfg.title = val
            elif key in ('title_size', 'titlesize'):
                cfg.title_size = max(0.1, float(val))
            elif key in ('title_offset', 'titleoffset'):
                cfg.title_offset = max(0.0, float(val))
            elif key in ('label_offset', 'labeloffset'):
                cfg.label_offset = max(0.0, float(val))
            elif key == 'min':
                cfg.min = float(val)
            elif key == 'max':
                cfg.max = float(val)
            elif key in ('segments', 'segment_count', 'seg_count'):
                cfg.segments = max(2, int(val))
            elif key in ('decimals', 'decimal_places'):
                cfg.decimals = max(0, int(val))
            elif key == 'vertical':
                cfg.vertical = val.lower() in ('true', 'yes', '1', 't', 'y')
            elif key in ('seg_height', 'segment_height'):
                cfg.seg_height = max(0.1, float(val))
            elif key in ('seg_width', 'segment_width'):
                cfg.seg_width = max(0.1, float(val))
            elif key == 'text_height':
                cfg.text_height = max(0.1, float(val))
            elif key == 'scale':
                cfg.scale = max(0.1, float(val))
    except Exception as _e:
        print("Warning: legend config parse error: {}".format(_e))
    return cfg


# ---------------------------------------------------------------------------
# Core color-assignment logic
# ---------------------------------------------------------------------------

def _is_number(x):
    try:
        float(x)
        return True
    except Exception:
        return False


def compute_color_assignment(values_flat, gradient_argb, cls_raw, linear, cfg):
    """Map a flat list of raw items to per-value ARGB tuples.

    Args:
        values_flat:   flat list of raw values (may include None or non-numeric).
        gradient_argb: list of (A,R,G,B) tuples defining the gradient.
        cls_raw:       raw cls input as a list — either [0] (continuous),
                       [n] (fixed n classes), or [f1, f2, ...] (custom breakpoints).
        linear:        True = equal-width bins; False = percentile bins.
        cfg:           LegendConfig (mutated: cfg.min and cfg.max are updated
                       to the effective lo/hi used for the assignment).

    Returns:
        (argb_per_value, leg_ranges, leg_colors_argb)

        argb_per_value  : list[tuple|None] — parallel to values_flat.
                          None means invalid/NaN/inf/out-of-range → GH layer paints Gray.
        leg_ranges      : list of dicts {'min': float, 'max': float}
        leg_colors_argb : list of (A,R,G,B) tuples, one per legend segment.

    Raises:
        ValueError if values_flat has no valid numeric entries.
    """
    # Parse cls_raw into mode
    custom_bins = None
    actual_classes = 0
    if len(cls_raw) > 1:
        numeric = [float(x) for x in cls_raw if _is_number(x)]
        if len(numeric) >= 2:
            custom_bins = sorted(numeric)
            actual_classes = len(custom_bins) - 1
        else:
            actual_classes = int(cls_raw[0]) if _is_number(cls_raw[0]) else 0
    else:
        v0 = cls_raw[0] if cls_raw else 0
        actual_classes = int(v0) if _is_number(v0) else 0

    # Collect valid floats
    all_numeric = []
    for item in values_flat:
        if item is not None and _is_number(item):
            fv = float(item)
            if not math.isnan(fv) and not math.isinf(fv):
                all_numeric.append(fv)

    if not all_numeric:
        raise ValueError("No valid numeric values")

    lo = cfg.min if cfg.min is not None else min(all_numeric)
    hi = cfg.max if cfg.max is not None else max(all_numeric)
    cfg.min = lo
    cfg.max = hi

    argb_per_value = []

    if custom_bins is not None:
        # --- Custom breakpoints mode ---
        cr_list = [{'min': custom_bins[i], 'max': custom_bins[i + 1]}
                   for i in range(len(custom_bins) - 1)]
        cc_list = []
        for i in range(len(cr_list)):
            t = 0.0 if len(cr_list) == 1 else float(i) / (len(cr_list) - 1)
            cc_list.append(interpolate_color_argb(gradient_argb, t))

        for item in values_flat:
            if item is None or not _is_number(item):
                argb_per_value.append(None)
            else:
                fv = float(item)
                assigned = None
                for i, cr in enumerate(cr_list):
                    if i == len(cr_list) - 1:
                        if fv >= cr['min'] and fv <= cr['max']:
                            assigned = cc_list[i]
                            break
                    else:
                        if fv >= cr['min'] and fv < cr['max']:
                            assigned = cc_list[i]
                            break
                argb_per_value.append(assigned)  # None = out of all bins → Gray

        eff_segs = min(len(cr_list), cfg.segments)
        step = float(len(cr_list)) / eff_segs
        leg_ranges = []
        leg_colors_argb = []
        for i in range(eff_segs):
            si = int(i * step)
            ei = int((i + 1) * step) - 1 if i < eff_segs - 1 else len(cr_list) - 1
            leg_ranges.append({'min': cr_list[si]['min'], 'max': cr_list[ei]['max']})
            leg_colors_argb.append(cc_list[si])

    elif actual_classes == 0:
        # --- Continuous mode ---
        vr = hi - lo
        for item in values_flat:
            if item is None or not _is_number(item):
                argb_per_value.append(None)
            else:
                fv = float(item)
                t = 0.0 if vr < 1e-10 else max(0.0, min(1.0, (fv - lo) / vr))
                argb_per_value.append(interpolate_color_argb(gradient_argb, t))

        eff_segs = cfg.segments
        sw = (hi - lo) / eff_segs if eff_segs > 0 else 1.0
        leg_ranges = [{'min': lo + i * sw, 'max': lo + (i + 1) * sw}
                      for i in range(eff_segs)]
        if leg_ranges:
            leg_ranges[-1]['max'] = hi
        leg_t = [float(i) / (eff_segs - 1) if eff_segs > 1 else 0.0
                 for i in range(eff_segs)]
        leg_colors_argb = [interpolate_color_argb(gradient_argb, t) for t in leg_t]

    else:
        # --- Fixed-class mode ---
        if linear:
            cw = (hi - lo) / actual_classes if (hi - lo) > 1e-10 else 1.0
            full_cr = [{'min': lo + i * cw,
                        'max': hi if i == actual_classes - 1 else lo + (i + 1) * cw}
                       for i in range(actual_classes)]
        else:
            sv = sorted(all_numeric)
            n = len(sv)
            full_cr = []
            pc = n // actual_classes
            for i in range(actual_classes):
                st = i * pc
                en = n - 1 if i == actual_classes - 1 else (i + 1) * pc - 1
                full_cr.append({'min': sv[st], 'max': sv[en]})

        full_cc = []
        for i in range(actual_classes):
            t = 0.0 if actual_classes == 1 else float(i) / (actual_classes - 1)
            full_cc.append(interpolate_color_argb(gradient_argb, t))

        for item in values_flat:
            if item is None or not _is_number(item):
                argb_per_value.append(None)
            else:
                fv = float(item)
                if math.isnan(fv) or math.isinf(fv) or fv < lo or fv > hi:
                    argb_per_value.append(None)
                else:
                    idx = 0
                    for i, cr in enumerate(full_cr):
                        if i == len(full_cr) - 1:
                            if fv >= cr['min'] and fv <= cr['max']:
                                idx = i
                                break
                        else:
                            if fv >= cr['min'] and fv < cr['max']:
                                idx = i
                                break
                    argb_per_value.append(full_cc[idx])

        eff_segs = min(actual_classes, cfg.segments)
        if eff_segs < actual_classes:
            step = float(actual_classes) / eff_segs
            leg_ranges = []
            leg_colors_argb = []
            for i in range(eff_segs):
                si = int(i * step)
                ei = int((i + 1) * step) - 1 if i < eff_segs - 1 else actual_classes - 1
                leg_ranges.append({'min': full_cr[si]['min'], 'max': full_cr[ei]['max']})
                leg_colors_argb.append(full_cc[si])
        else:
            leg_ranges = full_cr
            leg_colors_argb = full_cc

    return argb_per_value, leg_ranges, leg_colors_argb


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_statistics(valid_vals) -> str:
    """Return a formatted statistics string for a list of valid numeric values.

    Args:
        valid_vals: non-empty list of floats (must already be filtered for NaN/inf).

    Returns:
        Multi-line string: "Min: {:.2f}\\nMax: {:.2f}\\nMean: {:.2f}\\nMedian: {:.2f}\\nValid: {}"
    """
    sv = sorted(valid_vals)
    n = len(sv)
    mean_val = sum(sv) / n
    median_val = sv[n // 2]
    return "Min: {:.2f}\nMax: {:.2f}\nMean: {:.2f}\nMedian: {:.2f}\nValid: {}".format(
        sv[0], sv[-1], mean_val, median_val, n
    )


# ---------------------------------------------------------------------------
# Legend layout (pure math — no Rhino)
# ---------------------------------------------------------------------------

def legend_layout(cfg, leg_ranges, leg_colors_argb) -> dict:
    """Compute legend layout as pure local (x, y) coordinates.

    Returns a dict with:
        'segment_quads'  : list of 4-tuples of (x,y) pairs — one quad per segment.
                           Vertical: bottom-left, bottom-right, top-right, top-left.
                           Horizontal: bottom-left, bottom-right, top-right, top-left.
        'segment_argb'   : list of (A,R,G,B) tuples, one per segment.
        'labels'         : list of (x, y, text, size) tuples.
                           Title (if set) comes first.

    All coordinates are in the legend's local 2-D space. The GH component
    maps them to 3-D via base_plane.PointAt(x, y, 0).

    No Rhino imports. No rg.Mesh. No base_plane.PointAt here.
    """
    sh = cfg.seg_height * cfg.scale
    sw = cfg.seg_width * cfg.scale
    th = cfg.text_height * cfg.scale
    tith = th * cfg.title_size
    titoff = cfg.title_offset * sh
    laboff = cfg.label_offset * sh

    n = len(leg_ranges)
    segment_quads = []
    labels = []

    if cfg.vertical:
        for i in range(n):
            y0 = i * sh
            y1 = (i + 1) * sh
            # (bottom-left, bottom-right, top-right, top-left)
            segment_quads.append(((0, y0), (sw, y0), (sw, y1), (0, y1)))

        if cfg.title:
            labels.append((0, n * sh + titoff, cfg.title, tith))

        for i, cr in enumerate(leg_ranges):
            label_text = "{0:.{2}f} - {1:.{2}f}".format(
                cr['min'], cr['max'], cfg.decimals)
            labels.append((sw + laboff, (i + 0.5) * sh, label_text, th))

    else:
        for i in range(n):
            x0 = i * sh
            x1 = (i + 1) * sh
            # (bottom-left, bottom-right, top-right, top-left)
            segment_quads.append(((x0, 0), (x1, 0), (x1, sw), (x0, sw)))

        if cfg.title:
            labels.append((0, sw + titoff, cfg.title, tith))

        for i, cr in enumerate(leg_ranges):
            label_text = "{0:.{1}f}-{2:.{1}f}".format(
                cr['min'], cfg.decimals, cr['max'])
            labels.append(((i + 0.5) * sh, sw + laboff, label_text, th))

    return {
        'segment_quads': segment_quads,
        'segment_argb': list(leg_colors_argb),
        'labels': labels,
    }
