import pytest
from crc_modules.utils.sql_composer import compose


def test_compose_happy_path():
    template = "SELECT * FROM #TABLE#"
    replacements = {"#TABLE#": "buildings"}
    result = compose(template, replacements)
    assert result == "SELECT * FROM buildings"


def test_compose_multiple_replacements():
    template = "SELECT * FROM #SCHEMA#.#TABLE# WHERE #COL# = #VAL#"
    replacements = {
        "#SCHEMA#": "public",
        "#TABLE#": "buildings",
        "#COL#": "id",
        "#VAL#": "1"
    }
    result = compose(template, replacements)
    assert result == "SELECT * FROM public.buildings WHERE id = 1"


def test_compose_unmatched_placeholder():
    template = "SELECT * FROM #TABLE# WHERE #COL# = #VAL#"
    replacements = {"#TABLE#": "buildings", "#COL#": "id"}
    result = compose(template, replacements)
    assert result == "SELECT * FROM buildings WHERE id = #VAL#"


def test_compose_empty_template_raises():
    with pytest.raises(ValueError, match="Template cannot be empty"):
        compose("", {"#TABLE#": "buildings"})

    with pytest.raises(ValueError, match="Template cannot be empty"):
        compose("   ", {"#TABLE#": "buildings"})


def test_compose_empty_replacements():
    template = "SELECT * FROM #TABLE#"
    replacements = {}
    result = compose(template, replacements)
    assert result == template


def test_compose_replacements_applied_in_sequence():
    template = "#A# #B# #C#"
    replacements = {"#A#": "1", "#B#": "2", "#C#": "3"}
    result = compose(template, replacements)
    assert result == "1 2 3"


def test_compose_with_special_characters():
    template = "SELECT * FROM #TABLE# WHERE name = '#NAME#'"
    replacements = {"#TABLE#": "users", "#NAME#": "O'Reilly"}
    result = compose(template, replacements)
    assert result == "SELECT * FROM users WHERE name = 'O'Reilly'"