-- Trading Sentinel Database Schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====== CORE SCHEMA ======

-- Markets table
CREATE TABLE markets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  type TEXT NOT NULL, -- 'stock', 'crypto', 'forex'
  exchange TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- OHLCV Candles (TimescaleDB for time-series optimization)
CREATE TABLE candles (
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  open DECIMAL(18, 8) NOT NULL,
  high DECIMAL(18, 8) NOT NULL,
  low DECIMAL(18, 8) NOT NULL,
  close DECIMAL(18, 8) NOT NULL,
  volume BIGINT NOT NULL,
  PRIMARY KEY (market_id, timestamp)
);

-- Technical Indicators (pre-computed for speed)
CREATE TABLE indicators (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  rsi DECIMAL(5, 2), -- Relative Strength Index (0-100)
  macd DECIMAL(18, 8), -- MACD value
  macd_signal DECIMAL(18, 8),
  bb_upper DECIMAL(18, 8), -- Bollinger Bands upper
  bb_lower DECIMAL(18, 8), -- Bollinger Bands lower
  bb_middle DECIMAL(18, 8),
  sma_20 DECIMAL(18, 8), -- Simple Moving Average 20-day
  sma_50 DECIMAL(18, 8),
  sma_200 DECIMAL(18, 8),
  volume_sma BIGINT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (market_id, timestamp)
);

-- AI Predictions
CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  sentiment TEXT NOT NULL, -- 'bull', 'bear', 'neutral'
  confidence DECIMAL(5, 2) NOT NULL, -- 0-100
  bull_score DECIMAL(5, 2), -- Bull %
  bear_score DECIMAL(5, 2), -- Bear %
  reasoning TEXT, -- Why bull/bear
  features JSONB, -- Feature importance map
  model_version TEXT,
  accuracy_on_backtest DECIMAL(5, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  name TEXT,
  telegram_user_id TEXT,
  subscription_tier TEXT DEFAULT 'free', -- 'free', 'pro', 'api'
  subscription_expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Watchlists
CREATE TABLE watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  entry_price DECIMAL(18, 8),
  target_price DECIMAL(18, 8),
  stop_loss DECIMAL(18, 8),
  alert_on_flip BOOLEAN DEFAULT TRUE,
  last_sentiment TEXT, -- Previous sentiment (to detect flips)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, market_id)
);

-- Trade History (for backtesting accuracy)
CREATE TABLE backtest_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  initial_capital DECIMAL(18, 2),
  final_capital DECIMAL(18, 2),
  total_return DECIMAL(5, 2), -- %
  win_rate DECIMAL(5, 2),
  num_trades INT,
  max_drawdown DECIMAL(5, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  watchlist_id UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
  alert_type TEXT NOT NULL, -- 'sentiment_flip', 'price_target', 'stop_loss'
  triggered_at TIMESTAMPTZ,
  sent BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id UUID,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====== INDEXES ======
CREATE INDEX idx_candles_market_timestamp ON candles(market_id, timestamp DESC);
CREATE INDEX idx_indicators_market_timestamp ON indicators(market_id, timestamp DESC);
CREATE INDEX idx_predictions_market_timestamp ON predictions(market_id, timestamp DESC);
CREATE INDEX idx_watchlists_user ON watchlists(user_id);
CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_alerts_triggered ON alerts(triggered_at) WHERE sent = FALSE;
CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);

-- ====== ROW-LEVEL SECURITY (RLS) ======
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;

-- Watchlists: Users see only their own
CREATE POLICY watchlist_user_isolation ON watchlists
  USING (user_id = (SELECT id FROM users WHERE email = current_user));

-- Alerts: Users see only their own
CREATE POLICY alert_user_isolation ON alerts
  USING (user_id = (SELECT id FROM users WHERE email = current_user));

-- Backtest: Users see only their own
CREATE POLICY backtest_user_isolation ON backtest_results
  USING (user_id = (SELECT id FROM users WHERE email = current_user));
