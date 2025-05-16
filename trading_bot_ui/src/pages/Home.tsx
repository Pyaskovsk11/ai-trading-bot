import React, { useEffect, useState, Suspense } from 'react';
import { Stats } from '../types/Stats';
import { Price } from '../types/Price';
import { fetchStats, fetchPrices } from '../utils/dataFetchers';

const StatCard = React.lazy(() => import('../components/Dashboard/StatCard'));
const SignalTypeDistribution = React.lazy(() => import('../components/Dashboard/SignalTypeDistribution'));
const SuccessRateChart = React.lazy(() => import('../components/Dashboard/SuccessRateChart'));
const PriceChart = React.lazy(() => import('../components/Charts/PriceChart'));

const Home: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [btcPrices, setBtcPrices] = useState<Price[]>([]);
  const [ethPrices, setEthPrices] = useState<Price[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const statsData = await fetchStats();
        setStats(statsData);
        const btcPriceData = await fetchPrices('BTC/USD');
        setBtcPrices(btcPriceData);
        const ethPriceData = await fetchPrices('ETH/USD');
        setEthPrices(ethPriceData);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  if (loading) return <div className="text-center p-8">Loading dashboard...</div>;
  if (error) return <div className="text-center p-8 text-red-500">Error loading dashboard: {error}</div>;
  if (!stats) return <div className="text-center p-8">No stats data available.</div>;

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Dashboard</h2>
      <Suspense fallback={<div className='text-center p-4'>Loading cards...</div>}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard title="Active Signals" value={stats.active_signals} />
          <StatCard title="Success Rate" value={`${(stats.success_rate * 100).toFixed(1)}%`} />
          <StatCard title="Total PNL" value={stats.overall_pnl ? `$${stats.overall_pnl.toFixed(2)}` : 'N/A'} />
          {/* Add another relevant stat card here if needed */}
        </div>
      </Suspense>

      <Suspense fallback={<div className='text-center p-4'>Loading charts...</div>}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <SignalTypeDistribution distribution={stats.signal_distribution} />
          <SuccessRateChart successRate={stats.success_rate} />
        </div>

        <h3 className="text-xl font-semibold text-gray-700 mb-4">Key Asset Prices</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white shadow-lg rounded-lg p-4">
            <h4 className="text-md font-semibold mb-2 text-gray-700">BTC/USD</h4>
            {btcPrices.length > 0 ? <PriceChart prices={btcPrices} /> : <p>No BTC price data.</p>}
          </div>
          <div className="bg-white shadow-lg rounded-lg p-4">
            <h4 className="text-md font-semibold mb-2 text-gray-700">ETH/USD</h4>
            {ethPrices.length > 0 ? <PriceChart prices={ethPrices} /> : <p>No ETH price data.</p>}
          </div>
        </div>
      </Suspense>
    </div>
  );
};

export default Home; 