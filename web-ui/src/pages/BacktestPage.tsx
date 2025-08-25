import React, { useState } from 'react';
import { backtestApi } from '../utils/api';

const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'];
const timeframes = ['15m', '1h', '4h'];
const strategies = [
  { value: 'trend_following', label: 'Следование тренду' },
  { value: 'scalping', label: 'Скальпинг' },
  { value: 'breakout', label: 'Пробой' },
  { value: 'mean_reversion', label: 'Mean Reversion' },
  { value: 'volatility_spike', label: 'Всплеск волатильности' },
];

const BacktestPage = () => {
  const [symbol, setSymbol] = useState(symbols[0]);
  const [timeframe, setTimeframe] = useState(timeframes[1]);
  const [strategy, setStrategy] = useState(strategies[0].value);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<null | any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setResult(null);
    setError(null);
    try {
      // Формируем payload для API
      const payload = {
        symbols: [symbol],
        start_date: dateFrom,
        end_date: dateTo,
        timeframe,
        strategy_type: strategy,
        aggressiveness: 'moderate',
        ai_mode: 'semi_auto',
        initial_capital: 10000,
        commission_rate: 0.001,
        slippage_rate: 0.0005,
        position_size: 0.02,
        max_positions: 10,
        use_stop_loss: true,
        max_trade_duration: 24,
      };
      const { data } = await backtestApi.run(payload);
      const backtestId = data.backtest_id;
      // Poll status
      let status = 'running';
      let pollCount = 0;
      while (status === 'running' && pollCount < 60) {
        await new Promise(res => setTimeout(res, 2000));
        const statusResp = await backtestApi.status(backtestId);
        status = statusResp.data.status;
        pollCount++;
      }
      if (status !== 'completed') {
        setError('Бэктест не завершился вовремя или произошла ошибка.');
        setIsRunning(false);
        return;
      }
      // Получаем результат
      const resultResp = await backtestApi.result(backtestId);
      setResult(resultResp.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Ошибка запуска бэктеста');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="p-8 text-white max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Бэктестинг стратегий</h1>
      <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-6 mb-8 shadow">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block mb-1">Символ</label>
            <select value={symbol} onChange={e => setSymbol(e.target.value)} className="w-full bg-gray-700 rounded px-2 py-1">
              {symbols.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block mb-1">Таймфрейм</label>
            <select value={timeframe} onChange={e => setTimeframe(e.target.value)} className="w-full bg-gray-700 rounded px-2 py-1">
              {timeframes.map(tf => <option key={tf} value={tf}>{tf}</option>)}
            </select>
          </div>
          <div>
            <label className="block mb-1">Стратегия</label>
            <select value={strategy} onChange={e => setStrategy(e.target.value)} className="w-full bg-gray-700 rounded px-2 py-1">
              {strategies.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block mb-1">Период с</label>
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="w-full bg-gray-700 rounded px-2 py-1" />
          </div>
          <div>
            <label className="block mb-1">Период по</label>
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="w-full bg-gray-700 rounded px-2 py-1" />
          </div>
        </div>
        <button type="submit" className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white font-semibold" disabled={isRunning}>
          {isRunning ? 'Запуск...' : 'Запустить бэктест'}
        </button>
      </form>
      {error && <div className="bg-red-700 text-white p-3 mb-4 rounded">{error}</div>}
      {isRunning && <div className="text-blue-400 mb-4">Бэктест выполняется, пожалуйста, подождите...</div>}
      {result && (
        <div className="bg-gray-800 rounded-lg p-6 shadow">
          <h2 className="text-xl font-semibold mb-2">Результаты</h2>
          <ul className="mb-2">
            <li>PNL: <span className="font-mono">{result.metrics?.pnl ?? '-'}</span></li>
            <li>Winrate: <span className="font-mono">{(result.metrics?.winrate * 100).toFixed(1) ?? '-'}%</span></li>
            <li>Max Drawdown: <span className="font-mono">{(result.metrics?.max_drawdown * 100).toFixed(1) ?? '-'}%</span></li>
            <li>Сделок: <span className="font-mono">{result.trades_count ?? '-'}</span></li>
          </ul>
          <div className="text-gray-400 text-sm">(Данные получены с backend API)</div>
        </div>
      )}
    </div>
  );
};

export default BacktestPage; 