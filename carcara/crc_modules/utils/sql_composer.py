def compose(template: str, replacements: dict[str, str]) -> str:
    """
    Replace each key in `replacements` with its value inside `template`
    using plain str.replace(). No quoting, no escaping — the caller
    chooses placeholder tokens and is responsible for safe values.
    Raises ValueError if `template` is empty.
    Returns the final SQL statement string.
    """
    if not template or not template.strip():
        raise ValueError("Template cannot be empty")

    statement = template
    for placeholder, replacement in replacements.items():
        statement = statement.replace(str(placeholder), str(replacement))

    return statement