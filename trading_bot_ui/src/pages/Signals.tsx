import React, { Suspense } from 'react';

const SignalsList = React.lazy(() => import('../components/Signals/SignalsList'));
const SignalFilter = React.lazy(() => import('../components/Signals/SignalFilter'));

const SignalsPage: React.FC = () => {
  const handleFilterChange = (filters: any) => {
    console.log('Applying filters:', filters); // Placeholder
    // Here you would typically refetch signals with new filter parameters
    // or filter existing signals on the client-side if they are all loaded.
  };

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Trading Signals</h2>
      <Suspense fallback={<div className='text-center p-4'>Loading filters...</div>}>
        <SignalFilter onFilterChange={handleFilterChange} />
      </Suspense>
      <Suspense fallback={<div className='text-center p-4'>Loading signals list...</div>}>
        <SignalsList />
      </Suspense>
    </div>
  );
};

export default SignalsPage; 