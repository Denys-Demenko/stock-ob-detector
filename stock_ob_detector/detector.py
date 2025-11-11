"""Order block detection logic translated from the Pine script."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List

from .models import Bias, Candle, DetectionResult, OrderBlock, OrderBlockKind


@dataclass(slots=True)
class Pivot:
    """Represents a swing pivot."""

    current_level: float | None = None
    last_level: float | None = None
    crossed: bool = False
    bar_time: datetime | None = None
    bar_index: int | None = None


@dataclass(slots=True)
class Trend:
    """Represents the current structural bias."""

    bias: int = 0


@dataclass(slots=True)
class StructureContext:
    """Tracks leg and pivot information for a particular structure size."""

    size: int
    leg: int = 0
    high_pivot: Pivot = field(default_factory=Pivot)
    low_pivot: Pivot = field(default_factory=Pivot)
    trend: Trend = field(default_factory=Trend)

    def reset_cross_state(self) -> None:
        """Reset the pivot crossed state when switching legs."""

        self.high_pivot.crossed = False
        self.low_pivot.crossed = False


class OrderBlockDetector:
    """Detects swing and internal bullish order blocks."""

    def __init__(
        self,
        candles: Iterable[Candle],
        swing_size: int = 50,
        internal_size: int = 5,
        atr_period: int = 200,
    ) -> None:
        self._candles: List[Candle] = list(candles)
        if len(self._candles) < max(swing_size, internal_size) * 2:
            raise ValueError("Not enough candles for detection")
        self._swing_context = StructureContext(size=swing_size)
        self._internal_context = StructureContext(size=internal_size)
        self._atr_period = atr_period

        self._parsed_highs: List[float] = []
        self._parsed_lows: List[float] = []
        self._highs: List[float] = []
        self._lows: List[float] = []
        self._times: List[datetime] = []

        self._swing_order_blocks: List[OrderBlock] = []
        self._internal_order_blocks: List[OrderBlock] = []

    def detect(self) -> DetectionResult:
        """Run the detection process and return the resulting order blocks."""

        highs = [candle.high for candle in self._candles]
        lows = [candle.low for candle in self._candles]
        closes = [candle.close for candle in self._candles]

        atr_values = self._atr(highs, lows, closes)

        for index, candle in enumerate(self._candles):
            self._push_bar_data(index, candle, atr_values)

            if index == 0:
                continue

            self._update_structure(index, self._swing_context, highs, lows)
            self._update_structure(index, self._internal_context, highs, lows)

            self._evaluate_structure(index, self._swing_context, closes, internal=False)
            self._evaluate_structure(index, self._internal_context, closes, internal=True)

        return DetectionResult(
            swing_order_blocks=self._swing_order_blocks,
            internal_order_blocks=self._internal_order_blocks,
        )

    def _push_bar_data(self, index: int, candle: Candle, atr_values: List[float]) -> None:
        """Store parsed price data similar to the Pine implementation."""

        self._parsed_highs.append(candle.high)
        self._parsed_lows.append(candle.low)
        self._highs.append(candle.high)
        self._lows.append(candle.low)
        self._times.append(candle.timestamp)

    def _update_structure(
        self,
        index: int,
        context: StructureContext,
        highs: List[float],
        lows: List[float],
    ) -> None:
        """Update pivot information for the given structure context."""

        size = context.size
        if index < size:
            return

        previous_leg = context.leg
        candidate_high = highs[index - size]
        candidate_low = lows[index - size]

        future_high = highs[index - size + 1 : index + 1]
        future_low = lows[index - size + 1 : index + 1]

        new_leg = previous_leg
        if future_high and candidate_high > max(future_high):
            new_leg = 0
        elif future_low and candidate_low < min(future_low):
            new_leg = 1

        if new_leg != previous_leg:
            context.leg = new_leg
            change = new_leg - previous_leg
            context.reset_cross_state()
            pivot = context.low_pivot if change == 1 else context.high_pivot
            pivot.last_level = pivot.current_level
            pivot.current_level = candidate_low if change == 1 else candidate_high
            pivot.bar_index = index - size
            pivot.bar_time = self._times[index - size]
        else:
            context.leg = new_leg

    def _evaluate_structure(
        self,
        index: int,
        context: StructureContext,
        closes: List[float],
        *,
        internal: bool,
    ) -> None:
        """Check for break of structure and register order blocks."""

        close_now = closes[index]
        close_prev = closes[index - 1]

        if self._check_bullish_break(context.high_pivot, close_prev, close_now, internal):
            context.high_pivot.crossed = True
            context.trend.bias = Bias.BULLISH.value
            self._store_order_block(index, context.high_pivot, internal, Bias.BULLISH)

        if self._check_bearish_break(context.low_pivot, close_prev, close_now, internal):
            context.low_pivot.crossed = True
            context.trend.bias = Bias.BEARISH.value

    def _check_bullish_break(
        self,
        pivot: Pivot,
        close_prev: float,
        close_now: float,
        internal: bool,
    ) -> bool:
        """Return True when the pivot high is broken to the upside."""

        if pivot.current_level is None or pivot.crossed:
            return False
        if internal and pivot.current_level == self._swing_context.high_pivot.current_level:
            return False
        return close_prev <= pivot.current_level < close_now

    def _check_bearish_break(
        self,
        pivot: Pivot,
        close_prev: float,
        close_now: float,
        internal: bool,
    ) -> bool:
        """Return True when the pivot low is broken to the downside."""

        if pivot.current_level is None or pivot.crossed:
            return False
        if internal and pivot.current_level == self._swing_context.low_pivot.current_level:
            return False
        return close_prev >= pivot.current_level > close_now

    def _store_order_block(
        self,
        index: int,
        pivot: Pivot,
        internal: bool,
        bias: Bias,
    ) -> None:
        """Store a bullish order block following the Pine logic."""

        if pivot.bar_index is None:
            return

        start_index = pivot.bar_index
        end_index = index
        if end_index <= start_index:
            return
        parsed_slice = self._parsed_lows[start_index:end_index]
        if not parsed_slice:
            return

        relative_index = min(range(len(parsed_slice)), key=parsed_slice.__getitem__)
        parsed_index = start_index + relative_index

        high_level = self._parsed_highs[parsed_index]
        low_level = self._parsed_lows[parsed_index]
        start_time = self._times[parsed_index]

        order_block = OrderBlock(
            start=start_time,
            high=max(high_level, low_level),
            low=min(high_level, low_level),
            bias=bias,
            kind=OrderBlockKind.INTERNAL if internal else OrderBlockKind.SWING,
        )

        target = self._internal_order_blocks if internal else self._swing_order_blocks
        target.append(order_block)

    def _atr(self, highs: List[float], lows: List[float], closes: List[float]) -> List[float]:
        """Compute the Average True Range similar to Pine's ta.atr."""

        tr = [0.0] * len(highs)
        tr[0] = highs[0] - lows[0]
        for idx in range(1, len(highs)):
            high = highs[idx]
            low = lows[idx]
            prev_close = closes[idx - 1]
            tr[idx] = max(high - low, abs(high - prev_close), abs(low - prev_close))

        atr = [0.0] * len(tr)
        alpha = 1 / float(self._atr_period)
        atr[0] = tr[0]
        for idx in range(1, len(tr)):
            atr[idx] = atr[idx - 1] + alpha * (tr[idx] - atr[idx - 1])
        return atr
