export interface SignalDistribution {
  BUY: number;
  SELL: number;
  HOLD: number;
}

export interface Stats {
  active_signals: number;
  signal_distribution: SignalDistribution;
  success_rate: number;
  overall_pnl?: number; // Assuming PNL might not always be present
} 