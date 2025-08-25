import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

interface StrategyParamSpec {
  name: string;
  type: string;
  default: number | string;
  min?: number;
  max?: number;
  step?: number;
  desc?: string;
}

interface StrategySpec {
  name: string;
  display_name: string;
  description: string;
  category: string;
  params: StrategyParamSpec[];
}

const AdminBacktest: React.FC = () => {
  const { data: strategiesResp, isLoading } = useQuery({
    queryKey: ['strategies-list'],
    queryFn: async () => (await fetch('/api/v1/strategies')).json(),
  });

  const strategies: StrategySpec[] = useMemo(() => strategiesResp?.strategies || [], [strategiesResp]);
  const [selected, setSelected] = useState<string>('');
  useEffect(() => {
    if (!selected && strategies.length) setSelected(strategies[0].name);
  }, [strategies, selected]);

  const spec = useMemo(() => strategies.find(s => s.name === selected), [strategies, selected]);

  const [symbol, setSymbol] = useState('BTCUSDT');
  const [days, setDays] = useState(60);
  const [timeframe, setTimeframe] = useState('15m');
  const [params, setParams] = useState<Record<string, any>>({});

  // Sweep settings
  const [sweepParam, setSweepParam] = useState<string>('');
  const [sweepFrom, setSweepFrom] = useState<number>(0);
  const [sweepTo, setSweepTo] = useState<number>(0);
  const [sweepStep, setSweepStep] = useState<number>(0);

  // Results
  const [singleResult, setSingleResult] = useState<any>(null);
  const [gridResults, setGridResults] = useState<any[]>([]);
  const [activeIdx, setActiveIdx] = useState<number>(-1);
  const abortRef = useRef<boolean>(false);

  const pollJob = async (jobId: string) => {
    abortRef.current = false;
    // простой polling 1.5s пока не done/failed
    while (!abortRef.current) {
      const st = await fetch(`/api/v1/admin/backtests/${jobId}`);
      const js = await st.json();
      if (js.status === 'done') {
        const r = await fetch(`/api/v1/admin/backtests/${jobId}/result`);
        return await r.json();
      }
      if (js.status === 'failed') {
        throw new Error(js.error || 'job failed');
      }
      await new Promise(res => setTimeout(res, 1500));
    }
    throw new Error('aborted');
  };

  const runSingle = useMutation(async () => {
    const body = { name: selected, symbol, days, timeframe, params };
    const res = await fetch('/api/v1/admin/backtests', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const { job_id } = await res.json();
    const result = await pollJob(job_id);
    return result;
  }, {
    onSuccess: (data) => { setSingleResult(data); setGridResults([]); setActiveIdx(-1); },
  });

  const runGrid = useMutation(async () => {
    if (!sweepParam || sweepStep === 0) return [];
    const values: number[] = [];
    for (let v = sweepFrom; v <= sweepTo + 1e-9; v += sweepStep) values.push(Number(v.toFixed(6)));
    const out: any[] = [];
    for (const v of values) {
      const body = { name: selected, symbol, days, timeframe, params: { ...params, [sweepParam]: v } };
      const res = await fetch('/api/v1/admin/backtests', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const { job_id } = await res.json();
      const json = await pollJob(job_id);
      out.push({ value: v, result: json });
    }
    return out;
  }, {
    onSuccess: (data) => { setGridResults(data as any[]); setActiveIdx(0); setSingleResult(null); },
  });

  const activeResult = activeIdx >= 0 ? gridResults[activeIdx]?.result : singleResult;

  const metricsRow = (r: any) => ({
    trades: r?.performance?.trades ?? 0,
    winrate: r?.performance?.winrate ?? 0,
    pf: r?.performance?.profit_factor ?? null,
    sharpe: r?.performance?.sharpe ?? null,
    maxdd: (r?.performance?.max_drawdown ?? 0) * 100,
    avgR: r?.performance?.avg_R ?? null,
    final: r?.performance?.final_balance ?? r?.chart?.slice(-1)[0]?.equity ?? null,
  });

  const activeMetrics = metricsRow(activeResult);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Admin · Бэктесты</h1>
      </div>

      <div className="card p-4 space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-2">Стратегии</h3>
            {isLoading ? <div className="text-gray-400">Загрузка...</div> : (
              <ul className="space-y-2">
                {strategies.map(s => (
                  <li key={s.name}>
                    <button
                      onClick={() => { setSelected(s.name); setParams({}); setSingleResult(null); setGridResults([]); setActiveIdx(-1); }}
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

          <div className="lg:col-span-2">
            <h3 className="text-lg font-semibold mb-2">Настройки запуска</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
            </div>

            <h4 className="mt-4 mb-2 font-semibold">Параметры стратегии</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {spec?.params.map(p => (
                <div key={p.name}>
                  <label className="block text-sm mb-1">{p.name}</label>
                  <input
                    type={(p.type === 'int' || p.type === 'float') ? 'number' : 'text'}
                    step={p.step || 1}
                    min={p.min}
                    max={p.max}
                    defaultValue={String(p.default)}
                    className="input w-full"
                    onChange={e => setParams(prev => ({ ...prev, [p.name]: (p.type === 'int' ? parseInt(e.target.value) : (p.type === 'float' ? parseFloat(e.target.value) : e.target.value)) }))}
                  />
                </div>
              ))}
            </div>

            <div className="flex gap-3 mt-4">
              <button className="btn btn-primary" onClick={() => runSingle.mutate()} disabled={runSingle.isLoading}>Запустить одиночный</button>
            </div>

            <div className="mt-6 p-3 rounded bg-gray-800">
              <div className="font-semibold mb-2">Параметрический прогон</div>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
                <div>
                  <label className="block text-sm mb-1">Параметр</label>
                  <select className="input w-full" value={sweepParam} onChange={e => setSweepParam(e.target.value)}>
                    <option value="">—</option>
                    {spec?.params.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm mb-1">От</label>
                  <input type="number" className="input w-full" value={sweepFrom} onChange={e => setSweepFrom(parseFloat(e.target.value || '0'))} />
                </div>
                <div>
                  <label className="block text-sm mb-1">До</label>
                  <input type="number" className="input w-full" value={sweepTo} onChange={e => setSweepTo(parseFloat(e.target.value || '0'))} />
                </div>
                <div>
                  <label className="block text-sm mb-1">Шаг</label>
                  <input type="number" className="input w-full" value={sweepStep} onChange={e => setSweepStep(parseFloat(e.target.value || '0'))} />
                </div>
                <div className="flex items-end">
                  <button className="btn" onClick={() => runGrid.mutate()} disabled={runGrid.isLoading || !sweepParam}>Запустить сетку</button>
                </div>
              </div>
              {(runSingle.isLoading || runGrid.isLoading) && <div className="text-xs text-gray-400 mt-2">Выполняется, подождите...</div>}
              {gridResults.length > 0 && (
                <div className="mt-4">
                  <div className="flex gap-2 flex-wrap">
                    {gridResults.map((gr, idx) => (
                      <button key={idx} className={`btn btn-xs ${idx === activeIdx ? 'btn-primary' : ''}`} onClick={() => setActiveIdx(idx)}>
                        {sweepParam}={gr.value}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Метрики и график активного результата */}
      {activeResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="card p-4 space-y-2">
            <h3 className="text-lg font-semibold">Метрики</h3>
            <div className="text-sm text-gray-300 space-y-1">
              <div>Сделок: {activeMetrics.trades}</div>
              <div>Winrate: {activeMetrics.winrate.toFixed(2)}%</div>
              <div>PF: {activeMetrics.pf ? activeMetrics.pf.toFixed(2) : '-'}</div>
              <div>Sharpe: {activeMetrics.sharpe ? activeMetrics.sharpe.toFixed(2) : '-'}</div>
              <div>MaxDD: {activeMetrics.maxdd.toFixed(2)}%</div>
              <div>Avg R: {activeMetrics.avgR ? activeMetrics.avgR.toFixed(2) : '-'}</div>
            </div>
          </div>
          <div className="card p-4 lg:col-span-2">
            <h3 className="text-lg font-semibold mb-2">Equity / Drawdown</h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={activeResult?.chart || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="t" tick={false} stroke="#9CA3AF" />
                  <YAxis yAxisId="left" stroke="#86EFAC" domain={['auto', 'auto']} />
                  <YAxis yAxisId="right" orientation="right" stroke="#FCA5A5" domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151' }} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="equity" stroke="#34d399" dot={false} name="Equity" />
                  <Line yAxisId="right" type="monotone" dataKey="drawdown" stroke="#f87171" dot={false} name="Drawdown" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {gridResults.length > 0 && (
        <div className="card p-4 mt-4">
          <h3 className="text-lg font-semibold mb-2">Результаты сетки</h3>
          <div className="overflow-auto">
            <table className="min-w-full text-sm text-gray-300">
              <thead>
                <tr className="text-left border-b border-gray-700">
                  <th className="py-2 pr-4">{sweepParam}</th>
                  <th className="py-2 pr-4">Trades</th>
                  <th className="py-2 pr-4">Winrate %</th>
                  <th className="py-2 pr-4">PF</th>
                  <th className="py-2 pr-4">Sharpe</th>
                  <th className="py-2 pr-4">MaxDD %</th>
                  <th className="py-2 pr-4">Avg R</th>
                </tr>
              </thead>
              <tbody>
                {gridResults.map((gr, idx) => {
                  const m = metricsRow(gr.result);
                  return (
                    <tr key={idx} className={`border-b border-gray-800 ${idx === activeIdx ? 'bg-gray-800/60' : ''}`} onClick={() => setActiveIdx(idx)}>
                      <td className="py-2 pr-4">{gr.value}</td>
                      <td className="py-2 pr-4">{m.trades}</td>
                      <td className="py-2 pr-4">{m.winrate.toFixed(2)}</td>
                      <td className="py-2 pr-4">{m.pf ? m.pf.toFixed(2) : '-'}</td>
                      <td className="py-2 pr-4">{m.sharpe ? m.sharpe.toFixed(2) : '-'}</td>
                      <td className="py-2 pr-4">{m.maxdd.toFixed(2)}</td>
                      <td className="py-2 pr-4">{m.avgR ? m.avgR.toFixed(2) : '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminBacktest;
