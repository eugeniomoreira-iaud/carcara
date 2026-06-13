import re


def validate_offset(value: str) -> str:
    """Return value unchanged if numeric literal (text). Raise ValueError otherwise. '0' = no shift."""
    if not re.match(r'^-?\d+(\.\d+)?$', value):
        raise ValueError(f"Invalid offset: {value}")
    return value


def translate_expr(geom_sql: str, cx: str, cy: str, direction: str) -> str:
    """Wrap SQL geometry expression in ST_Translate.
    direction='to_local'     -> ST_Translate(<geom_sql>, -cx, -cy)   (read)
    direction='to_projected' -> ST_Translate(<geom_sql>,  cx,  cy)   (write / filter)
    cx, cy are validated numeric text, embedded verbatim."""
    cx = validate_offset(cx)
    cy = validate_offset(cy)
    if direction == "to_local":
        return f"ST_Translate({geom_sql}, -{cx}, -{cy})"
    elif direction == "to_projected":
        return f"ST_Translate({geom_sql}, {cx}, {cy})"
    raise ValueError(f"Unknown direction: {direction}")