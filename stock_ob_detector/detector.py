"""Order block detection engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Sequence, Tuple

from .models import Bias, Candle, OrderBlock, Pivot, Trend

_BEARISH_LEG = 0
_BULLISH_LEG = 1


@dataclass
class _StructureState:
    pivot_high: Pivot = field(default_factory=Pivot)
    pivot_low: Pivot = field(default_factory=Pivot)
    trend: Trend = field(default_factory=Trend)
    leg_value: int = _BEARISH_LEG


class OrderBlockDetector:
    """Detects swing and internal bullish and bearish order blocks."""

    def __init__(
        self,
        candles: Sequence[Candle],
        swing_length: int = 50,
        internal_length: int = 5,
    ) -> None:
        if swing_length <= internal_length:
            raise ValueError("Swing length must be greater than internal length")
        self._candles = candles
        self._swing_length = swing_length
        self._internal_length = internal_length
        self._parsed_highs: List[float] = []
        self._parsed_lows: List[float] = []
        self._times: List[datetime] = []
        self._states: Dict[int, _StructureState] = {
            swing_length: _StructureState(),
            internal_length: _StructureState(),
        }
        self._swing_order_blocks: List[OrderBlock] = []
        self._internal_order_blocks: List[OrderBlock] = []

    @property
    def swing_order_blocks(self) -> Sequence[OrderBlock]:
        return self._swing_order_blocks

    @property
    def internal_order_blocks(self) -> Sequence[OrderBlock]:
        return self._internal_order_blocks

    def detect(self) -> None:
        for index, candle in enumerate(self._candles):
            self._register_candle(candle)
            self._process_structure(index, self._swing_length, internal=False)
            self._process_structure(index, self._internal_length, internal=True)

    def _register_candle(self, candle: Candle) -> None:
        self._parsed_highs.append(candle.high)
        self._parsed_lows.append(candle.low)
        self._times.append(candle.timestamp)

    def _process_structure(self, index: int, length: int, *, internal: bool) -> None:
        state = self._states[length]
        leg_value = self._compute_leg(index, length, state.leg_value)
        leg_changed = leg_value != state.leg_value
        pivot_is_low = leg_changed and leg_value == _BULLISH_LEG
        pivot_is_high = leg_changed and leg_value == _BEARISH_LEG
        state.leg_value = leg_value

        if pivot_is_low:
            self._update_pivot_low(state.pivot_low, index, length)
        elif pivot_is_high:
            self._update_pivot_high(state.pivot_high, index, length)

        self._check_breakout(index, internal, state)

    def _compute_leg(self, index: int, length: int, previous: int) -> int:
        if index < length:
            return previous

        pivot_index = index - length
        recent_highs = self._parsed_highs[pivot_index + 1 : index + 1]
        recent_lows = self._parsed_lows[pivot_index + 1 : index + 1]
        if not recent_highs or not recent_lows:
            return previous

        new_leg_high = self._parsed_highs[pivot_index] > max(recent_highs)
        new_leg_low = self._parsed_lows[pivot_index] < min(recent_lows)

        if new_leg_high:
            return _BEARISH_LEG
        if new_leg_low:
            return _BULLISH_LEG
        return previous

    def _update_pivot_low(self, pivot: Pivot, index: int, length: int) -> None:
        pivot_index = index - length
        pivot.last_level = pivot.current_level
        pivot.current_level = self._parsed_lows[pivot_index]
        pivot.crossed = False
        pivot.bar_time = self._times[pivot_index]
        pivot.bar_index = pivot_index

    def _update_pivot_high(self, pivot: Pivot, index: int, length: int) -> None:
        pivot_index = index - length
        pivot.last_level = pivot.current_level
        pivot.current_level = self._parsed_highs[pivot_index]
        pivot.crossed = False
        pivot.bar_time = self._times[pivot_index]
        pivot.bar_index = pivot_index

    def _check_breakout(self, index: int, internal: bool, state: _StructureState) -> None:
        candle = self._candles[index]
        self._check_bullish_breakout(index, internal, state, candle)
        self._check_bearish_breakout(index, internal, state, candle)

    def _check_bullish_breakout(
        self,
        index: int,
        internal: bool,
        state: _StructureState,
        candle: Candle,
    ) -> None:
        pivot = state.pivot_high
        if pivot.current_level is None or pivot.bar_index is None:
            return

        if index == 0:
            return

        previous_close = self._candles[index - 1].close
        crossed = (
            previous_close <= pivot.current_level
            and candle.close > pivot.current_level
            and not pivot.crossed
        )
        if not crossed:
            return

        pivot.crossed = True
        state.trend.bias = Bias.BULLISH.value
        self._store_order_block(index, internal, Bias.BULLISH, state)

    def _check_bearish_breakout(
        self,
        index: int,
        internal: bool,
        state: _StructureState,
        candle: Candle,
    ) -> None:
        pivot = state.pivot_low
        if pivot.current_level is None or pivot.bar_index is None:
            return

        if index == 0:
            return

        previous_close = self._candles[index - 1].close
        crossed = (
            previous_close >= pivot.current_level
            and candle.close < pivot.current_level
            and not pivot.crossed
        )
        if not crossed:
            return

        pivot.crossed = True
        state.trend.bias = Bias.BEARISH.value
        self._store_order_block(index, internal, Bias.BEARISH, state)

    def _store_order_block(
        self,
        index: int,
        internal: bool,
        bias: Bias,
        state: _StructureState,
    ) -> None:
        pivot = state.pivot_high if bias == Bias.BULLISH else state.pivot_low
        if pivot.bar_index is None:
            return

        start = pivot.bar_index
        highs_slice = self._parsed_highs[start : index + 1]
        lows_slice = self._parsed_lows[start : index + 1]

        if not highs_slice or not lows_slice:
            return

        if bias == Bias.BEARISH:
            relative_index = highs_slice.index(max(highs_slice))
        else:
            relative_index = lows_slice.index(min(lows_slice))

        ob_index = start + relative_index
        order_block = OrderBlock(
            high=self._parsed_highs[ob_index],
            low=self._parsed_lows[ob_index],
            timestamp=self._times[ob_index],
            bias=bias,
            is_internal=internal,
        )

        container = (
            self._internal_order_blocks if internal else self._swing_order_blocks
        )
        container.append(order_block)

    def summarize(self) -> Dict[str, List[Tuple[datetime, float, float, Bias]]]:
        return {
            "swing": [
                (ob.timestamp, ob.low, ob.high, ob.bias)
                for ob in self._swing_order_blocks
                if ob.bias == Bias.BULLISH
            ],
            "internal": [
                (ob.timestamp, ob.low, ob.high, ob.bias)
                for ob in self._internal_order_blocks
                if ob.bias == Bias.BULLISH
            ],
        }
