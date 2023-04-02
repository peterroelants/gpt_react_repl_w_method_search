"""
Location API wrapping around:
- Open-Meteo's geocoding API: https://open-meteo.com/en/docs/geocoding-api
- geocoder: https://geocoder.readthedocs.io/
"""
import geocoder
import requests

from react_repl_agent.utils.exceptions import SelfDescriptiveError


class LocationNameError(ValueError, SelfDescriptiveError):
    """Location name error."""


def _parse_location_result(location_dct: dict) -> dict:
    """
    Parse a location result returned by the geocoding API.

    https://open-meteo.com/en/docs/geocoding-api
    """
    # TODO: feature_code lookup: https://www.geonames.org/export/codes.html
    # http://download.geonames.org/export/dump/featureCodes_en.txt
    params_to_select = set(
        ["name", "latitude", "longitude", "timezone", "feature_code", "population"]
    )
    administrative_zones = ", ".join(
        location_dct[k]
        for k in ["admin4", "admin3", "admin2", "admin1"]
        if k in location_dct
    ).strip()
    country_w_code = (
        f"{location_dct['country']} ({location_dct['country_code']})".strip()
    )
    return_dct = {k: v for k, v in location_dct.items() if k in params_to_select}
    return_dct["country"] = country_w_code
    return_dct["administrative_zones"] = administrative_zones
    return return_dct


def search_location_geocoordinates(location_name: str) -> list:
    """
    Return a list of geo-locations (latitude and longitude) for locations matching the given location name.

    Args:
            location_name (str): Location name to search for. An empty string or only 1 character will return an empty result. 2 characters will only match exact matching locations. 3 and more characters will perform fuzzy matching. The search string can be a location name or a postal code.

    Returns:
            List of locations with geographical coordinates (latitude and longitude) where the name matches the given location_name.
    """
    url_endpoint = "https://geocoding-api.open-meteo.com/v1/search"
    params: dict[str, str | int] = {
        "name": location_name,
        "count": 5,
        "format": "json",
        "language": "en",
    }
    resp = requests.get(url_endpoint, params=params)
    results_dct = resp.json()
    if "results" in results_dct:
        return [_parse_location_result(r) for r in results_dct["results"]]
    else:
        raise LocationNameError(
            f"No results found. for '{location_name}'. Simplify the search string!"
        )


def get_user_location() -> dict:
    """
    Return the user's current location.

    Returns:
        The current location of the user's device running this code.
    """
    geo = geocoder.ip("me")
    return {
        "address": geo.address,
        "latitude": geo.lat,
        "longitude": geo.lng,
    }
