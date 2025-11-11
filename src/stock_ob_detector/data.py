"""Utilities for loading and resampling OHLCV data."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

from .models import Bar


@dataclass(frozen=True)
class Dataset:
    """Represents a collection of OHLCV bars."""

    bars: Sequence[Bar]

    @classmethod
    def from_json(
        cls,
        path: Path,
        timeframe: str = "1D",
    ) -> "Dataset":
        """Load OHLCV data from the given JSON file."""

        frame = pd.read_json(path)
        frame = frame.drop_duplicates(subset="date", keep="last")
        frame["date"] = pd.to_datetime(frame["date"])
        frame = frame.sort_values("date")

        frame = _resample(frame, timeframe)

        bars = [
            Bar(
                timestamp=row["date"].to_pydatetime(),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0)),
            )
            for row in frame.to_dict("records")
        ]
        return cls(bars=bars)


def _resample(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    timeframe = timeframe.upper()
    if timeframe not in {"1D", "1W", "1M"}:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    if timeframe == "1D":
        return frame.reset_index(drop=True)

    rule = {"1W": "W", "1M": "ME"}[timeframe]
    resampled = (
        frame.set_index("date")
        .resample(rule, label="right", closed="right")
        .agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        .dropna()
        .reset_index()
    )
    return resampled


def as_bars(iterable: Iterable[Bar]) -> List[Bar]:
    """Return a concrete list of bars."""

    return list(iterable)
