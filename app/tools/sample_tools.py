"""Sample tools for the demo agents."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city (mock data).

    Args:
        city: The city name to get weather for.
    """
    weather_data: dict[str, dict[str, str | int]] = {
        "berlin": {"temp": 18, "condition": "Partly Cloudy", "humidity": 65},
        "new york": {"temp": 22, "condition": "Sunny", "humidity": 45},
        "tokyo": {"temp": 26, "condition": "Rainy", "humidity": 80},
        "london": {"temp": 15, "condition": "Overcast", "humidity": 75},
        "paris": {"temp": 20, "condition": "Clear", "humidity": 55},
    }

    data = weather_data.get(city.lower(), {"temp": 20, "condition": "Unknown", "humidity": 50})
    return f"Weather in {city}: {data['temp']}°C, {data['condition']}, Humidity: {data['humidity']}%"


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A math expression like '2 + 3 * 4' or 'sqrt(16)'.
    """
    allowed_names = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "abs": abs,
        "round": round,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return f"Result: {result}"
    except Exception as exc:
        return f"Error evaluating '{expression}': {exc}"


@tool
def get_current_time() -> str:
    """Get the current UTC date and time."""
    now = datetime.now(tz=timezone.utc)
    return f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}"


all_tools = [get_weather, calculate, get_current_time]
