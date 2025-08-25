import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const api = (path: string, options?: RequestInit) => fetch(path, options).then(r => r.json());

const RealTrading: React.FC = () => {
  const [exchange, setExchange] = useState('bingx');
  const [tradingType, setTradingType] = useState('futures');
  const [apiKey, setApiKey] = useState('');
  const [secret, setSecret] = useState('');
  const [testnet, setTestnet] = useState(true);
  const [symbols, setSymbols] = useState<string>('BTCUSDT,ETHUSDT');
  const [order, setOrder] = useState({ symbol: 'BTCUSDT', side: 'buy', amount: 0.001, order_type: 'market', price: '' });

  const statusQuery = useQuery({
    queryKey: ['real-trading-status'],
    queryFn: () => api('/api/v1/real-trading/status'),
    enabled: false,
  });

  const initMutation = useMutation(async () => {
    const body = {
      exchange,
      trading_type: tradingType,
      api_key: apiKey,
      secret,
      leverage: 1,
      testnet,
      symbols: symbols.split(',').map(s => s.trim()).filter(Boolean),
    };
    return api('/api/v1/real-trading/init', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  }, {
    onSuccess: (data) => { toast.success('Движок инициализирован'); statusQuery.refetch(); },
    onError: () => toast.error('Ошибка инициализации'),
  });

  const startMutation = useMutation(async () => {
    const body = { symbols: symbols.split(',').map(s => s.trim()).filter(Boolean) };
    return api('/api/v1/real-trading/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  }, {
    onSuccess: () => { toast.success('Торговля запущена'); statusQuery.refetch(); },
    onError: () => toast.error('Ошибка старта торговли'),
  });

  const stopMutation = useMutation(async () => api('/api/v1/real-trading/stop', { method: 'POST' }), {
    onSuccess: () => { toast.success('Торговля остановлена'); statusQuery.refetch(); },
    onError: () => toast.error('Ошибка остановки торговли'),
  });

  const balanceQuery = useQuery({
    queryKey: ['real-balance'],
    queryFn: () => api('/api/v1/real-trading/balance'),
    enabled: false,
  });

  const positionsQuery = useQuery({
    queryKey: ['real-positions'],
    queryFn: () => api('/api/v1/real-trading/positions'),
    enabled: false,
  });

  const placeOrderMutation = useMutation(async () => {
    const body: any = { symbol: order.symbol, side: order.side, amount: Number(order.amount), order_type: order.order_type };
    if (order.order_type === 'limit' && order.price) body.price = Number(order.price);
    return api('/api/v1/real-trading/order', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  }, {
    onSuccess: () => { toast.success('Ордер размещен'); positionsQuery.refetch(); },
    onError: () => toast.error('Ошибка размещения ордера'),
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Реальная торговля</h1>
        <p className="text-gray-400 text-sm">Инициализация и управление торговлей на бирже</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Инициализация</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">Биржа</label>
              <select className="input w-full" value={exchange} onChange={e => setExchange(e.target.value)}>
                <option value="binance">Binance</option>
                <option value="bingx">BingX</option>
                <option value="bybit">Bybit</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1">Тип</label>
              <select className="input w-full" value={tradingType} onChange={e => setTradingType(e.target.value)}>
                <option value="spot">Spot</option>
                <option value="futures">Futures</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-sm mb-1">API Key</label>
              <input type="password" className="input w-full" value={apiKey} onChange={e => setApiKey(e.target.value)} />
            </div>
            <div className="col-span-2">
              <label className="block text-sm mb-1">Secret</label>
              <input type="password" className="input w-full" value={secret} onChange={e => setSecret(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm mb-1">Тестнет</label>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" checked={testnet} onChange={e => setTestnet(e.target.checked)} />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            <div className="col-span-2">
              <label className="block text-sm mb-1">Символы (через запятую)</label>
              <input className="input w-full" value={symbols} onChange={e => setSymbols(e.target.value)} />
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={() => initMutation.mutate()} className="btn btn-primary">Инициализировать</button>
            <button onClick={() => startMutation.mutate()} className="btn btn-success">Старт</button>
            <button onClick={() => stopMutation.mutate()} className="btn btn-danger">Стоп</button>
            <button onClick={() => statusQuery.refetch()} className="btn">Статус</button>
          </div>
          {statusQuery.data && (
            <pre className="mt-3 text-xs text-gray-300 bg-gray-800 p-3 rounded">{JSON.stringify(statusQuery.data, null, 2)}</pre>
          )}
        </div>
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Баланс и позиции</h2>
          <div className="flex gap-3">
            <button onClick={() => balanceQuery.refetch()} className="btn">Баланс</button>
            <button onClick={() => positionsQuery.refetch()} className="btn">Позиции</button>
          </div>
          {balanceQuery.data && (
            <pre className="mt-3 text-xs text-gray-300 bg-gray-800 p-3 rounded">{JSON.stringify(balanceQuery.data, null, 2)}</pre>
          )}
          {positionsQuery.data && (
            <pre className="mt-3 text-xs text-gray-300 bg-gray-800 p-3 rounded">{JSON.stringify(positionsQuery.data, null, 2)}</pre>
          )}
        </div>
      </div>

      <div className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Ручной ордер</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm mb-1">Символ</label>
            <input className="input w-full" value={order.symbol} onChange={e => setOrder({ ...order, symbol: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm mb-1">Сторона</label>
            <select className="input w-full" value={order.side} onChange={e => setOrder({ ...order, side: e.target.value })}>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Кол-во</label>
            <input type="number" className="input w-full" value={order.amount} onChange={e => setOrder({ ...order, amount: Number(e.target.value) })} />
          </div>
          <div>
            <label className="block text-sm mb-1">Тип</label>
            <select className="input w-full" value={order.order_type} onChange={e => setOrder({ ...order, order_type: e.target.value })}>
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Цена (для Limit)</label>
            <input type="number" className="input w-full" value={order.price} onChange={e => setOrder({ ...order, price: e.target.value })} />
          </div>
        </div>
        <button onClick={() => placeOrderMutation.mutate()} className="btn btn-primary">Отправить ордер</button>
      </div>
    </div>
  );
};

export default RealTrading;
