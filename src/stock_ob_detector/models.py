"""Core domain models for the stock order block detector."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Bias(Enum):
    """Represents the direction of a structure or order block."""

    BULLISH = 1
    BEARISH = -1


@dataclass
class Bar:
    """Single OHLCV bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Pivot:
    """Stores information about detected pivot highs or lows."""

    current_level: Optional[float] = None
    last_level: Optional[float] = None
    crossed: bool = False
    bar_time: Optional[datetime] = None
    bar_index: Optional[int] = None


@dataclass
class Trend:
    """Tracks the current trend direction."""

    bias: int = 0


@dataclass
class OrderBlock:
    """Represents a detected order block."""

    high: float
    low: float
    start_time: datetime
    created_time: datetime
    pivot_time: datetime
    bias: Bias
    internal: bool
    mitigated: bool = False

    def label(self) -> str:
        """Return a short label describing the order block."""

        prefix = "internal " if self.internal else ""
        direction = "bull" if self.bias is Bias.BULLISH else "bear"
        return f"{prefix}{direction} OB"
