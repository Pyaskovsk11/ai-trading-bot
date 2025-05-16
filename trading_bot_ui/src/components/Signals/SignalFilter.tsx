import React from 'react';

interface SignalFilterProps {
  // TODO: Define filter options and callback
  onFilterChange: (filters: any) => void;
}

const SignalFilter: React.FC<SignalFilterProps> = ({ onFilterChange }) => {
  // Basic filter inputs - can be expanded significantly
  return (
    <div className="p-4 mb-4 bg-gray-50 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-3">Filter Signals</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="asset-filter" className="block text-sm font-medium text-gray-700">Asset Pair</label>
          <input 
            type="text" 
            id="asset-filter"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="e.g., BTC/USD"
            // onChange={e => onFilterChange({ asset: e.target.value })} // Simplified
          />
        </div>
        <div>
          <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700">Signal Type</label>
          <select 
            id="type-filter"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            // onChange={e => onFilterChange({ type: e.target.value })} // Simplified
          >
            <option value="">All Types</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
            <option value="HOLD">HOLD</option>
          </select>
        </div>
        {/* Add more filters like date range, confidence score, etc. */}
      </div>
       {/* <button 
        onClick={() => onFilterChange({})} // Example: Clear filters
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Apply Filters (Not Implemented)
      </button> */}
    </div>
  );
};

export default SignalFilter; 