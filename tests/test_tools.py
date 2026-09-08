"""Unit tests for the lab's tool logic (plain functions behind the tools)."""

from agents_lab.tools import add, get_weather


def test_add():
    assert add(2, 3) == 5
    assert add(-1.5, 2.5) == 1.0


def test_get_weather_known_city():
    assert "clear" in get_weather("Tokyo")
    # Lookup is case/whitespace-insensitive.
    assert "clear" in get_weather("  tokyo ")


def test_get_weather_unknown_city():
    assert "No forecast" in get_weather("Atlantis")
