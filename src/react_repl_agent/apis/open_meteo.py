"""
Weather API

Wrapping around Open-Meteo: https://open-meteo.com/
"""
import requests
from timezonefinder import TimezoneFinder


def _lookup_weather_code(weather_code: int) -> str:
    # Codes based on https://open-meteo.com/en/docs , asked ChatGPT to convert the table to a python dict
    # TODO: look at other tables of codes: https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    ww_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Drizzle: Light intensity",
        53: "Drizzle: Moderate intensity",
        55: "Drizzle: Dense intensity",
        56: "Freezing Drizzle: Light intensity",
        57: "Freezing Drizzle: Dense intensity",
        61: "Rain: Slight intensity",
        63: "Rain: Moderate intensity",
        65: "Rain: Heavy intensity",
        66: "Freezing Rain: Light intensity",
        67: "Freezing Rain: Heavy intensity",
        71: "Snow fall: Slight intensity",
        73: "Snow fall: Moderate intensity",
        75: "Snow fall: Heavy intensity",
        77: "Snow grains",
        80: "Rain showers: Slight intensity",
        81: "Rain showers: Moderate intensity",
        82: "Rain showers: Violent intensity",
        85: "Snow showers: Slight intensity",
        86: "Snow showers: Heavy intensity",
        95: "Thunderstorm: Slight or moderate",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return ww_codes.get(weather_code, f"WMO code: {weather_code}")


def _parse_weather_result(result_dct: dict):
    timezone = (
        f"{result_dct['timezone']} [{result_dct['timezone_abbreviation']}]".strip()
    )
    del result_dct["timezone"]
    del result_dct["timezone_abbreviation"]
    result_dct["timezone"] = timezone
    del result_dct["generationtime_ms"]
    del result_dct["utc_offset_seconds"]
    # Parse weathercode
    weathercode = result_dct["current_weather"]["weathercode"]
    del result_dct["current_weather"]["weathercode"]
    result_dct["current_weather"]["description"] = _lookup_weather_code(weathercode)
    # Add units
    result_dct["temperature_unit"] = "celsius"
    result_dct["windspeed_unit"] = "kmh"
    result_dct["winddirection_unit"] = "degrees"


def get_current_weather(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Get the current weather for the given location (geographical coordinates).

    Args:
            latitude (float): Geographical WGS84 latitude of the location
            longitude (float): Geographical WGS84 longitude of the location

    Returns:
            Return current weather (temperature and wind) at the given location.
    """
    # https://open-meteo.com/en/docs
    url_endpoint = "https://api.open-meteo.com/v1/forecast"
    params: dict[str, str | float | int | bool] = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "past_days": 0,
        "temperature_unit": "celsius",
        "windspeed_unit": "kmh",
    }
    resp = requests.get(url_endpoint, params=params)
    result_dct = resp.json()
    _parse_weather_result(result_dct)
    return result_dct


def _geo_coordinates_to_timezone(latitude: float, longitude: float) -> str:
    # https://github.com/jannikmi/timezonefinder
    time_zone = TimezoneFinder().timezone_at(lng=longitude, lat=latitude)
    assert time_zone
    return time_zone


def _parse_daily_forecast_result(result_dct: dict):
    timezone = (
        f"{result_dct['timezone']} [{result_dct['timezone_abbreviation']}]".strip()
    )
    del result_dct["timezone"]
    del result_dct["timezone_abbreviation"]
    result_dct["timezone"] = timezone
    del result_dct["generationtime_ms"]
    del result_dct["utc_offset_seconds"]
    del result_dct["elevation"]
    # Parse weathercodes
    result_dct["daily"]["description"] = [
        _lookup_weather_code(wc) for wc in result_dct["daily"]["weathercode"]
    ]


def get_daily_weather_forecast(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Get the daily weather forecast for the next 7 days for the given location (geographical coordinates).

    Args:
            latitude (float): Geographical WGS84 latitude of the location
            longitude (float): Geographical WGS84 longitude of the location

    Returns:
            Daily weather forecast for the given location.
    """
    # https://open-meteo.com/en/docs
    url_endpoint = "https://api.open-meteo.com/v1/forecast"
    timezone = _geo_coordinates_to_timezone(latitude=latitude, longitude=longitude)
    params: dict[str, str | int | float | bool | list[str]] = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": False,
        "models": "best_match",
        "past_days": 0,
        "daily": [
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ],
        "temperature_unit": "celsius",
        "windspeed_unit": "kmh",
        "timezone": timezone,
    }
    resp = requests.get(url_endpoint, params=params)
    result_dct = resp.json()
    _parse_daily_forecast_result(result_dct)
    return result_dct
