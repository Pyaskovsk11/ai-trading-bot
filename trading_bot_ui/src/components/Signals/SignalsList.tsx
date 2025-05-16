import React, { useEffect, useState } from 'react';
import { Signal } from '../../types/Signal';
import { fetchSignals } from '../../utils/dataFetchers';
import SignalItem from './SignalItem';
// import { FixedSizeList } from 'react-window'; // For virtualization

// TODO: Implement filtering and sorting
// interface SignalFilterProps {
//   onFilterChange: (filters: any) => void;
// }
// const SignalFilter: React.FC<SignalFilterProps> = ({ onFilterChange }) => {
//   return <div>Filter controls here</div>;
// };

const SignalsList: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSignals = async () => {
      try {
        setLoading(true);
        const data = await fetchSignals();
        setSignals(data);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
        setSignals([]);
      } finally {
        setLoading(false);
      }
    };
    loadSignals();
  }, []);

  if (loading) return <div className="text-center p-4">Loading signals...</div>;
  if (error) return <div className="text-center p-4 text-red-500">Error: {error}</div>;
  if (signals.length === 0) return <div className="text-center p-4">No signals found.</div>;

  // Basic list rendering, virtualization can be added later for performance
  return (
    <div className="space-y-3">
      {/* <SignalFilter onFilterChange={() => {}} /> */}
      {signals.map(signal => (
        <SignalItem key={signal.id} signal={signal} />
      ))}
      {/* TODO: Add pagination controls */}
    </div>
  );
};

export default SignalsList; 