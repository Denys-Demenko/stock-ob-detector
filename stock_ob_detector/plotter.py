"""Chart plotting helpers using matplotlib."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .models import Bias, Candle, OrderBlock


class ChartPlotter:
    """Simple candlestick and order block plotter."""

    def __init__(self) -> None:
        self._figure, self._axis = plt.subplots(figsize=(14, 8))

    @property
    def axis(self) -> Axes:
        return self._axis

    def plot_candles(self, candles: Sequence[Candle]) -> None:
        xs = range(len(candles))
        highs = [candle.high for candle in candles]
        lows = [candle.low for candle in candles]
        opens = [candle.open for candle in candles]
        closes = [candle.close for candle in candles]
        colors = ["#089981" if close >= open else "#F23645" for open, close in zip(opens, closes)]

        self._axis.vlines(xs, lows, highs, color="black", linewidth=1.0)
        self._axis.bar(
            xs,
            [abs(close - open) for open, close in zip(opens, closes)],
            bottom=[min(open, close) for open, close in zip(opens, closes)],
            color=colors,
            width=0.6,
        )
        self._axis.set_xlim(-1, len(candles) + 1)
        self._axis.set_title("Price with Order Blocks")
        self._axis.set_ylabel("Price")

    def annotate_order_blocks(
        self,
        candles: Sequence[Candle],
        order_blocks: Iterable[OrderBlock],
        *,
        label: str,
        bias: Bias,
        color: str,
    ) -> None:
        for order_block in order_blocks:
            if order_block.bias != bias:
                continue
            index = self._find_index(candles, order_block.timestamp)
            if index is None:
                continue
            color = "#1848cc" if not order_block.is_internal else "#3179f5"
            self._axis.fill_betweenx(
                y=[order_block.low, order_block.high],
                x1=index - 0.5,
                x2=len(candles),
                color=color,
                alpha=0.2,
            )
            y_position = order_block.high if bias == Bias.BULLISH else order_block.low
            self._axis.text(
                index,
                y_position,
                label,
                color=color,
                fontsize=9,
                ha="left",
                va="bottom" if bias == Bias.BULLISH else "top",
            )

    @staticmethod
    def _find_index(candles: Sequence[Candle], timestamp: datetime) -> int | None:
        for index, candle in enumerate(candles):
            if candle.timestamp == timestamp:
                return index
        return None

    def show(self) -> None:
        plt.tight_layout()
        plt.show()
