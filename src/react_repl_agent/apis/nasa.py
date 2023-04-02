"""
NASA API module

More info:
- https://api.nasa.gov/
"""
from pathlib import Path

import requests


def _get_key() -> str:
    """Get the NASA API key."""
    NASA_KEY_FILE = (
        Path(__file__).resolve().parent.parent.parent.parent / "secrets" / "nasa.key"
    )
    assert (
        NASA_KEY_FILE.exists()
    ), f"NASA API key file does not exist! Make sure to provide a valid key file at '{NASA_KEY_FILE}'! A key can be obtained from https://api.nasa.gov/."
    with NASA_KEY_FILE.open("r") as f:
        key = f.read().strip()
    return key


assert _get_key()  # Fail at import time if the key is not present.


def get_nasa_astronomy_picture_of_the_day() -> dict:
    """
    Get the NASA Astronomy Picture of the Day (APOD).

    Returns:
            Dictionary containing the APOD information such as title, image URL and more information.
    """
    # https://api.nasa.gov/
    url_endpoint = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": _get_key()}
    resp = requests.get(url_endpoint, params=params)
    result_dct = resp.json()
    return result_dct
