"""Integration tests for order block detection."""

from pathlib import Path

from stock_ob_detector.data import load_candles
from stock_ob_detector.detector import OrderBlockDetector, Timeframe
from stock_ob_detector.models import Bias


def test_monthly_gld_bullish_order_blocks():
    data_path = Path("data/GLD.json")
    loaded = load_candles(data_path, timeframe=Timeframe.ONE_MONTH)

    detector = OrderBlockDetector()
    order_blocks = detector.process(loaded.candles)

    bullish_blocks = [
        block for block in order_blocks if block.bias is Bias.BULLISH
    ]
    detected_months = {block.time.strftime("%Y-%m") for block in bullish_blocks}

    assert {"2015-12", "2018-08", "2023-10"}.issubset(detected_months)
