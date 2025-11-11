"""Console entry point for detecting and plotting order blocks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .data import load_candles
from .detector import OrderBlockDetector, Timeframe
from .plotting import plot_order_blocks


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect bullish order blocks")
    parser.add_argument(
        "data_file",
        type=Path,
        help="Path to a JSON file containing OHLC candles",
    )
    parser.add_argument(
        "--timeframe",
        choices=[tf.value for tf in Timeframe],
        default=Timeframe.ONE_DAY.value,
        help="Aggregation timeframe for the analysis",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file path where the chart will be saved",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    timeframe = Timeframe(args.timeframe)
    loaded = load_candles(args.data_file, timeframe=timeframe)

    detector = OrderBlockDetector()
    order_blocks = detector.process(loaded.candles)

    title = f"{loaded.ticker} — {timeframe.value} order blocks"
    output_file = plot_order_blocks(
        candles=loaded.candles,
        order_blocks=order_blocks,
        title=title,
        output_path=args.output,
    )
    print(f"Chart saved to {output_file}")


if __name__ == "__main__":
    main()
