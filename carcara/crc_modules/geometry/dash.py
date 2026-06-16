"""Dash pattern parsing for CRC_CurveDisplay.

Pure Python — no Rhino imports. Mirrors the C# ParseDashPattern logic exactly.

Empty-fragment handling: splitting on single space char matches C#'s
`pattern.Split(new char[] { ' ' })` which DOES produce empty strings on multiple
consecutive spaces. We skip empty fragments (matching .NET Split with
StringSplitOptions.RemoveEmptyEntries behaviour for robustness), which is a safe
simplification: a double-space in the panel is a user typo, not a 0-length segment.
"""

from __future__ import annotations


def parse_dash_pattern(text) -> list[float] | None:
    """Parse a space-separated dash pattern string into a list of floats.

    Mirrors C# ``ParseDashPattern``, with one superset extension:
    - ``None``, empty string, or whitespace-only → return ``None``
    - Split on commas AND any whitespace, so both the CurveDisplay syntax
      (``"5 5"``) and the SVG ``stroke-dasharray`` syntax (``"5,5"`` / ``"5, 5"``)
      parse identically. Empty fragments are dropped (consecutive separators
      treated as one). Commas were never valid before, so this is backward-compatible.
    - Non-numeric fragment → ``ValueError("<frag> is not a valid number.")``
    - Value <= 0 → ``ValueError("Dashes or gaps must have a strictly positive length.")``
    - Returns ``list[float]`` on success.
    """
    if text is None:
        return None
    text = str(text)
    if not text.strip():
        return None

    # Split on commas or any run of whitespace; empties dropped by str.split().
    fragments = text.replace(",", " ").split()
    if not fragments:
        return None

    values: list[float] = []
    for fragment in fragments:
        try:
            v = float(fragment)
        except (ValueError, TypeError):
            raise ValueError(f"{fragment} is not a valid number.")
        if v <= 0.0:
            raise ValueError("Dashes or gaps must have a strictly positive length.")
        values.append(v)

    return values
