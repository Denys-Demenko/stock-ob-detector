"""Order block detection logic derived from the Pine Script reference."""
from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, List, Optional, Sequence

from .models import Bar, Bias, OrderBlock, Pivot, Trend


class OrderBlockDetector:
    """Detect swing and internal order blocks."""

    def __init__(
        self,
        swing_length: int = 5,
        internal_length: int = 4,
        atr_period: int = 200,
        max_order_blocks: int = 100,
    ) -> None:
        if swing_length <= 0 or internal_length <= 0:
            raise ValueError("Structure lengths must be positive")

        self.swing_length = swing_length
        self.internal_length = internal_length
        self.atr_period = atr_period
        self.max_order_blocks = max_order_blocks

        self.bars: List[Bar] = []
        self.parsed_highs: List[float] = []
        self.parsed_lows: List[float] = []
        self.atr_window: Deque[float] = deque(maxlen=atr_period)

        self.legs: Dict[int, int] = {}

        self.swing_high = Pivot()
        self.swing_low = Pivot()
        self.internal_high = Pivot()
        self.internal_low = Pivot()

        self.swing_trend = Trend()
        self.internal_trend = Trend()

        self.internal_order_blocks: List[OrderBlock] = []
        self.swing_order_blocks: List[OrderBlock] = []
        self.detected_order_blocks: List[OrderBlock] = []

    def process(self, bars: Sequence[Bar]) -> List[OrderBlock]:
        """Process the provided bars and return detected order blocks."""

        for bar in bars:
            self._process_bar(bar)
        return list(self.detected_order_blocks)

    def _process_bar(self, bar: Bar) -> None:
        self._append_bar(bar)

        self._update_structure(self.swing_length, internal=False)
        self._update_structure(self.internal_length, internal=True)

        self._display_structure(internal=True)
        self._display_structure(internal=False)

        self._delete_order_blocks(internal=True)
        self._delete_order_blocks(internal=False)

    def _append_bar(self, bar: Bar) -> None:
        prev_bar = self.bars[-1] if self.bars else None
        self.bars.append(bar)

        tr = self._true_range(bar, prev_bar)
        self.atr_window.append(tr)
        atr = self._average(self.atr_window)
        volatility_threshold = atr if atr else bar.high - bar.low
        high_volatility = (bar.high - bar.low) >= 2 * volatility_threshold

        parsed_high = bar.low if high_volatility else bar.high
        parsed_low = bar.high if high_volatility else bar.low

        self.parsed_highs.append(parsed_high)
        self.parsed_lows.append(parsed_low)

    @staticmethod
    def _true_range(bar: Bar, prev_bar: Optional[Bar]) -> float:
        if prev_bar is None:
            return bar.high - bar.low
        high_low = bar.high - bar.low
        high_close = abs(bar.high - prev_bar.close)
        low_close = abs(bar.low - prev_bar.close)
        return max(high_low, high_close, low_close)

    @staticmethod
    def _average(values: Iterable[float]) -> Optional[float]:
        total = 0.0
        count = 0
        for value in values:
            total += value
            count += 1
        if count == 0:
            return None
        return total / count

    def _update_structure(self, size: int, *, internal: bool) -> None:
        if len(self.bars) <= size:
            return

        prev_leg = self.legs.get(size, 0)
        current_leg = prev_leg

        anchor_index = len(self.bars) - 1 - size
        if anchor_index < 0:
            return

        anchor_bar = self.bars[anchor_index]
        subsequent = self.bars[anchor_index + 1 :]
        if not subsequent:
            return

        recent_high = max(bar.high for bar in subsequent)
        recent_low = min(bar.low for bar in subsequent)

        if anchor_bar.high > recent_high:
            current_leg = 0
        elif anchor_bar.low < recent_low:
            current_leg = 1

        self.legs[size] = current_leg
        change = current_leg - prev_leg
        if change == 0:
            return

        if change == 1:
            pivot = self.internal_low if internal else self.swing_low
            self._set_pivot(pivot, anchor_bar.low, anchor_bar.timestamp, anchor_index)
        elif change == -1:
            pivot = self.internal_high if internal else self.swing_high
            self._set_pivot(pivot, anchor_bar.high, anchor_bar.timestamp, anchor_index)

    @staticmethod
    def _set_pivot(pivot: Pivot, level: float, timestamp, index: int) -> None:
        pivot.last_level = pivot.current_level
        pivot.current_level = level
        pivot.crossed = False
        pivot.bar_time = timestamp
        pivot.bar_index = index

    def _display_structure(self, *, internal: bool) -> None:
        if len(self.bars) < 2:
            return

        pivot_high = self.internal_high if internal else self.swing_high
        pivot_low = self.internal_low if internal else self.swing_low
        trend = self.internal_trend if internal else self.swing_trend

        previous_close = self.bars[-2].close
        current_close = self.bars[-1].close

        if (
            pivot_high.current_level is not None
            and not pivot_high.crossed
            and previous_close <= pivot_high.current_level
            and current_close > pivot_high.current_level
        ):
            trend.bias = Bias.BULLISH.value
            pivot_high.crossed = True
            self._store_order_block(pivot_high, internal, Bias.BULLISH)

        if (
            pivot_low.current_level is not None
            and not pivot_low.crossed
            and previous_close >= pivot_low.current_level
            and current_close < pivot_low.current_level
        ):
            trend.bias = Bias.BEARISH.value
            pivot_low.crossed = True
            self._store_order_block(pivot_low, internal, Bias.BEARISH)

    def _store_order_block(
        self,
        pivot: Pivot,
        internal: bool,
        bias: Bias,
    ) -> None:
        if pivot.bar_index is None:
            return

        start_index = pivot.bar_index
        end_index = len(self.bars)
        if end_index <= start_index:
            return

        segment_highs = self.parsed_highs[start_index:end_index]
        segment_lows = self.parsed_lows[start_index:end_index]

        if bias is Bias.BULLISH:
            reference_values = segment_lows
            if not reference_values:
                return
            offset = reference_values.index(min(reference_values))
        else:
            reference_values = segment_highs
            if not reference_values:
                return
            offset = reference_values.index(max(reference_values))

        order_index = start_index + offset
        order_high = self.parsed_highs[order_index]
        order_low = self.parsed_lows[order_index]
        order_time = self.bars[order_index].timestamp
        pivot_time = pivot.bar_time or order_time
        created_time = self.bars[-1].timestamp

        order_block = OrderBlock(
            high=order_high,
            low=order_low,
            start_time=order_time,
            created_time=created_time,
            pivot_time=pivot_time,
            bias=bias,
            internal=internal,
        )

        self.detected_order_blocks.append(order_block)

        container = (
            self.internal_order_blocks if internal else self.swing_order_blocks
        )
        container.insert(0, order_block)
        del container[self.max_order_blocks :]

    def _delete_order_blocks(self, *, internal: bool) -> None:
        container = (
            self.internal_order_blocks if internal else self.swing_order_blocks
        )
        if not container:
            return

        current_bar = self.bars[-1]
        updated: List[OrderBlock] = []
        for order_block in container:
            if order_block.bias is Bias.BULLISH:
                mitigated = current_bar.low < order_block.low
            else:
                mitigated = current_bar.high > order_block.high
            if mitigated:
                order_block.mitigated = True
            else:
                updated.append(order_block)
        container[:] = updated

    def get_active_order_blocks(self) -> List[OrderBlock]:
        """Return all currently active order blocks."""

        return self.internal_order_blocks + self.swing_order_blocks
