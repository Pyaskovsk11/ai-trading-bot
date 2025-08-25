import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

const Scanner: React.FC = () => {
  const [limit, setLimit] = useState(30);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [query, setQuery] = useState('');
  const [minVolume, setMinVolume] = useState<number>(0);
  const [minVolatility, setMinVolatility] = useState<number>(0);
  const navigate = useNavigate();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['scanner-top', limit],
    queryFn: async () => (await fetch(`/api/v1/scanner/top?limit=${limit}`)).json(),
    refetchInterval: autoRefresh ? 30000 : false,
  });

  const filterItems = useCallback((items: any[] = []) => {
    const q = query.trim().toUpperCase();
    return items.filter(it => (
      (!q || it.symbol.includes(q)) &&
      (it.volume_usdt >= (minVolume || 0)) &&
      ((it.volatility * 100) >= (minVolatility || 0))
    ));
  }, [query, minVolume, minVolatility]);

  const byVolume = useMemo(() => filterItems(data?.by_volume), [data, filterItems]);
  const byVolatility = useMemo(() => filterItems(data?.by_volatility), [data, filterItems]);
  const byAtr = useMemo(() => filterItems(data?.by_atr), [data, filterItems]);

  const Section = ({ title, items }: any) => (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <div className="overflow-auto">
        <table className="min-w-full text-sm text-gray-300">
          <thead>
            <tr className="text-left border-b border-gray-700">
              <th className="py-2 pr-4">Symbol</th>
              <th className="py-2 pr-4">Vol USDT</th>
              <th className="py-2 pr-4">Volatility</th>
              <th className="py-2 pr-4">ATR-like</th>
              <th className="py-2 pr-4">24h %</th>
              <th className="py-2 pr-4">Действия</th>
            </tr>
          </thead>
          <tbody>
            {items?.map((it: any) => (
              <tr key={it.symbol} className="border-b border-gray-800 hover:bg-gray-800/50">
                <td className="py-2 pr-4">{it.symbol}</td>
                <td className="py-2 pr-4">{Math.round(it.volume_usdt).toLocaleString()}</td>
                <td className="py-2 pr-4">{(it.volatility * 100).toFixed(2)}%</td>
                <td className="py-2 pr-4">{it.atr_like.toFixed(2)}</td>
                <td className={`py-2 pr-4 ${it.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>{it.change_24h.toFixed(2)}%</td>
                <td className="py-2 pr-4">
                  <button className="btn btn-xs" onClick={() => navigate(`/strategies?symbol=${encodeURIComponent(it.symbol)}&tf=5m`)}>Бэктест</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-white">Сканер символов</h1>
        <div className="flex items-center gap-2">
          <input className="input" placeholder="Поиск (e.g. BTCUSDT)" value={query} onChange={e => setQuery(e.target.value)} />
          <label className="text-sm text-gray-300">Мин. объём, USDT</label>
          <input type="number" className="input w-32" value={minVolume} onChange={e => setMinVolume(parseFloat(e.target.value || '0'))} />
          <label className="text-sm text-gray-300">Мин. волат., %</label>
          <input type="number" className="input w-24" value={minVolatility} onChange={e => setMinVolatility(parseFloat(e.target.value || '0'))} />
          <label className="text-sm text-gray-300">Лимит</label>
          <select className="input" value={limit} onChange={e => setLimit(parseInt(e.target.value))}>
            {[10,20,30,50,100].map(v => <option key={v} value={v}>{v}</option>)}
          </select>
          <label className="text-sm text-gray-300 ml-1">Автообновление</label>
          <input type="checkbox" className="toggle" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
          <button className="btn" onClick={() => refetch()}>Обновить</button>
          <button className="btn" onClick={() => navigate('/security-keys')}>API-ключи</button>
        </div>
      </div>
      {isLoading && <div>Загрузка...</div>}
      {isError && (
        <div className="text-red-400 text-sm">
          Не удалось загрузить данные сканера. Проверьте backend (8000) и интернет. {String((error as any)?.message || '')}
        </div>
      )}
      {!isLoading && !isError && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Section title="Топ по объёму" items={byVolume} />
          <Section title="Топ по волатильности" items={byVolatility} />
          <Section title="Топ по ATR-like" items={byAtr} />
        </div>
      )}
    </div>
  );
};

export default Scanner;
