import { Signal } from '../types/Signal';
import { Price } from '../types/Price';
import { Stats } from '../types/Stats';

const API_BASE = '/data'; // Assuming mock data is in public/data

export const fetchSignals = async (): Promise<Signal[]> => {
  const response = await fetch(`${API_BASE}/signals.json`);
  if (!response.ok) {
    throw new Error('Failed to fetch signals');
  }
  return response.json();
};

export const fetchSignalById = async (id: string): Promise<Signal | undefined> => {
  const signals = await fetchSignals();
  return signals.find(signal => signal.id === id);
};

// Prices are per asset pair in prices.json
export const fetchPrices = async (assetPair: string): Promise<Price[]> => {
  const response = await fetch(`${API_BASE}/prices.json`);
  if (!response.ok) {
    throw new Error('Failed to fetch prices');
  }
  const allPrices = await response.json();
  return allPrices[assetPair] || [];
};

export const fetchStats = async (): Promise<Stats> => {
  const response = await fetch(`${API_BASE}/stats.json`);
  if (!response.ok) {
    throw new Error('Failed to fetch stats');
  }
  return response.json();
}; 