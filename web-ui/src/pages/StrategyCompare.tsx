import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const StrategyCompare: React.FC = () => {
  const { data } = useQuery({ queryKey: ['strategies-list'], queryFn: async () => (await fetch('/api/v1/strategies')).json() });
  const strategies = data?.strategies || [];

  const [a, setA] = useState('trend_following');
  const [b, setB] = useState('swing_conservative');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [days, setDays] = useState(30);
  const [timeframe, setTimeframe] = useState('5m');

  const backtest = async (name: string) => {
    const res = await fetch('/api/v1/strategies/backtest', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, symbol, days, timeframe, params: {} }),
    });
    return res.json();
  };

  const [resultA, setResultA] = useState<any>(null);
  const [resultB, setResultB] = useState<any>(null);

  const runMutation = useMutation(async () => {
    const [ra, rb] = await Promise.all([backtest(a), backtest(b)]);
    setResultA(ra); setResultB(rb);
    return true;
  });

  const metric = (r: any, key: string, d: any = '-') => r?.performance?.[key] ?? d;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Сравнение стратегий (A/B)</h1>
      </div>

      <div className="card p-4 space-y-3">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm mb-1">Стратегия A</label>
            <select className="input w-full" value={a} onChange={e => setA(e.target.value)}>
              {strategies.map((s: any) => <option key={s.name} value={s.name}>{s.display_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Стратегия B</label>
            <select className="input w-full" value={b} onChange={e => setB(e.target.value)}>
              {strategies.map((s: any) => <option key={s.name} value={s.name}>{s.display_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Символ</label>
            <input className="input w-full" value={symbol} onChange={e => setSymbol(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm mb-1">Дней</label>
            <input type="number" className="input w-full" value={days} onChange={e => setDays(parseInt(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm mb-1">TF</label>
            <select className="input w-full" value={timeframe} onChange={e => setTimeframe(e.target.value)}>
              {['1m','5m','15m','1h','4h','1d'].map(tf => <option key={tf} value={tf}>{tf}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn btn-primary" onClick={() => runMutation.mutate()}>Сравнить</button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-4">
          <h2 className="text-lg font-semibold">A: {a}</h2>
          <div className="text-gray-300 text-sm space-y-1">
            <div>Сделок: {metric(resultA, 'trades')}</div>
            <div>Winrate: {metric(resultA, 'winrate')}%</div>
            <div>PF: {metric(resultA, 'profit_factor')}</div>
            <div>Sharpe: {metric(resultA, 'sharpe')}</div>
            <div>MaxDD: {(resultA?.performance?.max_drawdown * 100 || 0).toFixed(2)}%</div>
          </div>
          {resultA?.chart && (
            <div className="mt-3 h-48 bg-gray-800 rounded">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={resultA.chart} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="t" tick={false} stroke="#9CA3AF" />
                  <YAxis stroke="#86EFAC" domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151' }} />
                  <Line type="monotone" dataKey="equity" stroke="#34d399" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          {resultA && <pre className="mt-3 text-xs text-gray-300 bg-gray-800 p-3 rounded">{JSON.stringify(resultA.signals?.slice(-10), null, 2)}</pre>}
        </div>
        <div className="card p-4">
          <h2 className="text-lg font-semibold">B: {b}</h2>
          <div className="text-gray-300 text-sm space-y-1">
            <div>Сделок: {metric(resultB, 'trades')}</div>
            <div>Winrate: {metric(resultB, 'winrate')}%</div>
            <div>PF: {metric(resultB, 'profit_factor')}</div>
            <div>Sharpe: {metric(resultB, 'sharpe')}</div>
            <div>MaxDD: {(resultB?.performance?.max_drawdown * 100 || 0).toFixed(2)}%</div>
          </div>
          {resultB?.chart && (
            <div className="mt-3 h-48 bg-gray-800 rounded">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={resultB.chart} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="t" tick={false} stroke="#9CA3AF" />
                  <YAxis stroke="#86EFAC" domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151' }} />
                  <Line type="monotone" dataKey="equity" stroke="#34d399" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          {resultB && <pre className="mt-3 text-xs text-gray-300 bg-gray-800 p-3 rounded">{JSON.stringify(resultB.signals?.slice(-10), null, 2)}</pre>}
        </div>
      </div>
    </div>
  );
};

export default StrategyCompare;
