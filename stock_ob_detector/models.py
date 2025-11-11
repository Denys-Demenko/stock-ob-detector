"""Core data models used by the order block detector."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Bias(Enum):
    """Directional bias of an order block."""

    BULLISH = 1
    BEARISH = -1


@dataclass(slots=True)
class Candle:
    """Represents OHLC data for a single bar."""

    time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(slots=True)
class Pivot:
    """Tracks the most recent swing pivot for a given structure."""

    current_level: Optional[float] = None
    last_level: Optional[float] = None
    crossed: bool = False
    bar_time: Optional[datetime] = None
    bar_index: Optional[int] = None


@dataclass(slots=True)
class Trend:
    """Stores the latest detected trend bias."""

    bias: int = 0


@dataclass(slots=True)
class OrderBlock:
    """Represents a detected order block."""

    high: float
    low: float
    time: datetime
    bias: Bias
    internal: bool
    detected_at: datetime
    detected_index: int

    @property
    def label(self) -> str:
        """Return a human readable label for plotting."""

        prefix = "internal " if self.internal else ""
        side = "bull" if self.bias is Bias.BULLISH else "bear"
        return f"{prefix}{side} OB"
