"""Console entry point for the stock order block detector."""
from __future__ import annotations

import argparse
from pathlib import Path

from .data import CandleLoader, Timeframe
from .detector import OrderBlockDetector
from .plotting import ChartRenderer


class Application:
    """Coordinates CLI execution."""

    def __init__(self, args: list[str] | None = None) -> None:
        self._args = self._parse_args(args)

    def run(self) -> None:
        timeframe = Timeframe.parse(self._args.timeframe)
        loader = CandleLoader(Path(self._args.data))
        candles = loader.load_resampled(timeframe)

        detector = OrderBlockDetector(candles)
        detection = detector.detect()

        renderer = ChartRenderer()
        renderer.render(
            candles,
            detection.swing_order_blocks,
            detection.internal_order_blocks,
            Path(self._args.output),
        )

    @staticmethod
    def _parse_args(args: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Detect order blocks and plot them.")
        parser.add_argument("--data", required=True, help="Path to a JSON file with OHLC data.")
        parser.add_argument(
            "--timeframe",
            default="1d",
            help="Timeframe to use (1d, 1w, 1m). Default is 1d.",
        )
        parser.add_argument(
            "--output",
            default="chart.png",
            help="File path where the chart will be written.",
        )
        return parser.parse_args(args)


def main() -> None:
    """Run the application."""

    Application().run()


if __name__ == "__main__":
    main()
