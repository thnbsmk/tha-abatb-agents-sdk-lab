"""Example tools used by the lab agents.

The business logic lives in plain, directly-testable Python functions. Each is
wrapped with ``function_tool`` to produce the ``FunctionTool`` objects the Agents
SDK exposes to a model (the tool name is taken from the function name, e.g.
``add`` and ``get_weather``).
"""

from __future__ import annotations

from agents import function_tool

# A tiny in-memory "weather service" so the tool is deterministic and offline.
_FAKE_WEATHER: dict[str, str] = {
    "london": "16C and rainy",
    "san francisco": "19C and foggy",
    "tokyo": "24C and clear",
}


def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the product."""
    return a * b


def get_weather(city: str) -> str:
    """Return a short weather report for the given city."""
    return _FAKE_WEATHER.get(city.strip().lower(), f"No forecast available for {city}.")


add_tool = function_tool(add)
multiply_tool = function_tool(multiply)
get_weather_tool = function_tool(get_weather)
