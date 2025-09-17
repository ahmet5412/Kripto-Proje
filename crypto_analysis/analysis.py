"""High level analysis helpers."""
from __future__ import annotations

import pandas as pd

from . import indicators


def enrich_with_indicators(prices: pd.Series) -> pd.DataFrame:
    """Return dataframe with common indicators based on closing prices."""
    df = pd.DataFrame({"price": prices})
    df["sma_20"] = indicators.moving_average(df["price"], 20)
    df["sma_50"] = indicators.moving_average(df["price"], 50)
    df["ema_20"] = indicators.exponential_moving_average(df["price"], 20)
    df["rsi_14"] = indicators.rsi(df["price"], 14)
    df["volatility_30"] = indicators.volatility(df["price"], 30)
    return df


def build_summary(prices: pd.Series) -> str:
    """Create a human readable summary for the price series."""
    if prices.empty:
        return "Veri bulunamadı."

    current = prices.iloc[-1]
    start = prices.iloc[0]
    change = ((current - start) / start) * 100 if start else 0
    max_price = prices.max()
    min_price = prices.min()
    rsi_latest = indicators.rsi(prices).iloc[-1]

    lines = [
        f"Başlangıç fiyatı: {start:,.2f}",
        f"Güncel fiyat: {current:,.2f}",
        f"Değişim: {change:,.2f} %",
        f"En yüksek fiyat: {max_price:,.2f}",
        f"En düşük fiyat: {min_price:,.2f}",
        f"RSI (14): {rsi_latest:,.2f}",
    ]

    if rsi_latest > 70:
        lines.append("Yorum: RSI aşırı alım bölgesinde, düzeltme gelebilir.")
    elif rsi_latest < 30:
        lines.append("Yorum: RSI aşırı satım bölgesinde, toparlanma mümkün.")
    else:
        lines.append("Yorum: RSI nötr seviyelerde.")

    return "\n".join(lines)
