import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface IndicatorChartProps {
  data: any[]; // Replace with specific indicator data type
  dataKey: string;
  strokeColor?: string;
}

const IndicatorChart: React.FC<IndicatorChartProps> = ({ data, dataKey, strokeColor = "#8884d8" }) => {
  return (
    <div className="h-48 w-full"> {/* Smaller height for indicator charts */}
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.2}/>
          <XAxis 
            dataKey="timestamp"  // Assuming timestamp is present
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
            }}
            minTickGap={30}
          />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke={strokeColor} dot={false} strokeWidth={2}/>
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default IndicatorChart; 