"""Visualization utilities for detected order blocks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from .models import Bar, Bias, OrderBlock


@dataclass
class ChartRenderer:
    """Render OHLC data and highlight order blocks."""

    width: int = 12
    height: int = 6

    def plot(
        self,
        bars: Sequence[Bar],
        order_blocks: Iterable[OrderBlock],
        *,
        show_internal: bool = True,
        show_swing: bool = True,
        title: str = "Order Blocks",
        show: bool = True,
    ):
        fig, ax = plt.subplots(figsize=(self.width, self.height))

        times = [mdates.date2num(bar.timestamp) for bar in bars]
        opens = [bar.open for bar in bars]
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        closes = [bar.close for bar in bars]

        for idx, bar_time in enumerate(times):
            color = "#089981" if closes[idx] >= opens[idx] else "#F23645"
            body_low = min(opens[idx], closes[idx])
            body_high = max(opens[idx], closes[idx])
            ax.add_line(Line2D([bar_time, bar_time], [lows[idx], highs[idx]], color=color))
            ax.add_patch(
                Rectangle(
                    (bar_time - 0.3, body_low),
                    0.6,
                    body_high - body_low if body_high - body_low else 0.01,
                    edgecolor=color,
                    facecolor=color,
                    alpha=0.6,
                )
            )

        last_time = times[-1] if times else None
        for order_block in order_blocks:
            if order_block.internal and not show_internal:
                continue
            if not order_block.internal and not show_swing:
                continue
            if order_block.bias is not Bias.BULLISH:
                continue

            start = mdates.date2num(order_block.start_time)
            end = last_time if last_time is not None else start
            width = max(end - start, 0.2)
            rect = Rectangle(
                (start, order_block.low),
                width,
                order_block.high - order_block.low,
                linewidth=1.0,
                edgecolor="#2157f3" if order_block.internal else "#1848cc",
                facecolor="#3179f5" if order_block.internal else "#1848cc",
                alpha=0.3 if order_block.internal else 0.2,
            )
            ax.add_patch(rect)
            ax.text(
                start,
                order_block.high,
                order_block.label(),
                color="#2157f3" if order_block.internal else "#1848cc",
                fontsize=8,
                verticalalignment="bottom",
            )

        ax.set_title(title)
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.xaxis_date()
        fig.autofmt_xdate()
        plt.tight_layout()
        if show:
            plt.show()
        return fig
