-- Create AI Analysis History table
CREATE TABLE public.ai_analysis_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query TEXT NOT NULL,
  symbol TEXT,
  sentiment TEXT,
  recommendation TEXT,
  confidence TEXT,
  analysis TEXT,
  market_score DECIMAL(5,2),
  risk_level TEXT,
  market_trend TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create Trade History table
CREATE TABLE public.trade_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL,
  action TEXT NOT NULL,
  amount DECIMAL(20,8) NOT NULL,
  price DECIMAL(20,8) NOT NULL,
  confidence TEXT,
  reasoning TEXT,
  sentiment TEXT,
  executed BOOLEAN DEFAULT false,
  execution_result TEXT,
  order_id TEXT,
  pnl DECIMAL(20,8),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS (but allow all access since no auth yet)
ALTER TABLE public.ai_analysis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trade_history ENABLE ROW LEVEL SECURITY;

-- Create permissive policies (no auth in app yet)
CREATE POLICY "Allow all access to ai_analysis_history" 
ON public.ai_analysis_history 
FOR ALL 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow all access to trade_history" 
ON public.trade_history 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- Create indexes for better query performance
CREATE INDEX idx_ai_analysis_created_at ON public.ai_analysis_history(created_at DESC);
CREATE INDEX idx_ai_analysis_symbol ON public.ai_analysis_history(symbol);
CREATE INDEX idx_trade_history_created_at ON public.trade_history(created_at DESC);
CREATE INDEX idx_trade_history_symbol ON public.trade_history(symbol);