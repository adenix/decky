"""
Weather widget using OpenWeatherMap API.
"""

import json
import logging
import os
import urllib.request
from typing import Any, Dict, Optional

from .base import BaseWidget

logger = logging.getLogger(__name__)


class WeatherWidget(BaseWidget):
    """
    Display weather information from OpenWeatherMap.

    Configuration:
        location: City name (required)
        api_key: OpenWeatherMap API key (or use OPENWEATHER_API_KEY env var)
        unit: "fahrenheit" or "celsius" (default: "celsius")
        format: "compact" or "detailed" (default: "compact")

    Example:
        widget:
          type: weather
          location: "San Francisco, CA"
          api_key: "${OPENWEATHER_API_KEY}"
          unit: fahrenheit
          format: compact
    """

    widget_type = "weather"
    update_interval = 600.0  # Update every 10 minutes (API rate limits)

    # Weather condition to emoji mapping
    WEATHER_ICONS = {
        "clear": "☀️",
        "clouds": "☁️",
        "rain": "🌧️",
        "drizzle": "🌦️",
        "thunderstorm": "⛈️",
        "snow": "🌨️",
        "mist": "🌫️",
        "smoke": "🌫️",
        "haze": "🌫️",
        "dust": "🌫️",
        "fog": "🌫️",
        "sand": "🌫️",
        "ash": "🌫️",
        "squall": "💨",
        "tornado": "🌪️",
    }

    def validate_config(self) -> bool:
        """Validate required parameters."""
        if not self.config.get("location"):
            logger.error("Weather widget requires 'location' parameter")
            return False

        # Check for API key in config or environment
        api_key = self.config.get("api_key")

        # Expand environment variable if present
        if api_key and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var)
            if not api_key:
                logger.error(
                    f"Weather widget: environment variable '{env_var}' not set"
                )
                return False

        if not api_key:
            api_key = os.environ.get("OPENWEATHER_API_KEY")

        if not api_key:
            logger.error(
                "Weather widget requires 'api_key' parameter or OPENWEATHER_API_KEY environment variable"
            )
            return False

        self._api_key = api_key
        return True

    def fetch_data(self) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap API."""
        location = self.config.get("location")
        unit_config = self.config.get("unit", "celsius")
        units = "imperial" if unit_config == "fahrenheit" else "metric"

        try:
            # Build API URL
            url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"q={urllib.parse.quote(location)}&appid={self._api_key}&units={units}"
            )

            # Make request with timeout
            timeout = self.config.get("timeout", 5)
            with urllib.request.urlopen(url, timeout=timeout) as response:
                data = json.loads(response.read().decode())

            # Parse response
            return {
                "temp": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["main"].lower(),
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "unit": "°F" if units == "imperial" else "°C",
                "location": data["name"],
            }

        except urllib.error.HTTPError as e:
            logger.error(f"Weather API HTTP error: {e.code} - {e.reason}")
            if e.code == 401:
                logger.error("Invalid API key for OpenWeatherMap")
            elif e.code == 404:
                logger.error(f"Location not found: {location}")
            return self._get_fallback_data()

        except urllib.error.URLError as e:
            logger.error(f"Weather API connection error: {e}")
            return self._get_fallback_data()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from weather API: {e}")
            return self._get_fallback_data()

        except KeyError as e:
            logger.error(f"Unexpected weather API response format (missing key {e})")
            return self._get_fallback_data()

        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}", exc_info=True)
            return self._get_fallback_data()

    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return cached data or fallback values on error."""
        if self._cached_data:
            logger.debug("Using cached weather data")
            return self._cached_data

        unit_config = self.config.get("unit", "celsius")
        return {
            "temp": "--",
            "condition": "unknown",
            "description": "No data",
            "unit": "°F" if unit_config == "fahrenheit" else "°C",
            "location": self.config.get("location", "Unknown"),
        }

    def render_text(self, data: Dict[str, Any]) -> str:
        """Format weather as text."""
        # Get weather icon
        condition = data.get("condition", "unknown")
        icon = self.WEATHER_ICONS.get(condition, "🌡️")

        # Get display format
        format_type = self.config.get("format", "compact")

        # Format temperature
        temp = data["temp"]
        if isinstance(temp, (int, float)):
            temp_str = f"{temp:.0f}{data['unit']}"
        else:
            temp_str = str(temp)

        if format_type == "detailed":
            # Detailed format: icon + temp + description
            description = data.get("description", "").title()
            humidity = data.get("humidity", "")

            if humidity:
                return f"{icon}\n{temp_str}\n{description}\n{humidity}%"
            else:
                return f"{icon}\n{temp_str}\n{description}"

        elif format_type == "minimal":
            # Minimal: just temp
            return f"{icon}\n{temp_str}"

        else:
            # Compact format (default): icon + temp
            location = data.get("location", "")
            if location and len(location) <= 10:
                return f"{icon} {location}\n{temp_str}"
            else:
                return f"{icon}\n{temp_str}"

    def get_required_params(self) -> list:
        """Return required configuration parameters."""
        return ["location"]

