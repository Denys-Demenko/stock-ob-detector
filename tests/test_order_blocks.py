from pathlib import Path

from stock_ob_detector import Dataset, OrderBlockDetector, Bias


DATA_PATH = Path("data/GLD.json")
EXPECTED_MONTHS = {
    (2015, 12),
    (2018, 8),
    (2023, 10),
}


def extract_months(order_blocks, *, internal: bool) -> set[tuple[int, int]]:
    return {
        (block.start_time.year, block.start_time.month)
        for block in order_blocks
        if block.bias is Bias.BULLISH and block.internal is internal
    }


def test_monthly_order_blocks_cover_expected_periods() -> None:
    dataset = Dataset.from_json(DATA_PATH, timeframe="1M")
    detector = OrderBlockDetector()
    order_blocks = detector.process(dataset.bars)

    swing_months = extract_months(order_blocks, internal=False)
    internal_months = extract_months(order_blocks, internal=True)

    assert EXPECTED_MONTHS.issubset(swing_months)
    assert EXPECTED_MONTHS.issubset(internal_months)
