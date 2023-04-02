"""
Get stock prices information.
Wrapper around https://www.alphavantage.co/.
"""
import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from .table import Table


def _get_key() -> str:
    """Get the Alpha Vantage API key."""
    AV_KEY_FILE = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "secrets"
        / "alpha_vantage.key"
    )
    assert (
        AV_KEY_FILE.exists()
    ), f"Alpha Vantage key file does not exist! Make sure to provide a valid key file at '{AV_KEY_FILE}'! A key can be obtained from https://www.alphavantage.co/support/#api-key."
    with AV_KEY_FILE.open("r") as f:
        key = f.read().strip()
    return key


assert _get_key()  # Fail at import time if the key is not present.


def get_weekly_stock_price(symbol: str) -> Table:
    """
    Get stock prices for the given company ticker symbol aggregated weekly. Financial historical prices returned are over a time period of 20+ years.

    Args:
            symbol (str): Company ticker symbol to get stock prices for.

    Returns:
            Table with weekly time series (last trading day of each week, weekly open, weekly high, weekly low, weekly close, weekly volume) of the global equity specified, covering 20+ years of historical data.
    """
    api_key = _get_key()
    url = "https://www.alphavantage.co/query"
    params = {
        "symbol": symbol,
        "apikey": api_key,
        "function": "TIME_SERIES_WEEKLY",
        "outputsize": "full",
        "datatype": "csv",
    }
    resp = requests.get(url, params=params)
    dateparse = lambda x: datetime.strptime(x, "%Y-%m-%d")
    with io.StringIO(resp.text) as f:
        return Table(pd.read_csv(f, parse_dates=["timestamp"], date_parser=dateparse))
