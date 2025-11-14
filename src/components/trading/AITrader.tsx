import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Brain, TrendingUp, TrendingDown, Pause, Play, AlertCircle, DollarSign, Activity, Target } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Badge } from "@/components/ui/badge";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface AIDecision {
  action: 'buy' | 'sell' | 'hold';
  symbol: string;
  confidence: string;
  amount: number;
  reasoning: string;
  sentiment: string;
  technicals?: {
    pricePosition: number;
    volatility: number;
    volumeStrength: number;
  };
}

interface TradeLog {
  timestamp: string;
  decision: AIDecision;
  executed: boolean;
  message?: string;
}

interface PerformanceMetrics {
  totalPnL: number;
  winRate: number;
  totalTrades: number;
  executedTrades: number;
  avgTradeSize: number;
}

const AITrader = () => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [autoExecute, setAutoExecute] = useState(false);
  const [currentDecision, setCurrentDecision] = useState<AIDecision | null>(null);
  const [tradeLogs, setTradeLogs] = useState<TradeLog[]>([]);
  const [marketData, setMarketData] = useState<any[]>([]);
  const [performance, setPerformance] = useState<PerformanceMetrics>({
    totalPnL: 0,
    winRate: 0,
    totalTrades: 0,
    executedTrades: 0,
    avgTradeSize: 0
  });
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    loadTradeHistory();
  }, []);

  const loadTradeHistory = async () => {
    const { data } = await supabase
      .from('trade_history')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50);
    
    if (data) {
      // Calculate performance metrics
      const executed = data.filter(t => t.executed);
      const totalPnL = executed.reduce((sum, t) => sum + (t.pnl || 0), 0);
      const wins = executed.filter(t => (t.pnl || 0) > 0).length;
      const winRate = executed.length > 0 ? (wins / executed.length) * 100 : 0;
      const avgSize = executed.length > 0 
        ? executed.reduce((sum, t) => sum + t.amount, 0) / executed.length 
        : 0;

      setPerformance({
        totalPnL,
        winRate,
        totalTrades: data.length,
        executedTrades: executed.length,
        avgTradeSize: avgSize
      });

      // Create PnL timeline
      let runningPnL = 0;
      const timeline = executed.reverse().map(t => {
        runningPnL += t.pnl || 0;
        return {
          time: new Date(t.created_at).toLocaleTimeString(),
          pnl: runningPnL,
          trade: `${t.action} ${t.symbol}`
        };
      });
      setPnlHistory(timeline);
    }
  };

  const showNotification = (title: string, description: string, variant: 'default' | 'destructive' = 'default') => {
    toast({ title, description, variant });
    
    // Browser notification if permission granted
    if (Notification.permission === 'granted') {
      new Notification(title, { body: description });
    }
  };

  const analyzeMarket = async () => {
    setIsAnalyzing(true);
    try {
      const { data, error } = await supabase.functions.invoke('ai-trader', {
        body: { action: 'analyze' },
      });

      if (error) throw error;

      setCurrentDecision(data.decision);
      setMarketData(data.marketData);

      // Log the analysis
      const newLog: TradeLog = {
        timestamp: new Date().toISOString(),
        decision: data.decision,
        executed: false,
      };
      setTradeLogs(prev => [newLog, ...prev].slice(0, 10));

      // Reload trade history
      await loadTradeHistory();

      // Auto-execute if enabled and confidence is high
      if (autoExecute && data.decision.confidence === 'high' && data.decision.action !== 'hold') {
        showNotification(
          "Auto-Executing Trade",
          `Executing ${data.decision.action} for ${data.decision.symbol}`,
        );
        await executeTrade(data.decision);
      } else if (data.decision.action !== 'hold') {
        showNotification(
          "New Trading Signal",
          `AI recommends: ${data.decision.action.toUpperCase()} ${data.decision.symbol}`,
        );
      }

      toast({
        title: "Analysis Complete",
        description: `AI recommends: ${data.decision.action.toUpperCase()} ${data.decision.symbol}`,
      });

    } catch (error: any) {
      console.error('Analysis error:', error);
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to analyze market",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const executeTrade = async (decision: AIDecision) => {
    try {
      const { data, error } = await supabase.functions.invoke('ai-trader', {
        body: { action: 'execute', decision },
      });

      if (error) throw error;

      // Update the last log entry
      setTradeLogs(prev => {
        const updated = [...prev];
        if (updated[0]) {
          updated[0] = { ...updated[0], executed: true, message: data.message };
        }
        return updated;
      });

      // Reload trade history
      await loadTradeHistory();

      showNotification(
        "Trade Executed Successfully",
        data.message,
      );

      toast({
        title: "Trade Executed",
        description: data.message,
      });

    } catch (error: any) {
      console.error('Execution error:', error);
      toast({
        title: "Trade Failed",
        description: error.message || "Failed to execute trade",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    // Request notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    let interval: NodeJS.Timeout;
    
    if (isEnabled) {
      // Analyze immediately when enabled
      analyzeMarket();
      
      // Then analyze every 5 minutes
      interval = setInterval(() => {
        analyzeMarket();
      }, 5 * 60 * 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isEnabled, autoExecute]);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'text-success';
      case 'bearish': return 'text-danger';
      default: return 'text-muted-foreground';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'buy': return <TrendingUp className="h-4 w-4 text-success" />;
      case 'sell': return <TrendingDown className="h-4 w-4 text-danger" />;
      default: return <Pause className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Brain className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-3xl font-bold">AI Trading Engine</h2>
          <p className="text-muted-foreground">Automated trading based on AI market analysis</p>
        </div>
      </div>

      {/* Performance Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
              performance.totalPnL >= 0 ? 'bg-success/20' : 'bg-danger/20'
            }`}>
              <DollarSign className={`h-5 w-5 ${
                performance.totalPnL >= 0 ? 'text-success' : 'text-danger'
              }`} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total P&L</p>
              <p className={`text-lg font-bold ${
                performance.totalPnL >= 0 ? 'text-success' : 'text-danger'
              }`}>
                ${performance.totalPnL.toFixed(2)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
              <Target className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Win Rate</p>
              <p className="text-lg font-bold">{performance.winRate.toFixed(1)}%</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-accent/20 flex items-center justify-center">
              <Activity className="h-5 w-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Trades</p>
              <p className="text-lg font-bold">{performance.totalTrades}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-muted/20 flex items-center justify-center">
              <Brain className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Executed</p>
              <p className="text-lg font-bold">{performance.executedTrades}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* P&L Timeline Chart */}
      {pnlHistory.length > 0 && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-lg font-bold mb-4">P&L Timeline</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={pnlHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))' 
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="pnl" 
                stroke="hsl(var(--primary))" 
                strokeWidth={2}
                dot={{ fill: 'hsl(var(--primary))' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Control Panel */}
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-lg font-bold mb-4">Control Panel</h3>
          
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>AI Trading Engine</Label>
                <p className="text-sm text-muted-foreground">
                  {isEnabled ? 'Active - Analyzing markets' : 'Inactive'}
                </p>
              </div>
              <Switch
                checked={isEnabled}
                onCheckedChange={setIsEnabled}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-Execute Trades</Label>
                <p className="text-sm text-muted-foreground">
                  Execute high-confidence trades automatically
                </p>
              </div>
              <Switch
                checked={autoExecute}
                onCheckedChange={setAutoExecute}
                disabled={!isEnabled}
              />
            </div>

            <div className="flex gap-2">
              <Button
                onClick={analyzeMarket}
                disabled={!isEnabled || isAnalyzing}
                className="flex-1"
              >
                {isAnalyzing ? "Analyzing..." : "Analyze Now"}
              </Button>
              
              {currentDecision && currentDecision.action !== 'hold' && (
                <Button
                  onClick={() => executeTrade(currentDecision)}
                  disabled={isAnalyzing}
                  variant="outline"
                  className="flex-1"
                >
                  Execute Trade
                </Button>
              )}
            </div>

            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-warning mt-0.5" />
                <div className="text-sm">
                  <p className="font-semibold text-warning mb-1">Risk Warning</p>
                  <p className="text-muted-foreground">
                    AI trading involves significant risk. The AI makes decisions based on market data but cannot predict the future. Only enable auto-execution with funds you can afford to lose.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Current Analysis */}
        {currentDecision && (
          <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
            <h3 className="text-lg font-bold mb-4">Current Analysis</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Action</span>
                <div className="flex items-center gap-2">
                  {getActionIcon(currentDecision.action)}
                  <span className="font-bold text-lg uppercase">{currentDecision.action}</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Symbol</span>
                <span className="font-semibold">{currentDecision.symbol}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Confidence</span>
                <Badge variant={currentDecision.confidence === 'high' ? 'default' : 'secondary'}>
                  {currentDecision.confidence.toUpperCase()}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Amount</span>
                <span className="font-semibold">{currentDecision.amount.toFixed(4)}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Sentiment</span>
                <span className={`font-semibold capitalize ${getSentimentColor(currentDecision.sentiment)}`}>
                  {currentDecision.sentiment}
                </span>
              </div>

              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground mb-2">AI Reasoning:</p>
                <p className="text-sm">{currentDecision.reasoning}</p>
              </div>

              {currentDecision.technicals && (
                <div className="pt-4 border-t border-border">
                  <p className="text-sm text-muted-foreground mb-2">Technical Indicators:</p>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center p-2 bg-background/50 rounded">
                      <p className="text-xs text-muted-foreground">Price Position</p>
                      <p className="text-sm font-semibold">{currentDecision.technicals.pricePosition}%</p>
                    </div>
                    <div className="text-center p-2 bg-background/50 rounded">
                      <p className="text-xs text-muted-foreground">Volatility</p>
                      <p className="text-sm font-semibold">{currentDecision.technicals.volatility}%</p>
                    </div>
                    <div className="text-center p-2 bg-background/50 rounded">
                      <p className="text-xs text-muted-foreground">Volume Strength</p>
                      <p className="text-sm font-semibold">{currentDecision.technicals.volumeStrength}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}
      </div>

      {/* Trade Logs */}
      {tradeLogs.length > 0 && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-lg font-bold mb-4">Recent Activity</h3>
          
          <div className="space-y-3">
            {tradeLogs.map((log, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 bg-background/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {getActionIcon(log.decision.action)}
                  <div>
                    <p className="font-semibold">
                      {log.decision.action.toUpperCase()} {log.decision.symbol}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <Badge variant={log.executed ? 'default' : 'secondary'}>
                    {log.executed ? 'Executed' : 'Analyzed'}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-1">
                    {log.decision.confidence} confidence
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Market Overview */}
      {marketData.length > 0 && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-lg font-bold mb-4">Market Snapshot</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {marketData.map((data) => (
              <div key={data.symbol} className="p-4 bg-background/50 rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">{data.symbol}</p>
                <p className="text-lg font-bold">${data.price.toLocaleString()}</p>
                <p className={`text-sm ${data.change >= 0 ? 'text-success' : 'text-danger'}`}>
                  {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default AITrader;
