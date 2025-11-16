"""Console application entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .data_loader import CandleData, load_candles
from .detector import OrderBlockDetector
from .models import Bias
from .plotter import ChartPlotter


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect and plot order blocks")
    parser.add_argument("data", type=Path, help="Path to OHLC JSON file")
    parser.add_argument(
        "--timeframe",
        default="1D",
        choices=["1D", "1W", "1M"],
        help="Target timeframe for analysis",
    )
    parser.add_argument(
        "--swing-length",
        type=int,
        default=50,
        help="Number of periods for swing structure",
    )
    parser.add_argument(
        "--internal-length",
        type=int,
        default=5,
        help="Number of periods for internal structure",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip matplotlib visualisation",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    dataset = load_candles(args.data)
    resampled = dataset.resample(args.timeframe)

    detector = OrderBlockDetector(
        resampled.candles,
        swing_length=args.swing_length,
        internal_length=args.internal_length,
    )
    detector.detect()

    summary = detector.summarize()
    _print_summary("swing", "bullish", summary, Bias.BULLISH)
    _print_summary("swing", "bearish", summary, Bias.BEARISH)
    _print_summary("internal", "bullish", summary, Bias.BULLISH)
    _print_summary("internal", "bearish", summary, Bias.BEARISH)

    if args.no_plot:
        return

    plotter = ChartPlotter()
    plotter.plot_candles(resampled.candles)
    plotter.annotate_order_blocks(
        resampled.candles,
        detector.swing_order_blocks,
        label="Bull OB",
        bias=Bias.BULLISH,
        color="#1848cc",
    )
    plotter.annotate_order_blocks(
        resampled.candles,
        detector.swing_order_blocks,
        label="Bear OB",
        bias=Bias.BEARISH,
        color="#b22833",
    )
    plotter.annotate_order_blocks(
        resampled.candles,
        detector.internal_order_blocks,
        label="Internal Bull OB",
        bias=Bias.BULLISH,
        color="#3179f5",
    )
    plotter.annotate_order_blocks(
        resampled.candles,
        detector.internal_order_blocks,
        label="Internal Bear OB",
        bias=Bias.BEARISH,
        color="#f77c80",
    )
    plotter.show()


def _print_summary(
    category: str,
    description: str,
    summary: dict[str, list[tuple]],
    bias: Bias,
) -> None:
    print(f"Detected {description} {category} order blocks:")
    entries = [entry for entry in summary[category] if entry[3] == bias]
    if not entries:
        print("  (none)")
        return
    for timestamp, low, high, _ in entries:
        print(f"  {timestamp:%Y-%m-%d} | low={low:.2f} high={high:.2f}")


if __name__ == "__main__":  # pragma: no cover - manual execution
    run()
