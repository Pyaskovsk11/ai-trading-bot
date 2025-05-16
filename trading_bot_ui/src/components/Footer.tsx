import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-100 text-center text-sm p-4 mt-8 border-t">
      <p>&copy; {new Date().getFullYear()} AI Trading Bot. All rights reserved.</p>
      <p className="text-xs text-gray-500">For demonstration purposes only.</p>
    </footer>
  );
};

export default Footer; 