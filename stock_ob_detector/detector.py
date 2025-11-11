"""Order block detection logic translated from the Pine Script indicator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable, List, Optional

from .models import Bias, Candle, OrderBlock, Pivot, Trend


class Timeframe(str, Enum):
    """Supported aggregation granularities."""

    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

    @property
    def pandas_rule(self) -> str:
        """Return the pandas resampling rule for the timeframe."""

        return {
            Timeframe.ONE_DAY: "1D",
            Timeframe.ONE_WEEK: "1W",
            Timeframe.ONE_MONTH: "1M",
        }[self]


@dataclass(slots=True)
class _ParsedBar:
    """Holds derived values required by the detection algorithm."""

    parsed_high: float
    parsed_low: float
    atr: float


class _AtrCalculator:
    """Incremental ATR calculator replicating ``ta.atr(200)`` behaviour."""

    def __init__(self, period: int = 200) -> None:
        self.period = period
        self._value: Optional[float] = None
        self._prev_close: Optional[float] = None
        self._buffer: List[float] = []

    def update(self, high: float, low: float, close: float) -> float:
        """Update the ATR series with a new bar and return the latest value."""

        true_range: float
        if self._prev_close is None:
            true_range = high - low
        else:
            true_range = max(
                high - low,
                abs(high - self._prev_close),
                abs(low - self._prev_close),
            )

        if self._value is None:
            self._buffer.append(true_range)
            if len(self._buffer) < self.period:
                self._prev_close = close
                return sum(self._buffer) / len(self._buffer)
            self._value = sum(self._buffer[-self.period :]) / self.period
        else:
            self._value = (
                (self._value * (self.period - 1)) + true_range
            ) / self.period

        self._prev_close = close
        return self._value


class OrderBlockDetector:
    """Detect internal and swing order blocks using OHLC candles."""

    def __init__(self, swing_length: int = 50, internal_length: int = 5) -> None:
        self.swing_length = swing_length
        self.internal_length = internal_length

        self._swing_high = Pivot()
        self._swing_low = Pivot()
        self._internal_high = Pivot()
        self._internal_low = Pivot()

        self._swing_trend = Trend()
        self._internal_trend = Trend()

        self._parsed_bars: List[_ParsedBar] = []
        self._highs: List[float] = []
        self._lows: List[float] = []
        self._closes: List[float] = []
        self._times: List[datetime] = []

        self._order_blocks: List[OrderBlock] = []
        self._atr = _AtrCalculator()

    @property
    def order_blocks(self) -> List[OrderBlock]:
        """Return the list of detected order blocks."""

        return list(self._order_blocks)

    def process(self, candles: Iterable[Candle]) -> List[OrderBlock]:
        """Process candles and return detected order blocks."""

        for index, candle in enumerate(candles):
            atr = self._atr.update(candle.high, candle.low, candle.close)
            high_low_range = candle.high - candle.low
            high_volatility = atr > 0 and high_low_range >= (2 * atr)
            parsed_high = candle.low if high_volatility else candle.high
            parsed_low = candle.high if high_volatility else candle.low

            self._parsed_bars.append(
                _ParsedBar(parsed_high=parsed_high, parsed_low=parsed_low, atr=atr)
            )
            self._highs.append(candle.high)
            self._lows.append(candle.low)
            self._closes.append(candle.close)
            self._times.append(candle.time)

            self._update_structure(
                size=self.swing_length,
                pivot_high=self._swing_high,
                pivot_low=self._swing_low,
                index=index,
            )
            self._update_structure(
                size=self.internal_length,
                pivot_high=self._internal_high,
                pivot_low=self._internal_low,
                index=index,
            )

            self._display_structure(index, internal=True)
            self._display_structure(index, internal=False)

        return list(self._order_blocks)

    def _update_structure(
        self,
        *,
        size: int,
        pivot_high: Pivot,
        pivot_low: Pivot,
        index: int,
    ) -> None:
        if index < size:
            return

        lookback_index = index - size
        window_slice = slice(lookback_index + 1, index + 1)
        highest_since = max(self._highs[window_slice])
        lowest_since = min(self._lows[window_slice])

        if self._lows[lookback_index] < lowest_since:
            self._assign_pivot(
                pivot=pivot_low,
                level=self._lows[lookback_index],
                index=lookback_index,
            )
        elif self._highs[lookback_index] > highest_since:
            self._assign_pivot(
                pivot=pivot_high,
                level=self._highs[lookback_index],
                index=lookback_index,
            )

    def _assign_pivot(self, *, pivot: Pivot, level: float, index: int) -> None:
        pivot.last_level = pivot.current_level
        pivot.current_level = level
        pivot.crossed = False
        pivot.bar_time = self._times[index]
        pivot.bar_index = index

    def _display_structure(self, index: int, *, internal: bool) -> None:
        pivot_high = self._internal_high if internal else self._swing_high
        pivot_low = self._internal_low if internal else self._swing_low
        trend = self._internal_trend if internal else self._swing_trend

        other_high = self._swing_high if internal else None
        other_low = self._swing_low if internal else None

        self._maybe_store_bullish_order_block(
            index=index,
            pivot=pivot_high,
            trend=trend,
            internal=internal,
            other_pivot=other_high,
        )
        self._maybe_store_bearish_order_block(
            index=index,
            pivot=pivot_low,
            trend=trend,
            internal=internal,
            other_pivot=other_low,
        )

    def _maybe_store_bullish_order_block(
        self,
        *,
        index: int,
        pivot: Pivot,
        trend: Trend,
        internal: bool,
        other_pivot: Optional[Pivot],
    ) -> None:
        if pivot.current_level is None or pivot.bar_index is None:
            return

        if other_pivot and other_pivot.current_level == pivot.current_level:
            return

        prev_close = self._closes[index - 1] if index > 0 else None
        current_close = self._closes[index]
        level = pivot.current_level

        if prev_close is None:
            return

        crossed = prev_close <= level < current_close
        if crossed and not pivot.crossed:
            trend.bias = Bias.BULLISH.value
            pivot.crossed = True
            self._store_order_block(
                pivot=pivot,
                bias=Bias.BULLISH,
                index=index,
                internal=internal,
            )

    def _maybe_store_bearish_order_block(
        self,
        *,
        index: int,
        pivot: Pivot,
        trend: Trend,
        internal: bool,
        other_pivot: Optional[Pivot],
    ) -> None:
        if pivot.current_level is None or pivot.bar_index is None:
            return

        if other_pivot and other_pivot.current_level == pivot.current_level:
            return

        prev_close = self._closes[index - 1] if index > 0 else None
        current_close = self._closes[index]
        level = pivot.current_level

        if prev_close is None:
            return

        crossed = prev_close >= level > current_close
        if crossed and not pivot.crossed:
            trend.bias = Bias.BEARISH.value
            pivot.crossed = True
            self._store_order_block(
                pivot=pivot,
                bias=Bias.BEARISH,
                index=index,
                internal=internal,
            )

    def _store_order_block(
        self,
        *,
        pivot: Pivot,
        bias: Bias,
        index: int,
        internal: bool,
    ) -> None:
        if pivot.bar_index is None:
            return

        start = pivot.bar_index
        end = index + 1
        parsed_segment = self._parsed_bars[start:end]

        if not parsed_segment:
            return

        if bias is Bias.BEARISH:
            values = self._highs[start:end]
            relative_index = max(range(len(values)), key=values.__getitem__)
        else:
            values = self._lows[start:end]
            relative_index = min(range(len(values)), key=values.__getitem__)

        absolute_index = start + relative_index

        order_block = OrderBlock(
            high=self._highs[absolute_index],
            low=self._lows[absolute_index],
            time=self._times[absolute_index],
            bias=bias,
            internal=internal,
            detected_at=self._times[index],
            detected_index=index,
        )
        self._order_blocks.append(order_block)
