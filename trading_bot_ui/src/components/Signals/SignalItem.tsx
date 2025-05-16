import React from 'react';
import { Link } from 'react-router-dom';
import { formatDate, formatPrice } from '../../utils/formatters'; // Adjusted path
import { Signal } from '../../types/Signal'; // Adjusted path

interface SignalItemProps {
  signal: Signal;
}

const SignalItem: React.FC<SignalItemProps> = React.memo(({ signal }) => {
  // const getSignalTypeColor = (type: string) => {
  //   switch (type) {
  //     case 'BUY':
  //       return 'text-green-600';
  //     case 'SELL':
  //       return 'text-red-600';
  //     default:
  //       return 'text-gray-600';
  //   }
  // };

  return (
    <Link 
      to={`/signals/${signal.id}`}
      className="block p-4 border rounded-lg mb-2 hover:bg-gray-50 transition-colors shadow-sm"
    >
      <div className="flex flex-col sm:flex-row justify-between sm:items-center">
        <div className="mb-2 sm:mb-0">
          <h3 className="font-medium text-lg text-blue-600 hover:text-blue-700">{signal.asset_pair}</h3>
          <p className="text-xs text-gray-500">
            {formatDate(signal.created_at)}
          </p>
        </div>
        <div className="flex items-center">
          <span className={`font-bold text-sm px-3 py-1 rounded-full ${signal.signal_type === 'BUY' ? 'bg-green-100 text-green-700' : signal.signal_type === 'SELL' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
            {signal.signal_type}
          </span>
          <span className="ml-3 bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">
            Confidence: {(signal.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      <div className="mt-2 text-sm">
        <span className="text-gray-600">Price: </span>
        <span className="font-medium">{formatPrice(signal.price_at_signal)}</span>
        {signal.target_price && (
          <>
            <span className="text-gray-600 ml-2">Target: </span>
            <span className="font-medium text-green-600">{formatPrice(signal.target_price)}</span>
          </>
        )}
         {signal.stop_loss && (
          <>
            <span className="text-gray-600 ml-2">Stop: </span>
            <span className="font-medium text-red-600">{formatPrice(signal.stop_loss)}</span>
          </>
        )}
      </div>
    </Link>
  );
});

export default SignalItem; 