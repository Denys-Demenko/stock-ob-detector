"""Console entry point for the order block detector."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .chart import ChartRenderer
from .data import Dataset
from .detector import OrderBlockDetector
from .models import OrderBlock


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect order blocks and plot them.")
    parser.add_argument(
        "data_file",
        type=Path,
        help="Path to a JSON file containing OHLCV data.",
    )
    parser.add_argument(
        "--timeframe",
        default="1D",
        choices=["1D", "1W", "1M"],
        help="Timeframe to use for calculations.",
    )
    parser.add_argument(
        "--swing-length",
        type=int,
        default=5,
        help="Lookback length used for swing structure.",
    )
    parser.add_argument(
        "--internal-length",
        type=int,
        default=4,
        help="Lookback length used for internal structure.",
    )
    parser.add_argument(
        "--hide-internal",
        action="store_true",
        help="Hide internal order blocks on the chart.",
    )
    parser.add_argument(
        "--hide-swing",
        action="store_true",
        help="Hide swing order blocks on the chart.",
    )
    parser.add_argument(
        "--save-path",
        type=Path,
        help="If provided, save the resulting figure to this path instead of showing it.",
    )
    return parser.parse_args()


def run(
    data_file: Path,
    *,
    timeframe: str = "1D",
    swing_length: int = 5,
    internal_length: int = 4,
    hide_internal: bool = False,
    hide_swing: bool = False,
    save_path: Path | None = None,
) -> Iterable[OrderBlock]:
    dataset = Dataset.from_json(data_file, timeframe=timeframe)
    detector = OrderBlockDetector(
        swing_length=swing_length,
        internal_length=internal_length,
    )
    order_blocks = detector.process(dataset.bars)

    renderer = ChartRenderer()
    figure = renderer.plot(
        dataset.bars,
        order_blocks,
        show_internal=not hide_internal,
        show_swing=not hide_swing,
        title=f"Order Blocks ({timeframe})",
        show=save_path is None,
    )

    if save_path is not None:
        figure.savefig(save_path)
        from matplotlib import pyplot as plt

        plt.close(figure)

    return order_blocks


def main() -> None:
    args = parse_args()
    run(
        args.data_file,
        timeframe=args.timeframe,
        swing_length=args.swing_length,
        internal_length=args.internal_length,
        hide_internal=args.hide_internal,
        hide_swing=args.hide_swing,
        save_path=args.save_path,
    )


if __name__ == "__main__":
    main()
