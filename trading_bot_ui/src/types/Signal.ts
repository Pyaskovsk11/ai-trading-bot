export interface Signal {
  id: string;
  asset_pair: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  confidence_score: number;
  price_at_signal: number;
  target_price?: number;
  stop_loss?: number;
  created_at: string; // ISO date string
  xai_explanation?: string;
  technical_indicators?: Record<string, number | string>;
} 