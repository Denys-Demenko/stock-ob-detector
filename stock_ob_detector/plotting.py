"""Plotting utilities for the console application."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .models import Candle, OrderBlock


@dataclass(slots=True)
class PlotConfig:
    """Configuration for chart rendering."""

    width: float = 16
    height: float = 9
    candle_width: float = 0.6


class ChartRenderer:
    """Render candlestick charts with order block overlays."""

    def __init__(self, config: PlotConfig | None = None) -> None:
        self._config = config or PlotConfig()

    def render(
        self,
        candles: Sequence[Candle],
        swing_order_blocks: Iterable[OrderBlock],
        internal_order_blocks: Iterable[OrderBlock],
        output: Path,
    ) -> None:
        figure, axis = plt.subplots(figsize=(self._config.width, self._config.height))
        self._plot_candles(axis, candles)
        self._plot_order_blocks(axis, swing_order_blocks, color="#1848cc", label="Bull OB")
        self._plot_order_blocks(
            axis,
            internal_order_blocks,
            color="#3179f5",
            label="Internal Bull OB",
            alpha=0.4,
        )

        axis.set_title("Order Blocks")
        axis.set_ylabel("Price")
        axis.grid(True, which="both", linestyle="--", alpha=0.3)
        axis.legend(loc="upper left")
        figure.autofmt_xdate()
        figure.tight_layout()
        figure.savefig(output)
        plt.close(figure)

    def _plot_candles(self, axis, candles: Sequence[Candle]) -> None:
        converter = mdates.DateFormatter("%Y-%m-%d")
        axis.xaxis.set_major_formatter(converter)

        dates = [mdates.date2num(candle.timestamp) for candle in candles]
        for index, candle in enumerate(candles):
            color = "#089981" if candle.close >= candle.open else "#F23645"
            axis.vlines(dates[index], candle.low, candle.high, color=color, linewidth=1)
            body_low = min(candle.open, candle.close)
            body_height = abs(candle.close - candle.open)
            rect = Rectangle(
                (dates[index] - self._config.candle_width / 2, body_low),
                self._config.candle_width,
                body_height if body_height else 0.0001,
                edgecolor=color,
                facecolor=color,
                alpha=0.8,
            )
            axis.add_patch(rect)

    def _plot_order_blocks(
        self,
        axis,
        order_blocks: Iterable[OrderBlock],
        *,
        color: str,
        label: str,
        alpha: float = 0.2,
    ) -> None:
        for block in order_blocks:
            start = mdates.date2num(block.start)
            width = 0.8
            rect = Rectangle(
                (start - width / 2, block.low),
                width,
                block.high - block.low,
                edgecolor=color,
                facecolor=color,
                alpha=alpha,
                label=label,
            )
            axis.add_patch(rect)
            axis.text(start, block.high, label, color=color, fontsize=8, verticalalignment="bottom")
            label = "_nolegend_"
