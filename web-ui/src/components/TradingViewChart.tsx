import React, { useEffect, useRef, useState } from 'react';

interface ChartData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartMetadata {
  symbol: string;
  interval: string;
  total_candles: number;
  date_range: {
    start: string;
    end: string;
  };
  price_range: {
    min: number;
    max: number;
    current: number;
  };
}

interface TradingViewChartProps {
  symbol?: string;
  interval?: string;
  days?: number;
  height?: number;
  showToolbar?: boolean;
}

const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol = 'BTCUSDT',
  interval = '1h',
  days = 30,
  height = 400,
  showToolbar = true
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [metadata, setMetadata] = useState<ChartMetadata | null>(null);

  // Fetch chart data from our API
  const fetchChartData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/charts/historical-data?symbol=${symbol}&interval=${interval}&days=${days}&format=tradingview`
      );
      
      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }

      setChartData(result.data);
      setMetadata(result.metadata);
      
    } catch (err) {
      console.error('Ошибка загрузки данных графика:', err);
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  };

  // Initialize chart
  const initChart = () => {
    if (!chartContainerRef.current || chartData.length === 0) return;

    try {
      // Clear previous chart
      if (chartRef.current) {
        chartRef.current.remove();
      }

      // Chart configuration
      const chartOptions = {
        width: chartContainerRef.current.clientWidth,
        height: height,
        layout: {
          background: { color: 'transparent' },
          textColor: '#DDD',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
        crosshair: {
          mode: 0,
        },
        rightPriceScale: {
          borderColor: '#485158',
        },
        timeScale: {
          borderColor: '#485158',
          timeVisible: true,
          secondsVisible: false,
        },
      };

      // Create lightweight chart (простая реализация без TradingView library)
      const chartContainer = chartContainerRef.current;
      chartContainer.innerHTML = '';

      // Create simple chart with Canvas
      const canvas = document.createElement('canvas');
      canvas.width = chartOptions.width;
      canvas.height = chartOptions.height;
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      canvas.style.backgroundColor = '#1A1A2E';
      chartContainer.appendChild(canvas);

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Draw simple candlestick chart
      drawCandlestickChart(ctx, chartData, canvas.width, canvas.height);
      
      chartRef.current = canvas;

    } catch (err) {
      console.error('Ошибка инициализации графика:', err);
      setError('Ошибка инициализации графика');
    }
  };

  // Simple candlestick drawing function
  const drawCandlestickChart = (ctx: CanvasRenderingContext2D, data: ChartData[], width: number, height: number) => {
    if (data.length === 0) return;

    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    // Calculate price range
    const prices = data.flatMap(d => [d.low, d.high]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;

    // Clear canvas
    ctx.fillStyle = '#1A1A2E';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = '#2B2B43';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i <= 5; i++) {
      const x = padding + (chartWidth / 5) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
      ctx.stroke();
    }

    // Draw price labels
    ctx.fillStyle = '#DDD';
    ctx.font = '12px Arial';
    ctx.textAlign = 'right';
    
    for (let i = 0; i <= 5; i++) {
      const price = maxPrice - (priceRange / 5) * i;
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(price.toFixed(2), padding - 5, y + 4);
    }

    // Draw candlesticks
    const candleWidth = Math.max(1, chartWidth / data.length * 0.8);
    
    data.forEach((candle, index) => {
      const x = padding + (chartWidth / data.length) * (index + 0.5);
      
      // Calculate y positions
      const openY = padding + ((maxPrice - candle.open) / priceRange) * chartHeight;
      const closeY = padding + ((maxPrice - candle.close) / priceRange) * chartHeight;
      const highY = padding + ((maxPrice - candle.high) / priceRange) * chartHeight;
      const lowY = padding + ((maxPrice - candle.low) / priceRange) * chartHeight;

      // Determine color (green for up, red for down)
      const isUp = candle.close > candle.open;
      ctx.fillStyle = isUp ? '#00D084' : '#F23645';
      ctx.strokeStyle = isUp ? '#00D084' : '#F23645';

      // Draw high-low line
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      // Draw candle body
      const bodyTop = Math.min(openY, closeY);
      const bodyHeight = Math.abs(closeY - openY);
      
      if (bodyHeight > 0) {
        ctx.fillRect(x - candleWidth/2, bodyTop, candleWidth, bodyHeight);
      } else {
        // Doji case (open === close)
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - candleWidth/2, openY);
        ctx.lineTo(x + candleWidth/2, openY);
        ctx.stroke();
      }
    });

    // Draw current price line
    if (data.length > 0) {
      const lastPrice = data[data.length - 1].close;
      const lastPriceY = padding + ((maxPrice - lastPrice) / priceRange) * chartHeight;
      
      ctx.strokeStyle = '#FFD700';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(padding, lastPriceY);
      ctx.lineTo(width - padding, lastPriceY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Price label
      ctx.fillStyle = '#FFD700';
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(`$${lastPrice.toFixed(2)}`, width - padding + 5, lastPriceY + 4);
    }
  };

  // Effect to fetch data when props change
  useEffect(() => {
    fetchChartData();
  }, [symbol, interval, days]);

  // Effect to initialize chart when data is loaded
  useEffect(() => {
    if (!loading && !error && chartData.length > 0) {
      const timer = setTimeout(initChart, 100);
      return () => clearTimeout(timer);
    }
  }, [loading, error, chartData, height]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (!loading && !error && chartData.length > 0) {
        const timer = setTimeout(initChart, 100);
        return () => clearTimeout(timer);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [loading, error, chartData]);

  return (
    <div className="w-full bg-gray-900 rounded-lg overflow-hidden">
      {/* Toolbar */}
      {showToolbar && (
        <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h3 className="text-white font-semibold">
                {symbol.replace('USDT', '/USDT')}
              </h3>
              {metadata && (
                <div className="flex items-center space-x-2 text-sm text-gray-400">
                  <span>{interval}</span>
                  <span>•</span>
                  <span>{metadata.total_candles} свечей</span>
                  <span>•</span>
                  <span className="text-green-400">
                    ${metadata.price_range.current.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
            <button
              onClick={fetchChartData}
              className="text-blue-400 hover:text-blue-300 text-sm"
              disabled={loading}
            >
              {loading ? '🔄' : '↻'} Обновить
            </button>
          </div>
        </div>
      )}

      {/* Chart Container */}
      <div className="relative" style={{ height: `${height}px` }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-2"></div>
              <p className="text-gray-400">Загрузка графика...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center text-red-400">
              <p className="mb-2">❌ Ошибка загрузки</p>
              <p className="text-sm text-gray-500">{error}</p>
              <button
                onClick={fetchChartData}
                className="mt-2 text-blue-400 hover:text-blue-300 text-sm"
              >
                Попробовать снова
              </button>
            </div>
          </div>
        )}

        <div
          ref={chartContainerRef}
          className="w-full h-full"
          style={{ display: loading || error ? 'none' : 'block' }}
        />
      </div>

      {/* Chart Info */}
      {metadata && !loading && !error && (
        <div className="bg-gray-800 px-4 py-2 border-t border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <div>
              <span>Диапазон: ${metadata.price_range.min.toFixed(2)} - ${metadata.price_range.max.toFixed(2)}</span>
            </div>
            <div>
              <span>Период: {new Date(metadata.date_range.start).toLocaleDateString()} - {new Date(metadata.date_range.end).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingViewChart; 