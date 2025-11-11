"""Core domain models for order block detection."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Bias(Enum):
    """Directional bias for detected structures."""

    BULLISH = 1
    BEARISH = -1


@dataclass(slots=True)
class Candle:
    """Single OHLC candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(slots=True)
class Pivot:
    """Represents a structural pivot point."""

    current_level: Optional[float] = None
    last_level: Optional[float] = None
    crossed: bool = False
    bar_time: Optional[datetime] = None
    bar_index: Optional[int] = None


@dataclass(slots=True)
class Trend:
    """Simple structure trend state."""

    bias: int = 0


@dataclass(slots=True)
class OrderBlock:
    """Detected order block boundaries."""

    high: float
    low: float
    timestamp: datetime
    bias: Bias
    is_internal: bool


@dataclass(slots=True)
class TrailingExtremes:
    """Tracks most recent swing extremes for plotting."""

    top: Optional[float] = None
    bottom: Optional[float] = None
    last_top_time: Optional[datetime] = None
    last_bottom_time: Optional[datetime] = None
    last_top_index: Optional[int] = None
    last_bottom_index: Optional[int] = None
