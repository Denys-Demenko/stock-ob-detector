"""Utilities for loading and resampling candle data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .models import Candle


_TIMEFRAME_RULES = {
    "1D": "1D",
    "1W": "W-MON",
    "1M": "ME",
}


@dataclass(slots=True)
class CandleData:
    """Container for a series of candles."""

    candles: List[Candle]

    @classmethod
    def from_records(cls, records: Iterable[dict]) -> "CandleData":
        candles = [
            Candle(
                timestamp=datetime.fromisoformat(str(record["date"])),
                open=float(record["open"]),
                high=float(record["high"]),
                low=float(record["low"]),
                close=float(record["close"]),
            )
            for record in records
        ]
        candles.sort(key=lambda candle: candle.timestamp)
        return cls(candles)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": [candle.open for candle in self.candles],
                "high": [candle.high for candle in self.candles],
                "low": [candle.low for candle in self.candles],
                "close": [candle.close for candle in self.candles],
            },
            index=pd.DatetimeIndex([candle.timestamp for candle in self.candles], name="timestamp"),
        )

    def resample(self, timeframe: str) -> "CandleData":
        if timeframe not in _TIMEFRAME_RULES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        if timeframe == "1D":
            return CandleData(list(self.candles))

        df = self.to_dataframe()
        rule = _TIMEFRAME_RULES[timeframe]
        label = "left"
        closed = "left"
        if timeframe == "1M":
            label = "right"
            closed = "right"

        resampled = (
            df.resample(rule, label=label, closed=closed)
            .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
            .dropna()
        )
        if timeframe == "1M":
            resampled.index = resampled.index.to_period("M").to_timestamp("M")
        candles = [
            Candle(
                timestamp=index.to_pydatetime(),
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
            )
            for index, row in resampled.iterrows()
        ]
        return CandleData(candles)


def load_candles(path: Path) -> CandleData:
    records = pd.read_json(path).to_dict(orient="records")
    return CandleData.from_records(records)
