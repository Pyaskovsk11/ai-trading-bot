import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface DemoPosition {
  symbol: string;
  side: string;
  entry_price: number;
  quantity: number;
  entry_time: string;
  stop_loss?: number;
  take_profit?: number;
  current_pnl: number;
  unrealized_pnl: number;
  status: string;
  reason: string;
}

interface DemoAccount {
  balance: number;
  equity: number;
  margin_used: number;
  free_margin: number;
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  positions: DemoPosition[];
  is_running: boolean;
}

interface TradeHistory {
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  entry_time: string;
  exit_time: string;
  pnl: number;
  reason: string;
}

const DemoTrading: React.FC = () => {
  const [account, setAccount] = useState<DemoAccount | null>(null);
  const [history, setHistory] = useState<TradeHistory[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState('swing_conservative');
  const [selectedSymbols, setSelectedSymbols] = useState(['BTCUSDT', 'ETHUSDT', 'ADAUSDT']);
  const [manualTrade, setManualTrade] = useState({
    symbol: 'BTCUSDT',
    side: 'LONG',
    quantity: 0.001,
    price: 50000
  });

  const strategies = [
    { name: 'swing_conservative', label: 'Swing Conservative' },
    { name: 'trend_following', label: 'Trend Following' },
    { name: 'adaptive_multi_timeframe', label: 'Adaptive Multi-Timeframe' }
  ];

  const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'SOLUSDT'];

  const fetchAccountStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/demo-trading/status');
      setAccount(response.data);
    } catch (error) {
      console.error('Error fetching account status:', error);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/demo-trading/history');
      setHistory(response.data.history || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const fetchPerformance = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/demo-trading/performance');
      setPerformance(response.data);
    } catch (error) {
      console.error('Error fetching performance:', error);
    }
  };

  const startDemoTrading = async () => {
    setIsLoading(true);
    try {
      await axios.post('http://localhost:8000/api/v1/demo-trading/start', {
        symbols: selectedSymbols,
        strategy_name: selectedStrategy,
        initial_balance: 1000.0
      });
      alert('Демо-торговля запущена!');
      fetchAccountStatus();
    } catch (error) {
      alert('Ошибка запуска демо-торговли');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const stopDemoTrading = async () => {
    try {
      await axios.post('http://localhost:8000/api/v1/demo-trading/stop');
      alert('Демо-торговля остановлена!');
      fetchAccountStatus();
    } catch (error) {
      alert('Ошибка остановки демо-торговли');
      console.error(error);
    }
  };

  const resetAccount = async () => {
    if (window.confirm('Вы уверены, что хотите сбросить демо-счет?')) {
      try {
        await axios.post('http://localhost:8000/api/v1/demo-trading/reset');
        alert('Демо-счет сброшен!');
        fetchAccountStatus();
        fetchHistory();
        fetchPerformance();
      } catch (error) {
        alert('Ошибка сброса счета');
        console.error(error);
      }
    }
  };

  const executeManualTrade = async () => {
    try {
      await axios.post('http://localhost:8000/api/v1/demo-trading/trade', manualTrade);
      alert('Сделка выполнена!');
      fetchAccountStatus();
    } catch (error) {
      alert('Ошибка выполнения сделки');
      console.error(error);
    }
  };

  const closePosition = async (symbol: string) => {
    try {
      await axios.post(`http://localhost:8000/api/v1/demo-trading/close/${symbol}`);
      alert(`Позиция ${symbol} закрыта!`);
      fetchAccountStatus();
    } catch (error) {
      alert('Ошибка закрытия позиции');
      console.error(error);
    }
  };

  useEffect(() => {
    fetchAccountStatus();
    fetchHistory();
    fetchPerformance();
    
    const interval = setInterval(() => {
      fetchAccountStatus();
    }, 5000); // Обновляем каждые 5 секунд

    return () => clearInterval(interval);
  }, []);

  if (!account) {
    return <div className="flex justify-center items-center h-screen">Загрузка...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">🎯 Демо-Торговля</h1>
          <p className="text-gray-300">Тестирование стратегий с виртуальным счетом $1000</p>
        </div>

        {/* Управление */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Управление</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2">Стратегия</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
              >
                {strategies.map(strategy => (
                  <option key={strategy.name} value={strategy.name}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Символы</label>
              <select
                multiple
                value={selectedSymbols}
                onChange={(e) => setSelectedSymbols(Array.from(e.target.selectedOptions, option => option.value))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
              >
                {symbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end space-x-2">
              <button
                onClick={startDemoTrading}
                disabled={isLoading || account.is_running}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded-lg font-medium"
              >
                {isLoading ? 'Запуск...' : 'Запустить'}
              </button>
              <button
                onClick={stopDemoTrading}
                disabled={!account.is_running}
                className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 px-4 py-2 rounded-lg font-medium"
              >
                Остановить
              </button>
            </div>
          </div>
          <button
            onClick={resetAccount}
            className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg font-medium"
          >
            Сбросить счет
          </button>
        </div>

        {/* Статистика счета */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400">Баланс</h3>
            <p className="text-2xl font-bold text-green-400">${account.balance.toFixed(2)}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400">Собственный капитал</h3>
            <p className={`text-2xl font-bold ${account.equity >= account.balance ? 'text-green-400' : 'text-red-400'}`}>
              ${account.equity.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400">Общий P&L</h3>
            <p className={`text-2xl font-bold ${account.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${account.total_pnl.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400">Винрейт</h3>
            <p className="text-2xl font-bold text-blue-400">{account.win_rate.toFixed(1)}%</p>
          </div>
        </div>

        {/* Открытые позиции */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Открытые позиции ({account.positions.length})</h2>
          {account.positions.length === 0 ? (
            <p className="text-gray-400">Нет открытых позиций</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2">Символ</th>
                    <th className="text-left py-2">Сторона</th>
                    <th className="text-left py-2">Цена входа</th>
                    <th className="text-left py-2">Количество</th>
                    <th className="text-left py-2">P&L</th>
                    <th className="text-left py-2">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {account.positions.map((position, index) => (
                    <tr key={index} className="border-b border-gray-700">
                      <td className="py-2">{position.symbol}</td>
                      <td className={`py-2 ${position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                        {position.side}
                      </td>
                      <td className="py-2">${position.entry_price.toFixed(2)}</td>
                      <td className="py-2">{position.quantity.toFixed(4)}</td>
                      <td className={`py-2 ${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${position.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => closePosition(position.symbol)}
                          className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-sm"
                        >
                          Закрыть
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Ручная торговля */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Ручная торговля</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Символ</label>
              <select
                value={manualTrade.symbol}
                onChange={(e) => setManualTrade({...manualTrade, symbol: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
              >
                {symbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Сторона</label>
              <select
                value={manualTrade.side}
                onChange={(e) => setManualTrade({...manualTrade, side: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
              >
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Количество</label>
              <input
                type="number"
                value={manualTrade.quantity}
                onChange={(e) => setManualTrade({...manualTrade, quantity: parseFloat(e.target.value)})}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
                step="0.0001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Цена</label>
              <input
                type="number"
                value={manualTrade.price}
                onChange={(e) => setManualTrade({...manualTrade, price: parseFloat(e.target.value)})}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
                step="0.01"
              />
            </div>
          </div>
          <button
            onClick={executeManualTrade}
            className="mt-4 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium"
          >
            Выполнить сделку
          </button>
        </div>

        {/* История торговли */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">История торговли ({history.length})</h2>
          {history.length === 0 ? (
            <p className="text-gray-400">Нет истории торговли</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2">Символ</th>
                    <th className="text-left py-2">Сторона</th>
                    <th className="text-left py-2">Цена входа</th>
                    <th className="text-left py-2">Цена выхода</th>
                    <th className="text-left py-2">P&L</th>
                    <th className="text-left py-2">Причина</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(-10).reverse().map((trade, index) => (
                    <tr key={index} className="border-b border-gray-700">
                      <td className="py-2">{trade.symbol}</td>
                      <td className={`py-2 ${trade.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.side}
                      </td>
                      <td className="py-2">${trade.entry_price.toFixed(2)}</td>
                      <td className="py-2">${trade.exit_price.toFixed(2)}</td>
                      <td className={`py-2 ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${trade.pnl.toFixed(2)}
                      </td>
                      <td className="py-2 text-sm">{trade.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Производительность */}
        {performance && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Производительность</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-400">Общая доходность</h3>
                <p className={`text-2xl font-bold ${performance.total_return_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {performance.total_return_percent.toFixed(2)}%
                </p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-400">Средний P&L на сделку</h3>
                <p className={`text-2xl font-bold ${performance.avg_pnl_per_trade >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${performance.avg_pnl_per_trade.toFixed(2)}
                </p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-400">Всего сделок</h3>
                <p className="text-2xl font-bold text-blue-400">{performance.total_trades}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DemoTrading;
