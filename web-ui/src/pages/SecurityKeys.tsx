import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const SecurityKeys: React.FC = () => {
  const [exchange, setExchange] = useState('bingx');
  const [apiKey, setApiKey] = useState('');
  const [secret, setSecret] = useState('');
  const [testnet, setTestnet] = useState(true);

  const listQuery = useQuery({
    queryKey: ['keys-list'],
    queryFn: async () => (await fetch('/api/v1/security/keys')).json(),
  });

  const saveMutation = useMutation(async () => {
    const res = await fetch('/api/v1/security/keys/save', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exchange, api_key: apiKey, secret, testnet }),
    });
    return res.json();
  }, {
    onSuccess: () => { toast.success('Ключи сохранены'); listQuery.refetch(); setApiKey(''); setSecret(''); },
    onError: () => toast.error('Ошибка сохранения ключей'),
  });

  const deleteMutation = useMutation(async (ex: string) => {
    const res = await fetch(`/api/v1/security/keys/${ex}`, { method: 'DELETE' });
    return res.json();
  }, {
    onSuccess: () => { toast.success('Ключи удалены'); listQuery.refetch(); },
    onError: () => toast.error('Ошибка удаления ключей'),
  });

  const items = listQuery.data?.items || [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">API-ключи</h1>
        <button className="btn" onClick={() => listQuery.refetch()}>Обновить</button>
      </div>

      <div className="card p-4 space-y-3">
        <h2 className="text-lg font-semibold">Сохранить ключи</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1">Биржа</label>
            <select className="input w-full" value={exchange} onChange={e => setExchange(e.target.value)}>
              <option value="bingx">BingX</option>
              <option value="binance">Binance</option>
              <option value="bybit">Bybit</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Тестнет</label>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" checked={testnet} onChange={e => setTestnet(e.target.checked)} />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          <div>
            <label className="block text-sm mb-1">API Key</label>
            <input type="password" className="input w-full" value={apiKey} onChange={e => setApiKey(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm mb-1">Secret</label>
            <input type="password" className="input w-full" value={secret} onChange={e => setSecret(e.target.value)} />
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => saveMutation.mutate()}>Сохранить</button>
      </div>

      <div className="card p-4 space-y-3">
        <h2 className="text-lg font-semibold">Сохранённые ключи</h2>
        {items.length === 0 ? <div className="text-gray-400">Нет сохранённых ключей</div> : (
          <ul className="space-y-2">
            {items.map((it: any) => (
              <li key={it.exchange} className="flex items-center justify-between bg-gray-800 rounded p-3">
                <div>
                  <div className="font-medium">{it.exchange}</div>
                  <div className="text-xs text-gray-400">{it.testnet ? 'Testnet' : 'Live'} • {it.created_at}</div>
                </div>
                <button className="btn btn-danger" onClick={() => deleteMutation.mutate(it.exchange)}>Удалить</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SecurityKeys;
