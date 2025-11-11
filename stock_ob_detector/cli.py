"""Console application entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .data_loader import CandleData, load_candles
from .detector import OrderBlockDetector
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
    print("Detected bullish swing order blocks:")
    for timestamp, low, high in summary["swing"]:
        print(f"  {timestamp:%Y-%m-%d} | low={low:.2f} high={high:.2f}")

    print("Detected bullish internal order blocks:")
    for timestamp, low, high in summary["internal"]:
        print(f"  {timestamp:%Y-%m-%d} | low={low:.2f} high={high:.2f}")

    if args.no_plot:
        return

    plotter = ChartPlotter()
    plotter.plot_candles(resampled.candles)
    plotter.annotate_order_blocks(
        resampled.candles,
        detector.swing_order_blocks,
        label="Bull OB",
    )
    plotter.annotate_order_blocks(
        resampled.candles,
        detector.internal_order_blocks,
        label="Internal Bull OB",
    )
    plotter.show()


if __name__ == "__main__":  # pragma: no cover - manual execution
    run()
