"""Function tools used by the lab agents.

Each tool is a plain Python function decorated with ``@function_tool`` from the
Agents SDK, so it can be registered on an ``Agent`` and invoked by a model.
"""

from __future__ import annotations

from agents import function_tool

_WEATHER = {
    "san francisco": "18°C and foggy",
    "tokyo": "24°C and clear",
    "london": "12°C and rainy",
}


@function_tool
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the product."""
    return a * b


@function_tool
def get_weather(city: str) -> str:
    """Return a short weather report for a known city."""
    return _WEATHER.get(city.strip().lower(), f"No weather data for {city!r}.")
