"""Functions for interacting with external cryptocurrency APIs."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import requests

COINGECKO_API = "https://api.coingecko.com/api/v3"


class CoinGeckoError(RuntimeError):
    """Raised when the CoinGecko API returns an unexpected response."""


@dataclass(frozen=True)
class MarketData:
    """Container for historical market data."""

    prices: pd.DataFrame
    volumes: pd.DataFrame


def _parse_market_chart(data: Dict[str, List[List[float]]]) -> MarketData:
    price_rows = []
    volume_rows = []

    for timestamp, price in data.get("prices", []):
        price_rows.append(
            {
                "timestamp": dt.datetime.fromtimestamp(timestamp / 1000, dt.timezone.utc),
                "price": price,
            }
        )

    for timestamp, volume in data.get("total_volumes", []):
        volume_rows.append(
            {
                "timestamp": dt.datetime.fromtimestamp(timestamp / 1000, dt.timezone.utc),
                "volume": volume,
            }
        )

    prices_df = pd.DataFrame(price_rows).set_index("timestamp").sort_index()
    volumes_df = pd.DataFrame(volume_rows).set_index("timestamp").sort_index()

    return MarketData(prices=prices_df, volumes=volumes_df)


def fetch_market_chart(coin_id: str, vs_currency: str, days: int) -> MarketData:
    """Fetch market chart data for a coin from CoinGecko.

    Args:
        coin_id: CoinGecko identifier of the cryptocurrency.
        vs_currency: The target currency (e.g., "usd").
        days: Number of days of historical data to retrieve.

    Returns:
        MarketData: Historical price and volume data indexed by timestamp.

    Raises:
        CoinGeckoError: If the API responds with an error or malformed payload.
    """

    url = f"{COINGECKO_API}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days, "interval": "hourly" if days <= 90 else "daily"}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise CoinGeckoError("CoinGecko API'ye ulaşılamadı") from exc

    data = response.json()
    if not isinstance(data, dict) or "prices" not in data:
        raise CoinGeckoError("Beklenmeyen API cevabı alındı")

    return _parse_market_chart(data)


def list_supported_vs_currencies() -> List[str]:
    """Return supported vs currencies from CoinGecko."""
    url = f"{COINGECKO_API}/simple/supported_vs_currencies"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise CoinGeckoError("Kur listesi alınamadı") from exc

    data = response.json()
    if not isinstance(data, list):
        raise CoinGeckoError("Kur listesi beklenen formatta değil")

    return sorted(set(map(str.lower, data)))
