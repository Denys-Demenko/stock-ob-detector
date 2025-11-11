"""Utilities for loading and transforming candle data."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .models import Candle


@dataclass(slots=True)
class Timeframe:
    """Represents a supported timeframe."""

    value: str

    @classmethod
    def parse(cls, value: str) -> "Timeframe":
        mapping = {
            "1d": "1D",
            "1w": "1W",
            "1m": "1M",
        }
        normalised = value.strip().lower()
        if normalised not in mapping:
            raise ValueError(f"Unsupported timeframe: {value}")
        return cls(mapping[normalised])

    def resample(self, candles: List[Candle]) -> List[Candle]:
        """Return candles resampled to the timeframe."""

        if self.value == "1D":
            return candles
        grouped: Dict[Tuple[int, int, int], List[Candle]] = defaultdict(list)
        for candle in candles:
            key = self._group_key(candle.timestamp)
            grouped[key].append(candle)

        results: List[Candle] = []
        for key in sorted(grouped):
            chunk = grouped[key]
            chunk_sorted = sorted(chunk, key=lambda candle: candle.timestamp)
            open_price = chunk_sorted[0].open
            close_price = chunk_sorted[-1].close
            high_price = max(candle.high for candle in chunk_sorted)
            low_price = min(candle.low for candle in chunk_sorted)
            volume = sum(candle.volume for candle in chunk_sorted)
            timestamp = self._label_timestamp(chunk_sorted)
            results.append(
                Candle(
                    timestamp=timestamp,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
            )
        return results

    def _group_key(self, timestamp: datetime) -> Tuple[int, int, int]:
        if self.value == "1W":
            year, week, _ = timestamp.isocalendar()
            return year, week, 0
        if self.value == "1M":
            return timestamp.year, timestamp.month, 0
        raise ValueError(f"Unsupported timeframe: {self.value}")

    def _label_timestamp(self, candles: List[Candle]) -> datetime:
        return candles[-1].timestamp


class CandleLoader:
    """Loads candle data from JSON files."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> List[Candle]:
        with self._path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        candles = [
            Candle(
                timestamp=datetime.fromisoformat(entry["date"]),
                open=float(entry["open"]),
                high=float(entry["high"]),
                low=float(entry["low"]),
                close=float(entry["close"]),
                volume=float(entry.get("volume", 0.0)),
            )
            for entry in raw
        ]
        candles.sort(key=lambda candle: candle.timestamp)
        return candles

    def load_resampled(self, timeframe: Timeframe) -> List[Candle]:
        candles = self.load()
        return timeframe.resample(candles)
