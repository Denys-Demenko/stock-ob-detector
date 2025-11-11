"""Utilities for loading and resampling OHLC data without external deps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .detector import Timeframe
from .models import Candle


@dataclass(slots=True)
class LoadedData:
    """Container holding loaded candles and metadata."""

    ticker: str
    candles: List[Candle]


def load_candles(path: Path, *, timeframe: Timeframe) -> LoadedData:
    """Load OHLC candles from ``path`` and aggregate to the given timeframe."""

    with path.open("r", encoding="utf-8") as handle:
        raw_candles = json.load(handle)

    daily_candles = [
        Candle(
            time=datetime.fromisoformat(entry["date"]),
            open=float(entry["open"]),
            high=float(entry["high"]),
            low=float(entry["low"]),
            close=float(entry["close"]),
        )
        for entry in raw_candles
    ]
    daily_candles.sort(key=lambda candle: candle.time)

    if timeframe is Timeframe.ONE_DAY:
        aggregated = daily_candles
    else:
        aggregated = _aggregate_candles(daily_candles, timeframe)

    ticker = path.stem.upper()
    return LoadedData(ticker=ticker, candles=aggregated)


def _aggregate_candles(candles: List[Candle], timeframe: Timeframe) -> List[Candle]:
    grouped: Dict[Tuple[int, int], List[Candle]] = {}

    for candle in candles:
        key = _group_key(candle.time, timeframe)
        grouped.setdefault(key, []).append(candle)

    aggregated: List[Candle] = []
    for key in sorted(grouped):
        group = grouped[key]
        group.sort(key=lambda candle: candle.time)
        aggregated.append(
            Candle(
                time=group[-1].time,
                open=group[0].open,
                high=max(candle.high for candle in group),
                low=min(candle.low for candle in group),
                close=group[-1].close,
            )
        )

    return aggregated


def _group_key(moment: datetime, timeframe: Timeframe) -> Tuple[int, int]:
    if timeframe is Timeframe.ONE_WEEK:
        iso = moment.isocalendar()
        return iso.year, iso.week
    if timeframe is Timeframe.ONE_MONTH:
        return moment.year, moment.month
    return moment.year, moment.timetuple().tm_yday
