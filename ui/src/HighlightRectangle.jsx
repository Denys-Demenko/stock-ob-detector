import { useEffect, useRef } from 'react';

export default function HighlightRectangle({
  chart,
  series,
  container,
  data,
  targetIndex,
  extendLeft = false,
  extendRight = true,
  fillColor = 'rgba(59, 130, 246, 0.25)',
  borderColor = 'rgba(59, 130, 246, 0.8)'
}) {
  const rectangleRef = useRef(null);

  useEffect(() => {
    if (!chart || !series || !container || typeof targetIndex !== 'number') {
      return undefined;
    }

    const targetCandle = data?.[targetIndex];
    if (!targetCandle) {
      return undefined;
    }

    const rectangle = document.createElement('div');
    rectangle.className = 'chart-highlight';
    rectangle.style.backgroundColor = fillColor;
    rectangle.style.borderColor = borderColor;
    container.appendChild(rectangle);
    rectangleRef.current = rectangle;

    const updateRectanglePosition = () => {
      if (!rectangleRef.current) {
        return;
      }

      const xStart = chart.timeScale().timeToCoordinate(targetCandle.time);
      const top = series.priceToCoordinate(targetCandle.high);
      const bottom = series.priceToCoordinate(targetCandle.low);

      if (xStart == null || top == null || bottom == null) {
        rectangleRef.current.style.display = 'none';
        return;
      }

      rectangleRef.current.style.display = 'block';
      const containerWidth = container.clientWidth;
      const leftEdge = extendLeft ? 0 : Math.max(0, xStart);

      let rightEdge;
      if (extendRight) {
        rightEdge = containerWidth;
      } else {
        const nextCandle = data?.[targetIndex + 1];
        const prevCandle = data?.[targetIndex - 1];
        const nextCoord = nextCandle ? chart.timeScale().timeToCoordinate(nextCandle.time) : null;
        const prevCoord = prevCandle ? chart.timeScale().timeToCoordinate(prevCandle.time) : null;

        if (nextCoord != null) {
          rightEdge = nextCoord;
        } else if (prevCoord != null) {
          rightEdge = xStart + Math.abs(xStart - prevCoord);
        } else {
          rightEdge = xStart + 8;
        }
      }

      rightEdge = Math.min(containerWidth, Math.max(rightEdge ?? leftEdge, leftEdge));
      const width = Math.max(0, rightEdge - leftEdge);

      rectangleRef.current.style.left = `${leftEdge}px`;
      rectangleRef.current.style.width = `${width}px`;
      rectangleRef.current.style.top = `${Math.min(top, bottom)}px`;
      rectangleRef.current.style.height = `${Math.abs(top - bottom)}px`;
    };

    const timeScale = chart.timeScale();
    const visibleRangeHandler = () => updateRectanglePosition();
    const sizeHandler = () => updateRectanglePosition();
    const resizeHandler = () => updateRectanglePosition();

    updateRectanglePosition();

    timeScale.subscribeVisibleLogicalRangeChange(visibleRangeHandler);
    timeScale.subscribeSizeChange(sizeHandler);
    window.addEventListener('resize', resizeHandler);

    return () => {
      window.removeEventListener('resize', resizeHandler);
      timeScale.unsubscribeVisibleLogicalRangeChange(visibleRangeHandler);
      timeScale.unsubscribeSizeChange(sizeHandler);
      rectangleRef.current?.remove();
      rectangleRef.current = null;
    };
  }, [
    chart,
    series,
    container,
    data,
    targetIndex,
    extendLeft,
    extendRight,
    fillColor,
    borderColor
  ]);

  return null;
}
