import { useEffect, useMemo, useRef, useState } from 'react';
import { CandlestickSeries, createChart } from 'lightweight-charts';

import HighlightRectangle from './HighlightRectangle';

const CANDLE_COUNT = 120;

function generateRandomCandles() {
  const candles = [];
  let time = Math.floor(Date.now() / 1000) - CANDLE_COUNT * 60;
  let open = 100 + Math.random() * 20;

  for (let i = 0; i < CANDLE_COUNT; i += 1) {
    const high = open + Math.random() * 5;
    const low = open - Math.random() * 5;
    const close = low + Math.random() * (high - low);

    candles.push({ time, open, high, low, close });
    open = close + (Math.random() - 0.5) * 2;
    time += 60; // one minute step
  }

  return candles;
}

export default function App() {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [chartApi, setChartApi] = useState(null);
  const [seriesApi, setSeriesApi] = useState(null);
  const data = useMemo(() => generateRandomCandles(), []);
  const highlightIndex = useMemo(() => Math.floor(data.length / 2), [data]);

  useEffect(() => {
    if (!chartContainerRef.current) {
      return undefined;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#0b0e1a' },
        textColor: '#d1d4dc'
      },
      localization: {
        locale: 'en-US'
      },
      rightPriceScale: {
        borderVisible: false
      },
      timeScale: {
        borderVisible: false
      },
      grid: {
        vertLines: { color: '#1f2943' },
        horzLines: { color: '#1f2943' }
      }
    });

    chartRef.current = chart;
    setChartApi(chart);

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350'
    });

    candleSeries.setData(data);
    setSeriesApi(candleSeries);

    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current?.clientWidth ?? 0,
        height: chartContainerRef.current?.clientHeight ?? 0
      });
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="app">
      <header>
        <h1>Случайные свечи для тикера</h1>
        <p>Тестовый график на базе TradingView Lightweight Charts</p>
      </header>
      <div className="chart-wrapper" ref={chartContainerRef}>
        {chartApi && seriesApi && chartContainerRef.current ? (
          <HighlightRectangle
            chart={chartApi}
            series={seriesApi}
            container={chartContainerRef.current}
            data={data}
            targetIndex={highlightIndex}
            extendLeft={false}
            extendRight
            fillColor="rgba(59, 130, 246, 0.25)"
            borderColor="rgba(59, 130, 246, 0.8)"
          />
        ) : null}
      </div>
    </div>
  );
}
