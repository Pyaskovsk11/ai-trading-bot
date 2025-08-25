import React, { useMemo, useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, ReferenceLine } from 'recharts';

const StrategyLibrary: React.FC = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['strategies-list'],
    queryFn: async () => (await fetch('/api/v1/strategies')).json(),
  });
  const { data: currentSettings } = useQuery({
    queryKey: ['trading-settings-current'],
    queryFn: async () => (await fetch('/api/v1/trading-settings/current')).json(),
  });

  const [selected, setSelected] = useState<string>('');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [days, setDays] = useState(30);
  const [params, setParams] = useState<Record<string, any>>({});
  const [timeframe, setTimeframe] = useState('5m');

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const s = params.get('symbol');
      const tf = params.get('tf');
      const d = params.get('days');
      if (s) setSymbol(s);
      if (tf) setTimeframe(tf);
      if (d) setDays(parseInt(d));
    } catch {}
  }, []);

  useEffect(() => {
    const current = currentSettings?.strategy?.name;
    if (current && !selected) setSelected(current);
  }, [currentSettings, selected]);

  const strategies = useMemo(() => data?.strategies || [], [data]);
  const spec = useMemo(() => strategies.find((s: any) => s.name === selected), [strategies, selected]);

  const selectMutation = useMutation(async () => {
    const res = await fetch('/api/v1/strategies/select', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: selected, params }),
    });
    return res.json();
  }, {
    onSuccess: () => toast.success('Стратегия применена'),
    onError: () => toast.error('Ошибка применения стратегии'),
  });

  const backtestMutation = useMutation(async () => {
    const res = await fetch('/api/v1/strategies/backtest', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: selected, symbol, days, timeframe, params }),
    });
    return res.json();
  });

  // Фибоначчи уровни для equity: берем min/max и рисуем 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0
  const fibLevels = useMemo(() => {
    const chart = backtestMutation.data?.chart || [];
    if (!chart.length) return [] as number[];
    const values = chart.map((c: any) => c.equity);
    const minV = Math.min(...values), maxV = Math.max(...values);
    const span = maxV - minV || 1;
    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1].map(r => minV + span * r);
    return levels;
  }, [backtestMutation.data]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify_between">
        <h1 className="text-2xl font-bold text-white">Strategy Library</h1>
        <button className="btn" onClick={() => refetch()}>Обновить</button>
      </div>

      {/* Текущая стратегия */}
      <div className="card p-4">
        <div className="text-sm text-gray-300">Текущая стратегия</div>
        <div className="text-lg font-semibold">{currentSettings?.strategy?.name || selected || 'не выбрана'}</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-4 space-y-3">
          <h2 className="text-lg font-semibold">Стратегии</h2>
          {isLoading ? <div>Загрузка...</div> : (
            <ul className="space-y-2">
              {strategies.map((s: any) => (
                <li key={s.name}>
                  <button
                    onClick={() => { setSelected(s.name); setParams({}); }}
                    className={`w-full text-left p-3 rounded ${selected === s.name ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-200 hover:bg-gray-700'}`}
                  >
                    <div className="font-medium">{s.display_name}</div>
                    <div className="text-xs text-gray-400">{s.description}</div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card p-4 space-y-3 lg:col-span-2">
          <h2 className="text-lg font-semibold">Параметры</h2>
          {!spec ? <div className="text-gray-400">Выберите стратегию слева</div> : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {spec.params.map((p: any) => (
                  <div key={p.name}>
                    <label className="block text-sm mb-1">{p.name}</label>
                    <input
                      type={p.type === 'int' || p.type === 'float' ? 'number' : 'text'}
                      step={p.step || 1}
                      min={p.min}
                      max={p.max}
                      defaultValue={p.default}
                      className="input w-full"
                      onChange={e => setParams(prev => ({ ...prev, [p.name]: p.type === 'int' ? parseInt(e.target.value) : parseFloat(e.target.value) }))}
                    />
                  </div>
                ))}
              </div>
              <div className="flex gap-3">
                <button onClick={() => selectMutation.mutate()} className="btn btn-primary">Применить</button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card p-4 space-y-3">
        <h2 className="text-lg font-semibold">Быстрый бэктест</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
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
            <button onClick={() => backtestMutation.mutate()} className="btn">Запустить</button>
          </div>
        </div>
        {backtestMutation.data && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-sm text-gray-300">
              <div>Trades: {backtestMutation.data.performance?.trades}</div>
              <div>Winrate: {backtestMutation.data.performance?.winrate?.toFixed?.(2)}%</div>
              <div>PF: {backtestMutation.data.performance?.profit_factor?.toFixed?.(2) ?? '-'}</div>
              <div>Sharpe: {backtestMutation.data.performance?.sharpe?.toFixed?.(2) ?? '-'}</div>
              <div>MaxDD: {(backtestMutation.data.performance?.max_drawdown * 100)?.toFixed?.(2)}%</div>
              <div>Avg R: {backtestMutation.data.performance?.avg_R?.toFixed?.(2) ?? '-'}</div>
            </div>
            <div className="bg-gray-800 rounded p-3 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={backtestMutation.data.chart || [{ t: 0, equity: 0, drawdown: 0 }] } margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="t" tick={false} stroke="#9CA3AF" />
                  <YAxis yAxisId="left" stroke="#86EFAC" domain={['auto', 'auto']} />
                  <YAxis yAxisId="right" orientation="right" stroke="#FCA5A5" domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151' }} />
                  <Legend />
                  {/* Фибо линии */}
                  {fibLevels.map((lv: number, idx: number) => (
                    <ReferenceLine key={idx} y={lv} yAxisId="left" stroke="#6B7280" strokeDasharray="3 3" />
                  ))}
                  <Line yAxisId="left" type="monotone" dataKey="equity" stroke="#34d399" dot={false} name="Equity" />
                  <Line yAxisId="right" type="monotone" dataKey="drawdown" stroke="#f87171" dot={false} name="Drawdown" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyLibrary;
