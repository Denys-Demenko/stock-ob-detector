"""Tests for the order block detector."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from stock_ob_detector.data import CandleLoader, Timeframe
from stock_ob_detector.detector import OrderBlockDetector
from stock_ob_detector.models import Bias


def test_monthly_gld_bullish_order_blocks() -> None:
    """GLD monthly data should contain known bullish swing order blocks."""

    loader = CandleLoader(Path("data/GLD.json"))
    candles = loader.load_resampled(Timeframe.parse("1m"))
    detector = OrderBlockDetector(candles)
    result = detector.detect()

    bullish_blocks = {
        block.start.date()
        for block in result.all_blocks()
        if block.bias is Bias.BULLISH
    }
    expected = {
        datetime(2015, 12, 31).date(),
        datetime(2018, 8, 31).date(),
        datetime(2023, 10, 31).date(),
    }

    missing = expected - bullish_blocks
    assert not missing, f"Missing expected order blocks for months: {sorted(missing)}"
