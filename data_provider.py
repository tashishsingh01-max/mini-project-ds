"""Demo and optional live market data helpers."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Literal

import numpy as np
import pandas as pd

DataMode = Literal["demo", "live", "demo-fallback"]


def demo_data(symbol: str = "AAPL", days: int = 365) -> pd.DataFrame:
    """Create repeatable offline data so the project works without a network."""
    seed = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    movement = rng.normal(0.0004, 0.018, len(dates))
    close = 100 * np.exp(np.cumsum(movement))
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": close * (1 + rng.normal(0, 0.004, len(dates))),
            "High": close * (1 + rng.uniform(0.002, 0.018, len(dates))),
            "Low": close * (1 - rng.uniform(0.002, 0.018, len(dates))),
            "Close": close,
            "Volume": rng.integers(500_000, 5_000_000, len(dates)),
        }
    )


@lru_cache(maxsize=16)
def load_live(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Fetch Yahoo Finance data only when the user enables Live Data."""
    import yfinance as yf

    frame = yf.Ticker(symbol).history(period=period, auto_adjust=False)
    if frame is None or frame.empty:
        raise RuntimeError("Live data returned no rows")
    frame = frame.reset_index()
    date_column = "Datetime" if "Datetime" in frame.columns else "Date"
    frame["Date"] = pd.to_datetime(frame[date_column], utc=True).dt.tz_convert(None)
    return frame[["Date", "Open", "High", "Low", "Close", "Volume"]].dropna()


def get_data(symbol: str, live: bool) -> tuple[pd.DataFrame, DataMode, str | None]:
    """Return live data when possible and explain a fallback in the UI."""
    if not live:
        return demo_data(symbol), "demo", None
    try:
        return load_live(symbol), "live", None
    except Exception as error:  # network/rate-limit errors should not break the app
        return demo_data(symbol), "demo-fallback", str(error)


def filter_data(
    frame: pd.DataFrame,
    timeframe: str,
    start_date: object | None = None,
    end_date: object | None = None,
) -> pd.DataFrame:
    """Filter the chart using the selected quick range or custom dates."""
    if frame.empty:
        return frame
    end = frame["Date"].max().normalize()
    if timeframe == "Weekly":
        start = end - pd.Timedelta(days=6)
    elif timeframe == "Monthly":
        start = end - pd.Timedelta(days=29)
    elif timeframe == "Yearly":
        start = end - pd.Timedelta(days=364)
    else:
        start = pd.Timestamp(start_date).normalize() if start_date else end - pd.Timedelta(days=6)
        end = pd.Timestamp(end_date).normalize() if end_date else end
    return frame[(frame["Date"] >= start) & (frame["Date"] <= end)].copy()