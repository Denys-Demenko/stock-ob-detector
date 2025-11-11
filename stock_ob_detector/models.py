"""Domain models for the stock order block detector."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Sequence


class Bias(Enum):
    """Represents the direction of an order block."""

    BULLISH = 1
    BEARISH = -1


class OrderBlockKind(Enum):
    """The origin of an order block."""

    SWING = "swing"
    INTERNAL = "internal"


@dataclass(slots=True)
class Candle:
    """Represents OHLCV information for a single bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class OrderBlock:
    """Represents a detected order block."""

    start: datetime
    high: float
    low: float
    bias: Bias
    kind: OrderBlockKind

    def as_range(self) -> tuple[float, float]:
        """Return the price range of the order block."""

        return self.low, self.high


@dataclass(slots=True)
class DetectionResult:
    """Aggregated detection output for a run."""

    swing_order_blocks: Sequence[OrderBlock]
    internal_order_blocks: Sequence[OrderBlock]

    def all_blocks(self) -> List[OrderBlock]:
        """Return all order blocks sorted from oldest to newest."""

        return sorted(
            [*self.swing_order_blocks, *self.internal_order_blocks],
            key=lambda block: block.start,
        )
