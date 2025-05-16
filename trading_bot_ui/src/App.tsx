import React, { Suspense } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link
} from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import './index.css'; // Ensure Tailwind is imported

const Home = React.lazy(() => import('./pages/Home'));
const SignalsPage = React.lazy(() => import('./pages/Signals'));
const SignalView = React.lazy(() => import('./pages/SignalView'));

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Header />
        <nav className="bg-white shadow-sm mb-4">
          <div className="container mx-auto px-4 py-2 flex space-x-4">
            <Link to="/" className="text-blue-600 hover:text-blue-800 py-2 px-3 rounded-md hover:bg-blue-50 transition-colors">Dashboard</Link>
            <Link to="/signals" className="text-blue-600 hover:text-blue-800 py-2 px-3 rounded-md hover:bg-blue-50 transition-colors">Signals</Link>
          </div>
        </nav>
        <main className="flex-grow container mx-auto px-4">
          <Suspense fallback={<div className='text-center text-xl p-10'>Loading page...</div>}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/signals" element={<SignalsPage />} />
              <Route path="/signals/:id" element={<SignalView />} />
            </Routes>
          </Suspense>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
