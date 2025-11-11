"""SVG plotting helpers for visualising order blocks without extra deps."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List
from xml.etree import ElementTree as ET

from .models import Bias, Candle, OrderBlock

CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 600
MARGIN = 60
BODY_WIDTH_RATIO = 0.6


def plot_order_blocks(
    *,
    candles: Iterable[Candle],
    order_blocks: Iterable[OrderBlock],
    title: str,
    output_path: Path | None = None,
) -> Path:
    """Render a simple SVG chart with bullish order blocks highlighted."""

    candle_list = list(candles)
    if not candle_list:
        raise ValueError("No candles provided")

    output = output_path or Path("order_blocks.svg")

    root = ET.Element(
        "svg",
        attrib={
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(CANVAS_WIDTH),
            "height": str(CANVAS_HEIGHT),
            "viewBox": f"0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}",
        },
    )

    _draw_background(root)
    _draw_title(root, title)

    x_positions = _compute_x_positions(len(candle_list))
    price_to_y = _create_price_transform(candle_list)
    time_to_index = {candle.time: index for index, candle in enumerate(candle_list)}

    _draw_axes(root, candle_list, x_positions, price_to_y)
    _draw_candles(root, candle_list, x_positions, price_to_y)
    _draw_order_blocks(
        root,
        [block for block in order_blocks if block.bias is Bias.BULLISH],
        x_positions,
        price_to_y,
        time_to_index,
    )

    tree = ET.ElementTree(root)
    tree.write(output, encoding="utf-8", xml_declaration=True)
    return output


def _draw_background(root: ET.Element) -> None:
    ET.SubElement(
        root,
        "rect",
        attrib={
            "x": "0",
            "y": "0",
            "width": str(CANVAS_WIDTH),
            "height": str(CANVAS_HEIGHT),
            "fill": "#ffffff",
        },
    )


def _draw_title(root: ET.Element, title: str) -> None:
    ET.SubElement(
        root,
        "text",
        attrib={
            "x": str(CANVAS_WIDTH / 2),
            "y": str(MARGIN / 2),
            "text-anchor": "middle",
            "font-size": "20",
            "font-family": "Arial, sans-serif",
            "fill": "#1f2933",
        },
    ).text = title


def _compute_x_positions(length: int) -> List[float]:
    chart_width = CANVAS_WIDTH - 2 * MARGIN
    if length == 1:
        return [MARGIN + chart_width / 2]

    step = chart_width / (length - 1)
    return [MARGIN + index * step for index in range(length)]


def _create_price_transform(candles: List[Candle]):
    min_price = min(candle.low for candle in candles)
    max_price = max(candle.high for candle in candles)
    chart_height = CANVAS_HEIGHT - 2 * MARGIN

    def transform(price: float) -> float:
        if max_price == min_price:
            return CANVAS_HEIGHT / 2
        scale = (price - min_price) / (max_price - min_price)
        return CANVAS_HEIGHT - MARGIN - (scale * chart_height)

    return transform


def _draw_axes(
    root: ET.Element,
    candles: List[Candle],
    x_positions: List[float],
    price_to_y,
) -> None:
    min_price = min(candle.low for candle in candles)
    max_price = max(candle.high for candle in candles)

    ET.SubElement(
        root,
        "line",
        attrib={
            "x1": str(MARGIN),
            "y1": str(CANVAS_HEIGHT - MARGIN),
            "x2": str(CANVAS_WIDTH - MARGIN / 2),
            "y2": str(CANVAS_HEIGHT - MARGIN),
            "stroke": "#d2d6dc",
            "stroke-width": "1",
        },
    )
    ET.SubElement(
        root,
        "line",
        attrib={
            "x1": str(MARGIN),
            "y1": str(MARGIN / 2),
            "x2": str(MARGIN),
            "y2": str(CANVAS_HEIGHT - MARGIN),
            "stroke": "#d2d6dc",
            "stroke-width": "1",
        },
    )

    for fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
        price = min_price + (max_price - min_price) * fraction
        y = price_to_y(price)
        ET.SubElement(
            root,
            "line",
            attrib={
                "x1": str(MARGIN),
                "y1": str(y),
                "x2": str(CANVAS_WIDTH - MARGIN / 2),
                "y2": str(y),
                "stroke": "#f1f5f9",
                "stroke-width": "0.5",
            },
        )
        ET.SubElement(
            root,
            "text",
            attrib={
                "x": str(MARGIN - 10),
                "y": str(y + 4),
                "text-anchor": "end",
                "font-size": "11",
                "font-family": "Arial, sans-serif",
                "fill": "#4b5563",
            },
        ).text = f"{price:.2f}"

    label_step = max(1, len(candles) // 8)
    for index in range(0, len(candles), label_step):
        candle = candles[index]
        x = x_positions[index]
        ET.SubElement(
            root,
            "text",
            attrib={
                "x": str(x),
                "y": str(CANVAS_HEIGHT - MARGIN + 20),
                "text-anchor": "middle",
                "font-size": "11",
                "font-family": "Arial, sans-serif",
                "fill": "#4b5563",
            },
        ).text = candle.time.strftime("%Y-%m")


def _draw_candles(
    root: ET.Element,
    candles: List[Candle],
    x_positions: List[float],
    price_to_y,
) -> None:
    body_half_width = (x_positions[1] - x_positions[0]) * BODY_WIDTH_RATIO / 2 if len(x_positions) > 1 else 10

    for candle, x in zip(candles, x_positions):
        y_open = price_to_y(candle.open)
        y_close = price_to_y(candle.close)
        y_high = price_to_y(candle.high)
        y_low = price_to_y(candle.low)
        color = "#089981" if candle.close >= candle.open else "#F23645"

        ET.SubElement(
            root,
            "line",
            attrib={
                "x1": str(x),
                "y1": str(y_high),
                "x2": str(x),
                "y2": str(y_low),
                "stroke": color,
                "stroke-width": "1",
            },
        )

        top = min(y_open, y_close)
        height = max(abs(y_close - y_open), 1.0)
        ET.SubElement(
            root,
            "rect",
            attrib={
                "x": str(x - body_half_width),
                "y": str(top),
                "width": str(body_half_width * 2),
                "height": str(height),
                "fill": color,
                "stroke": color,
            },
        )


def _draw_order_blocks(
    root: ET.Element,
    order_blocks: List[OrderBlock],
    x_positions: List[float],
    price_to_y,
    time_to_index: dict[datetime, int],
) -> None:
    if not order_blocks:
        return

    end_index = len(x_positions) - 1
    end_x = x_positions[end_index] + (x_positions[1] - x_positions[0]) / 2 if len(x_positions) > 1 else x_positions[end_index] + 10

    for block in order_blocks:
        start_index = time_to_index.get(block.time)
        if start_index is None:
            continue

        start_x = x_positions[start_index] - (x_positions[1] - x_positions[0]) / 2 if len(x_positions) > 1 else x_positions[start_index] - 10
        top = price_to_y(block.high)
        bottom = price_to_y(block.low)
        color = "#3179f5" if block.internal else "#1848cc"

        ET.SubElement(
            root,
            "rect",
            attrib={
                "x": str(start_x),
                "y": str(top),
                "width": str(end_x - start_x),
                "height": str(bottom - top),
                "fill": color,
                "fill-opacity": "0.25",
                "stroke": color,
                "stroke-width": "1",
            },
        )

        ET.SubElement(
            root,
            "text",
            attrib={
                "x": str(start_x + 6),
                "y": str(top - 6),
                "text-anchor": "start",
                "font-size": "12",
                "font-family": "Arial, sans-serif",
                "fill": color,
            },
        ).text = block.label
