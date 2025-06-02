import React, { useEffect, useRef, useState } from 'react';
import { 
  createChart, 
  IChartApi, 
  CrosshairMode,
  Time
} from 'lightweight-charts';

interface CandlestickData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradePoint {
  time: number;
  price: number;
  type: 'entry' | 'exit' | 'stop_loss' | 'take_profit';
  side: 'buy' | 'sell';
  id: string;
  pnl?: number;
  size?: number;
}

interface IndicatorData {
  time: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  bb_upper?: number;
  bb_lower?: number;
  bb_middle?: number;
  support?: number;
  resistance?: number;
}

interface TradingChartProps {
  symbol: string;
  data: CandlestickData[];
  indicators?: IndicatorData[];
  trades?: TradePoint[];
  positions?: any[];
  onCandleClick?: (time: number, price: number) => void;
  className?: string;
}

const TradingChart: React.FC<TradingChartProps> = ({
  symbol,
  data,
  indicators = [],
  trades = [],
  positions = [],
  onCandleClick,
  className = ''
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [showIndicators, setShowIndicators] = useState({
    rsi: false,
    macd: false,
    bollinger: true,
    volume: true,
    levels: false
  });

  console.log('TradingChart props:', {
    symbol,
    dataLength: data?.length,
    indicatorsLength: indicators?.length,
    tradesLength: trades?.length,
    positionsLength: positions?.length
  });

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      console.log('Chart container or data not available');
      return;
    }

    // Безопасно удаляем предыдущий график
    if (chartRef.current) {
      try {
        chartRef.current.remove();
      } catch (e) {
        console.warn('Error removing chart:', e);
      }
      chartRef.current = null;
    }

    // Создаем новый график
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#1f2937' },
        textColor: '#ffffff',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#485563' },
      timeScale: { 
        borderColor: '#485563',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    try {
      // Основные свечи
      const candlestickSeries = (chart as any).addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderDownColor: '#ef4444',
        borderUpColor: '#10b981',
        wickDownColor: '#ef4444',
        wickUpColor: '#10b981',
      });

      const candleData = data.map(candle => ({
        time: candle.time as Time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      }));
      candlestickSeries.setData(candleData);

      // Bollinger Bands (полупрозрачные)
      if (showIndicators.bollinger && indicators.length > 0) {
        const bbUpperData = indicators
          .filter(ind => ind.bb_upper !== undefined)
          .map(ind => ({ time: ind.time as Time, value: ind.bb_upper! }));

        const bbLowerData = indicators
          .filter(ind => ind.bb_lower !== undefined)
          .map(ind => ({ time: ind.time as Time, value: ind.bb_lower! }));

        const bbMiddleData = indicators
          .filter(ind => ind.bb_middle !== undefined)
          .map(ind => ({ time: ind.time as Time, value: ind.bb_middle! }));

        if (bbUpperData.length > 0) {
          const bbUpperSeries = (chart as any).addLineSeries({
            color: 'rgba(139, 92, 246, 0.3)',
            lineWidth: 1,
            lineStyle: 2,
            lastValueVisible: false,
            priceLineVisible: false
          });
          bbUpperSeries.setData(bbUpperData);
        }

        if (bbLowerData.length > 0) {
          const bbLowerSeries = (chart as any).addLineSeries({
            color: 'rgba(139, 92, 246, 0.3)',
            lineWidth: 1,
            lineStyle: 2,
            lastValueVisible: false,
            priceLineVisible: false
          });
          bbLowerSeries.setData(bbLowerData);
        }

        if (bbMiddleData.length > 0) {
          const bbMiddleSeries = (chart as any).addLineSeries({
            color: 'rgba(99, 102, 241, 0.4)',
            lineWidth: 1,
            lastValueVisible: false,
            priceLineVisible: false
          });
          bbMiddleSeries.setData(bbMiddleData);
        }
      }

      // RSI как линия внизу графика (масштабированная к цене)
      if (showIndicators.rsi && indicators.length > 0) {
        const rsiData = indicators
          .filter(ind => ind.rsi !== undefined)
          .map(ind => {
            const currentPrice = data.find(d => d.time === ind.time)?.close || data[data.length - 1]?.close || 50000;
            // Масштабируем RSI (0-100) к 5% от текущей цены внизу графика
            const scaledRsi = currentPrice * 0.9 + (currentPrice * 0.1 * (ind.rsi! / 100));
            return { time: ind.time as Time, value: scaledRsi };
          });

        if (rsiData.length > 0) {
          const rsiSeries = (chart as any).addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
            lastValueVisible: false,
            priceLineVisible: false
          });
          rsiSeries.setData(rsiData);
        }
      }

      // MACD как столбчатая диаграмма внизу
      if (showIndicators.macd && indicators.length > 0) {
        const macdData = indicators
          .filter(ind => ind.macd !== undefined)
          .map(ind => {
            const currentPrice = data.find(d => d.time === ind.time)?.close || data[data.length - 1]?.close || 50000;
            // Масштабируем MACD к нижней части графика
            const scaledMacd = currentPrice * 0.85 + (ind.macd! * currentPrice * 0.001);
            return { 
              time: ind.time as Time, 
              value: scaledMacd,
              color: (ind.macd! > 0) ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'
            };
          });

        if (macdData.length > 0) {
          const macdSeries = (chart as any).addHistogramSeries({
            lastValueVisible: false,
            priceLineVisible: false
          });
          macdSeries.setData(macdData);
        }
      }

      // Объемы внизу как гистограмма
      if (showIndicators.volume) {
        const volumeData = data.map(candle => {
          const currentPrice = candle.close;
          // Масштабируем объем к нижней части графика (5-15% от цены)
          const maxVolume = Math.max(...data.map(d => d.volume));
          const scaledVolume = currentPrice * 0.8 + (candle.volume / maxVolume) * currentPrice * 0.15;
          return {
            time: candle.time as Time,
            value: scaledVolume,
            color: candle.close > candle.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
          };
        });

        const volumeSeries = (chart as any).addHistogramSeries({
          lastValueVisible: false,
          priceLineVisible: false
        });
        volumeSeries.setData(volumeData);
      }

      // Торговые маркеры
      if (trades.length > 0) {
        const markers = trades.map(trade => ({
          time: trade.time as Time,
          position: 'belowBar' as const,
          color: trade.side === 'buy' ? '#10b981' : '#ef4444',
          shape: 'arrowUp' as const,
          text: `${trade.side.toUpperCase()}`,
          size: 1,
        }));
        candlestickSeries.setMarkers(markers);
      }

    } catch (error) {
      console.error('Error setting up chart:', error);
    }

    // Обработчик изменения размера
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        try {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
          });
        } catch (e) {
          console.warn('Error resizing chart:', e);
        }
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        try {
          chartRef.current.remove();
        } catch (e) {
          console.warn('Error removing chart on cleanup:', e);
        }
        chartRef.current = null;
      }
    };
  }, [data, indicators, trades, showIndicators]);

  const toggleIndicator = (indicator: keyof typeof showIndicators) => {
    setShowIndicators(prev => ({ ...prev, [indicator]: !prev[indicator] }));
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Упрощенная панель управления */}
      <div className="bg-gray-800 rounded-lg p-4 mb-4">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-white">График {symbol}</h3>
            
            {/* Таймфреймы */}
            <div className="flex gap-1">
              {['1m', '5m', '15m', '1h', '4h', '1d'].map(tf => (
                <button
                  key={tf}
                  onClick={() => setSelectedTimeframe(tf)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    selectedTimeframe === tf
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Индикаторы */}
          <div className="flex gap-2 text-sm">
            <button
              onClick={() => toggleIndicator('bollinger')}
              className={`px-3 py-1 rounded transition-colors ${
                showIndicators.bollinger
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              BB
            </button>
            <button
              onClick={() => toggleIndicator('volume')}
              className={`px-3 py-1 rounded transition-colors ${
                showIndicators.volume
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              VOL
            </button>
            <button
              onClick={() => toggleIndicator('rsi')}
              className={`px-3 py-1 rounded transition-colors ${
                showIndicators.rsi
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              RSI
            </button>
            <button
              onClick={() => toggleIndicator('macd')}
              className={`px-3 py-1 rounded transition-colors ${
                showIndicators.macd
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              MACD
            </button>
          </div>
        </div>
      </div>

      {/* Основной график */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div ref={chartContainerRef} className="w-full" />
      </div>

      {/* Компактная статистика */}
      {(trades.length > 0 || positions.length > 0) && (
        <div className="bg-gray-800 rounded-lg p-4 mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {trades.length > 0 && (
              <>
                <div>
                  <div className="text-gray-400">Сделок</div>
                  <div className="text-white font-semibold">{trades.filter(t => t.type === 'entry').length}</div>
                </div>
                <div>
                  <div className="text-gray-400">P&L</div>
                  <div className={`font-semibold ${
                    trades.reduce((sum, t) => sum + (t.pnl || 0), 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trades.reduce((sum, t) => sum + (t.pnl || 0), 0).toFixed(2)}
                  </div>
                </div>
              </>
            )}
            {positions.length > 0 && (
              <>
                <div>
                  <div className="text-gray-400">Позиций</div>
                  <div className="text-white font-semibold">{positions.length}</div>
                </div>
                <div>
                  <div className="text-gray-400">Текущий P&L</div>
                  <div className="text-blue-400 font-semibold">
                    {positions.reduce((sum, p) => sum + (p.pnl || 0), 0).toFixed(2)}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingChart; 