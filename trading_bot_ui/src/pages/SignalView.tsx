import React, { useEffect, useState, Suspense } from 'react';
import { useParams } from 'react-router-dom';
import { Signal } from '../types/Signal';
import { Price } from '../types/Price';
import { fetchSignalById, fetchPrices } from '../utils/dataFetchers';
import { formatDate, formatPrice } from '../utils/formatters';

const PriceChart = React.lazy(() => import('../components/Charts/PriceChart'));
// const IndicatorChart = React.lazy(() => import('../components/Charts/IndicatorChart'));

const SignalView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [signal, setSignal] = useState<Signal | null | undefined>(null); // undefined for not found
  const [prices, setPrices] = useState<Price[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError('Signal ID is missing.');
      setLoading(false);
      return;
    }

    const loadSignalDetails = async () => {
      try {
        setLoading(true);
        const signalData = await fetchSignalById(id);
        setSignal(signalData);

        if (signalData) {
          const priceData = await fetchPrices(signalData.asset_pair);
          setPrices(priceData);
        } else {
          setPrices([]); // No signal, no prices to fetch for it
        }
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setSignal(null);
        setPrices([]);
      } finally {
        setLoading(false);
      }
    };

    loadSignalDetails();
  }, [id]);

  if (loading) return <div className="text-center p-8">Loading signal details...</div>;
  if (error) return <div className="text-center p-8 text-red-500">Error: {error}</div>;
  if (signal === undefined) return <div className="text-center p-8">Signal not found.</div>;
  if (!signal) return <div className="text-center p-8">No signal data.</div>; // Should be caught by undefined check mostly

  return (
    <div className="container mx-auto p-4">
      <div className="bg-white shadow-xl rounded-lg p-6">
        <div className="flex flex-col md:flex-row justify-between items-start mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-1">{signal.asset_pair}</h2>
            <span className={`text-lg font-semibold px-3 py-1 rounded-full ${signal.signal_type === 'BUY' ? 'bg-green-100 text-green-700' : signal.signal_type === 'SELL' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
              {signal.signal_type}
            </span>
          </div>
          <div className="text-right mt-4 md:mt-0">
            <p className="text-sm text-gray-500">Created: {formatDate(signal.created_at)}</p>
            <p className="text-lg font-medium text-blue-600">Confidence: {(signal.confidence_score * 100).toFixed(0)}%</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-700 mb-3">Signal Details</h3>
            <p><strong className="text-gray-600">Price at Signal:</strong> {formatPrice(signal.price_at_signal)}</p>
            {signal.target_price && <p><strong className="text-gray-600">Target Price:</strong> <span className="text-green-600">{formatPrice(signal.target_price)}</span></p>}
            {signal.stop_loss && <p><strong className="text-gray-600">Stop Loss:</strong> <span className="text-red-600">{formatPrice(signal.stop_loss)}</span></p>}
          </div>
          <div>
            <h3 className="text-xl font-semibold text-gray-700 mb-3">XAI Explanation</h3>
            <p className="text-gray-700 italic bg-gray-50 p-3 rounded">
              {signal.xai_explanation || 'No explanation available.'}
            </p>
          </div>
        </div>
        
        {signal.technical_indicators && Object.keys(signal.technical_indicators).length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-700 mb-3">Technical Indicators</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 bg-gray-50 p-3 rounded">
              {Object.entries(signal.technical_indicators).map(([key, value]) => (
                <div key={key} className="text-sm">
                  <strong className="text-gray-600">{key}:</strong> {typeof value === 'number' ? value.toFixed(2) : value}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-700 mb-3">Price Chart</h3>
          <Suspense fallback={<div className='text-center p-4'>Loading chart...</div>}>
            {prices.length > 0 ? (
              <PriceChart 
                prices={prices} 
                entryPrice={signal.price_at_signal}
                targetPrice={signal.target_price}
                stopLoss={signal.stop_loss}
              />
            ) : (
              <p className="text-center text-gray-500">Price data not available for this asset or timeframe.</p>
            )}
          </Suspense>
        </div>

        {/* Placeholder for Indicator Charts */}
        {/* <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-700 mb-3">Indicator Charts</h3>
          <Suspense fallback={<div>Loading indicator charts...</div>}>
            <IndicatorChart data={prices} dataKey="RSI_like_data_here" />
          </Suspense>
        </div> */}
      </div>
    </div>
  );
};

export default SignalView; 