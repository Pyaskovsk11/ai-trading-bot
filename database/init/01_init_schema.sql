-- AI Trading Bot Database Schema
-- PostgreSQL initialization script

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS logs;

-- Set default schema
SET search_path TO trading, public;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT,
    secret_key_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}',
    risk_profile VARCHAR(20) DEFAULT 'moderate' CHECK (risk_profile IN ('conservative', 'moderate', 'aggressive')),
    max_daily_loss DECIMAL(10,2) DEFAULT 1000.00,
    max_position_size DECIMAL(10,2) DEFAULT 10000.00
);

-- Trading pairs table
CREATE TABLE IF NOT EXISTS trading_pairs (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    base_asset VARCHAR(10) NOT NULL,
    quote_asset VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    min_quantity DECIMAL(20,8),
    max_quantity DECIMAL(20,8),
    step_size DECIMAL(20,8),
    tick_size DECIMAL(20,8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Market data table (partitioned by date)
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create partitions for market data (current year and next year)
CREATE TABLE IF NOT EXISTS market_data_2025 PARTITION OF market_data
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS market_data_2026 PARTITION OF market_data
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    total_value DECIMAL(20,8) DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,
    total_pnl_percent DECIMAL(10,4) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio positions table
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    average_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8),
    market_value DECIMAL(20,8),
    unrealized_pnl DECIMAL(20,8),
    unrealized_pnl_percent DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trading orders table
CREATE TABLE IF NOT EXISTS trading_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    type VARCHAR(20) NOT NULL CHECK (type IN ('market', 'limit', 'stop', 'stop_limit')),
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8),
    stop_price DECIMAL(20,8),
    filled_quantity DECIMAL(20,8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'cancelled', 'rejected', 'expired')),
    exchange_order_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP WITH TIME ZONE
);

-- Trading signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('buy', 'sell', 'hold')),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    source VARCHAR(50) NOT NULL,
    model_name VARCHAR(100),
    features JSONB,
    signal_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- ML model performance table
CREATE TABLE IF NOT EXISTS ml_model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    training_samples INTEGER,
    validation_samples INTEGER,
    training_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    hyperparameters JSONB,
    metrics JSONB
);

-- Analytics schema tables
SET search_path TO analytics, public;

-- Daily portfolio snapshots
CREATE TABLE IF NOT EXISTS daily_portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL,
    snapshot_date DATE NOT NULL,
    total_value DECIMAL(20,8) NOT NULL,
    total_pnl DECIMAL(20,8) NOT NULL,
    total_pnl_percent DECIMAL(10,4) NOT NULL,
    positions JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, snapshot_date)
);

-- Trading performance metrics
CREATE TABLE IF NOT EXISTS trading_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,
    max_drawdown DECIMAL(10,4) DEFAULT 0,
    sharpe_ratio DECIMAL(10,4),
    win_rate DECIMAL(5,4),
    avg_win DECIMAL(20,8),
    avg_loss DECIMAL(20,8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Logs schema tables
SET search_path TO logs, public;

-- Application logs
CREATE TABLE IF NOT EXISTS app_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(10) NOT NULL,
    logger VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER,
    user_id UUID,
    session_id VARCHAR(100),
    request_id VARCHAR(100),
    extra_data JSONB
);

-- API request logs
CREATE TABLE IF NOT EXISTS api_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_size INTEGER,
    response_size INTEGER,
    error_message TEXT
);

-- Reset to trading schema
SET search_path TO trading, public;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_id ON portfolio_positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_symbol ON portfolio_positions(symbol);

CREATE INDEX IF NOT EXISTS idx_trading_orders_user_id ON trading_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_orders_symbol ON trading_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_orders_status ON trading_orders(status);
CREATE INDEX IF NOT EXISTS idx_trading_orders_created_at ON trading_orders(created_at);

CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_signals_created_at ON trading_signals(created_at);
CREATE INDEX IF NOT EXISTS idx_trading_signals_signal_type ON trading_signals(signal_type);

CREATE INDEX IF NOT EXISTS idx_ml_model_performance_model_name ON ml_model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_ml_model_performance_symbol ON ml_model_performance(symbol);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_daily_snapshots_portfolio_date ON analytics.daily_portfolio_snapshots(portfolio_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_trading_performance_user_period ON analytics.trading_performance(user_id, period_start, period_end);

-- Logs indexes
CREATE INDEX IF NOT EXISTS idx_app_logs_timestamp ON logs.app_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_app_logs_level ON logs.app_logs(level);
CREATE INDEX IF NOT EXISTS idx_app_logs_user_id ON logs.app_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON logs.api_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_path ON logs.api_logs(path);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON logs.api_logs(user_id);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolio_positions_updated_at BEFORE UPDATE ON portfolio_positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_orders_updated_at BEFORE UPDATE ON trading_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default trading pairs
INSERT INTO trading_pairs (symbol, base_asset, quote_asset, min_quantity, max_quantity, step_size, tick_size) VALUES
('BTC-USDT', 'BTC', 'USDT', 0.00001, 1000, 0.00001, 0.01),
('ETH-USDT', 'ETH', 'USDT', 0.0001, 10000, 0.0001, 0.01),
('BNB-USDT', 'BNB', 'USDT', 0.001, 100000, 0.001, 0.001),
('ADA-USDT', 'ADA', 'USDT', 0.1, 1000000, 0.1, 0.0001),
('SOL-USDT', 'SOL', 'USDT', 0.001, 100000, 0.001, 0.001),
('DOT-USDT', 'DOT', 'USDT', 0.01, 100000, 0.01, 0.001),
('MATIC-USDT', 'MATIC', 'USDT', 0.1, 1000000, 0.1, 0.0001),
('AVAX-USDT', 'AVAX', 'USDT', 0.01, 100000, 0.01, 0.001),
('LINK-USDT', 'LINK', 'USDT', 0.01, 100000, 0.01, 0.001),
('UNI-USDT', 'UNI', 'USDT', 0.01, 100000, 0.01, 0.001)
ON CONFLICT (symbol) DO NOTHING;

-- Create a default admin user (password: admin123)
-- Note: In production, this should be changed immediately
INSERT INTO users (username, email, password_hash, settings) VALUES
('admin', 'admin@tradingbot.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W', '{"role": "admin", "theme": "dark"}')
ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA trading TO trading_user;
GRANT USAGE ON SCHEMA analytics TO trading_user;
GRANT USAGE ON SCHEMA logs TO trading_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trading TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA logs TO trading_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA trading TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA logs TO trading_user; 