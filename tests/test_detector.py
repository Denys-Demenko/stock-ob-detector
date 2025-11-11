"""Tests for order block detection."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from stock_ob_detector.data_loader import load_candles
from stock_ob_detector.detector import OrderBlockDetector
from stock_ob_detector.models import Bias


@pytest.fixture()
def gld_monthly_candles():
    dataset = load_candles(Path("data/GLD.json"))
    return dataset.resample("1M").candles


def test_monthly_order_blocks_cover_expected_dates(gld_monthly_candles):
    detector = OrderBlockDetector(gld_monthly_candles)
    detector.detect()

    swing_dates = {
        ob.timestamp.date()
        for ob in detector.swing_order_blocks
        if ob.bias == Bias.BULLISH
    }
    internal_dates = {
        ob.timestamp.date()
        for ob in detector.internal_order_blocks
        if ob.bias == Bias.BULLISH
    }

    expected_dates = {
        date(2015, 12, 31),
        date(2018, 8, 31),
        date(2023, 10, 31),
    }

    assert expected_dates.issubset(swing_dates | internal_dates)


def test_monthly_internal_bearish_order_blocks(gld_monthly_candles):
    detector = OrderBlockDetector(gld_monthly_candles)
    detector.detect()

    internal_dates = {
        ob.timestamp.date()
        for ob in detector.internal_order_blocks
        if ob.bias == Bias.BEARISH
    }

    expected_bearish = {
        date(2012, 10, 31),
        date(2014, 3, 31),
        date(2015, 1, 31),
        date(2022, 3, 31),
    }

    assert expected_bearish.issubset(internal_dates)
