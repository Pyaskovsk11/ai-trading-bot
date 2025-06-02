import React, { useState, useEffect } from 'react';
import TradingViewChart from '../components/TradingViewChart';

interface Symbol {
  symbol: string;
  name: string;
  category: string;
}

interface Interval {
  value: string;
  name: string;
  seconds: number;
}

// Default intervals
const defaultIntervals: Record<string, Interval> = {
  '1m': { value: '1m', name: '1 минута', seconds: 60 },
  '5m': { value: '5m', name: '5 минут', seconds: 300 },
  '15m': { value: '15m', name: '15 минут', seconds: 900 },
  '30m': { value: '30m', name: '30 минут', seconds: 1800 },
  '1h': { value: '1h', name: '1 час', seconds: 3600 },
  '4h': { value: '4h', name: '4 часа', seconds: 14400 },
  '1d': { value: '1d', name: '1 день', seconds: 86400 },
};

// Default symbols
const defaultSymbols: Symbol[] = [
  { symbol: 'BTCUSDT', name: 'Bitcoin', category: 'Major' },
  { symbol: 'ETHUSDT', name: 'Ethereum', category: 'Major' },
  { symbol: 'BNBUSDT', name: 'Binance Coin', category: 'Major' },
  { symbol: 'SOLUSDT', name: 'Solana', category: 'Major' },
  { symbol: 'ADAUSDT', name: 'Cardano', category: 'Major' },
];

const Charts: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedInterval, setSelectedInterval] = useState('1h');
  const [selectedDays, setSelectedDays] = useState(30);
  const [symbols, setSymbols] = useState<Symbol[]>(defaultSymbols);
  const [intervals, setIntervals] = useState<Record<string, Interval>>(defaultIntervals);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [multipleSymbols, setMultipleSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']);
  const [showMultiple, setShowMultiple] = useState(false);

  // Fetch available symbols and intervals
  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        
        // Fetch symbols
        const symbolsResponse = await fetch('http://localhost:8000/api/v1/charts/symbols-list');
        if (!symbolsResponse.ok) {
          throw new Error('Не удалось загрузить список символов');
        }
        const symbolsData = await symbolsResponse.json();
        
        if (symbolsData.status === 'success' && Array.isArray(symbolsData.symbols)) {
          setSymbols(symbolsData.symbols);
        }

        // Fetch intervals
        const intervalsResponse = await fetch('http://localhost:8000/api/v1/charts/supported-intervals');
        if (!intervalsResponse.ok) {
          throw new Error('Не удалось загрузить список интервалов');
        }
        const intervalsData = await intervalsResponse.json();
        
        if (intervalsData.status === 'success' && intervalsData.intervals) {
          setIntervals(intervalsData.intervals);
          if (intervalsData.default) {
            setSelectedInterval(intervalsData.default);
          }
        }

      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        setError(error instanceof Error ? error.message : 'Произошла ошибка при загрузке данных');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Group symbols by category
  const symbolsByCategory = symbols.reduce((acc, symbol) => {
    if (!acc[symbol.category]) {
      acc[symbol.category] = [];
    }
    acc[symbol.category].push(symbol);
    return acc;
  }, {} as Record<string, Symbol[]>);

  const daysOptions = [
    { value: 1, label: '1 день' },
    { value: 7, label: '7 дней' },
    { value: 30, label: '30 дней' },
    { value: 90, label: '90 дней' },
    { value: 180, label: '180 дней' },
    { value: 365, label: '1 год' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Загрузка графиков...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️ Ошибка</div>
          <p className="text-gray-400">{error}</p>
          <p className="text-gray-500 mt-2">Используются данные по умолчанию</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">📈 Графики криптовалют</h1>
          <p className="text-gray-400">Интерактивные графики с историческими данными TOP-20 криптовалют</p>
        </div>

        {/* Controls */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Symbol Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                💰 Криптовалюта
              </label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(symbolsByCategory).map(([category, categorySymbols]) => (
                  <optgroup key={category} label={category}>
                    {categorySymbols.map((symbol) => (
                      <option key={symbol.symbol} value={symbol.symbol}>
                        {symbol.name} ({symbol.symbol.replace('USDT', '/USDT')})
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            {/* Interval Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ⏰ Интервал
              </label>
              <select
                value={selectedInterval}
                onChange={(e) => setSelectedInterval(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(intervals).map(([value, interval]) => (
                  <option key={value} value={value}>
                    {interval.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Days Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                📅 Период
              </label>
              <select
                value={selectedDays}
                onChange={(e) => setSelectedDays(parseInt(e.target.value))}
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {daysOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* View Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                👁️ Режим просмотра
              </label>
              <select
                value={showMultiple ? 'multiple' : 'single'}
                onChange={(e) => setShowMultiple(e.target.value === 'multiple')}
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="single">Одиночный график</option>
                <option value="multiple">Множественные графики</option>
              </select>
            </div>

            {/* Quick Actions */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ⚡ Быстрые действия
              </label>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setSelectedSymbol('BTCUSDT');
                    setSelectedInterval('1h');
                    setSelectedDays(30);
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md text-sm transition-colors"
                >
                  BTC 1h
                </button>
                <button
                  onClick={() => {
                    setSelectedSymbol('ETHUSDT');
                    setSelectedInterval('4h');
                    setSelectedDays(90);
                  }}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-md text-sm transition-colors"
                >
                  ETH 4h
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        {showMultiple ? (
          /* Multiple Charts View */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {multipleSymbols.map((symbol) => (
              <div key={symbol} className="bg-gray-900 rounded-lg overflow-hidden">
                <TradingViewChart
                  symbol={symbol}
                  interval={selectedInterval}
                  days={selectedDays}
                  height={350}
                  showToolbar={true}
                />
              </div>
            ))}
          </div>
        ) : (
          /* Single Chart View */
          <div className="bg-gray-900 rounded-lg overflow-hidden">
            <TradingViewChart
              symbol={selectedSymbol}
              interval={selectedInterval}
              days={selectedDays}
              height={600}
              showToolbar={true}
            />
          </div>
        )}

        {/* Quick Symbol Selector for Multiple View */}
        {showMultiple && (
          <div className="mt-6 bg-gray-900 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-3">🎯 Выбор криптовалют для сравнения</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {symbols.slice(0, 12).map((symbol) => (
                <button
                  key={symbol.symbol}
                  onClick={() => {
                    if (multipleSymbols.includes(symbol.symbol)) {
                      setMultipleSymbols(multipleSymbols.filter(s => s !== symbol.symbol));
                    } else if (multipleSymbols.length < 4) {
                      setMultipleSymbols([...multipleSymbols, symbol.symbol]);
                    }
                  }}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    multipleSymbols.includes(symbol.symbol)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  } ${multipleSymbols.length >= 4 && !multipleSymbols.includes(symbol.symbol) ? 'opacity-50 cursor-not-allowed' : ''}`}
                  disabled={multipleSymbols.length >= 4 && !multipleSymbols.includes(symbol.symbol)}
                >
                  {symbol.symbol.replace('USDT', '')}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Выбрано: {multipleSymbols.length}/4 криптовалют
            </p>
          </div>
        )}

        {/* Market Overview */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-2">📊 Статистика</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Доступно символов:</span>
                <span className="text-white">{symbols.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Интервалов:</span>
                <span className="text-white">{Object.keys(intervals).length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Текущий символ:</span>
                <span className="text-blue-400">{selectedSymbol.replace('USDT', '/USDT')}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-2">⚙️ Настройки</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Интервал:</span>
                <span className="text-white">{intervals[selectedInterval]?.name || selectedInterval}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Период:</span>
                <span className="text-white">{selectedDays} дней</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Режим:</span>
                <span className="text-white">{showMultiple ? 'Множественный' : 'Одиночный'}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-2">🎯 Категории</h3>
            <div className="space-y-2 text-sm">
              {Object.entries(symbolsByCategory).map(([category, categorySymbols]) => (
                <div key={category} className="flex justify-between">
                  <span className="text-gray-400">{category}:</span>
                  <span className="text-white">{categorySymbols.length}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Help */}
        <div className="mt-6 bg-gray-900 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">ℹ️ Помощь</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-400">
            <div>
              <h4 className="text-white font-medium mb-1">Навигация:</h4>
              <ul className="space-y-1">
                <li>• Выберите криптовалюту из списка</li>
                <li>• Настройте интервал (1m - 1w)</li>
                <li>• Выберите период для анализа</li>
                <li>• Переключайтесь между режимами просмотра</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-medium mb-1">Функции графика:</h4>
              <ul className="space-y-1">
                <li>• Свечной график с объемами</li>
                <li>• Реальные данные с Binance API</li>
                <li>• Автоматическое обновление</li>
                <li>• Адаптивный дизайн</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Charts; 