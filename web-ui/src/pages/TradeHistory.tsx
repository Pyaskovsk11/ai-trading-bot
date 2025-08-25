import React from 'react';
import { useQuery } from '@tanstack/react-query';

const TradeHistory: React.FC = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['trade-history'],
    queryFn: async () => {
      const res = await fetch('/api/v1/real-trading/trade-history');
      return res.json();
    },
    refetchOnWindowFocus: false,
  });

  const items = data?.history || [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">История сделок</h1>
        <button onClick={() => refetch()} className="btn">Обновить</button>
      </div>
      <div className="card p-4 overflow-auto">
        <table className="min-w-full text-sm text-gray-300">
          <thead>
            <tr className="text-left border-b border-gray-700">
              <th className="py-2 pr-4">Время</th>
              <th className="py-2 pr-4">Тип</th>
              <th className="py-2 pr-4">Символ</th>
              <th className="py-2 pr-4">Сторона</th>
              <th className="py-2 pr-4">Кол-во</th>
              <th className="py-2 pr-4">Цена</th>
              <th className="py-2 pr-4">P&L</th>
              <th className="py-2 pr-4">Комментарий</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td className="py-3" colSpan={8}>Загрузка...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="py-3" colSpan={8}>Нет сделок</td></tr>
            ) : (
              items.slice().reverse().map((t: any, idx: number) => (
                <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="py-2 pr-4">{t.timestamp}</td>
                  <td className="py-2 pr-4">{t.type}</td>
                  <td className="py-2 pr-4">{t.symbol}</td>
                  <td className="py-2 pr-4">{t.side}</td>
                  <td className="py-2 pr-4">{t.quantity}</td>
                  <td className="py-2 pr-4">{t.price || t.close_price || '-'}</td>
                  <td className={`py-2 pr-4 ${t.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{t.realized_pnl ?? '-'}</td>
                  <td className="py-2 pr-4">{t.reason || ''}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TradeHistory;
