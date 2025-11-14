import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Brain, Sparkles, TrendingUp, AlertCircle, History, TrendingDown, Activity } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const AIAnalysis = () => {
  const [query, setQuery] = useState("");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [timelineData, setTimelineData] = useState<any[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    const { data } = await supabase
      .from('ai_analysis_history')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);
    
    if (data) {
      setHistory(data);
      
      // Create timeline data for chart
      const timeline = data
        .filter(d => d.market_score)
        .reverse()
        .map(d => ({
          time: new Date(d.created_at).toLocaleTimeString(),
          score: d.market_score,
          sentiment: d.sentiment
        }));
      setTimelineData(timeline);
    }
  };

  const calculateDynamicMetrics = (analysisData: any) => {
    // Extract sentiment and calculate scores
    const sentimentKeywords = {
      bullish: ['bullish', 'positive', 'growth', 'upward', 'strong', 'buy'],
      bearish: ['bearish', 'negative', 'decline', 'downward', 'weak', 'sell'],
      neutral: ['neutral', 'stable', 'hold', 'uncertain']
    };

    const text = (analysisData.analysis + ' ' + analysisData.sentiment + ' ' + analysisData.recommendation).toLowerCase();
    
    let bullishScore = 0;
    let bearishScore = 0;
    
    sentimentKeywords.bullish.forEach(word => {
      if (text.includes(word)) bullishScore += 1;
    });
    
    sentimentKeywords.bearish.forEach(word => {
      if (text.includes(word)) bearishScore += 1;
    });

    const totalScore = bullishScore + bearishScore;
    const marketScore = totalScore > 0 ? (bullishScore / totalScore) * 10 : 5;
    
    const marketTrend = marketScore > 6 ? 'Bullish' : marketScore < 4 ? 'Bearish' : 'Neutral';
    const riskLevel = marketScore > 7 ? 'Low' : marketScore < 4 ? 'High' : 'Medium';
    
    return { marketScore: marketScore.toFixed(1), marketTrend, riskLevel };
  };

  const handleAnalyze = async () => {
    if (!query.trim()) {
      toast({
        title: "Query Required",
        description: "Please enter a market question or symbol to analyze",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const fullQuery = symbol ? `${query} for ${symbol}` : query;
      const { data, error } = await supabase.functions.invoke('deepseek-analysis', {
        body: { query: fullQuery },
      });

      if (error) throw error;

      // Calculate dynamic metrics
      const metrics = calculateDynamicMetrics(data);
      const enrichedData = { ...data, ...metrics };
      setAnalysis(enrichedData);

      // Store in history
      await supabase.from('ai_analysis_history').insert({
        query: fullQuery,
        symbol: symbol || null,
        sentiment: data.sentiment,
        recommendation: data.recommendation,
        confidence: data.confidence,
        analysis: data.analysis,
        market_score: parseFloat(metrics.marketScore),
        risk_level: metrics.riskLevel,
        market_trend: metrics.marketTrend
      });

      // Reload history
      await loadHistory();

      toast({
        title: "Analysis Complete",
        description: "AI has generated market insights",
      });
    } catch (error: any) {
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to generate analysis",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Brain className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-3xl font-bold">AI Market Analysis</h2>
          <p className="text-muted-foreground">Powered by DeepSeek & Advanced Analytics</p>
        </div>
      </div>

      <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium mb-2 block">Trading Symbol (Optional)</Label>
              <Input
                placeholder="e.g., BTCUSDT, ETHUSDT"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="bg-background/50"
              />
            </div>
          </div>
          <div>
            <Label className="text-sm font-medium mb-2 block">Ask AI About Markets</Label>
            <Textarea
              placeholder="e.g., What's the sentiment? Should I buy now? Analyze market trends..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="min-h-[120px] bg-background/50"
            />
          </div>
          <Button 
            onClick={handleAnalyze}
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90"
          >
            {isLoading ? (
              <>
                <Brain className="h-4 w-4 mr-2 animate-pulse" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate AI Analysis
              </>
            )}
          </Button>
        </div>
      </Card>

      {analysis && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              AI Insights
            </h3>
            <Badge className="bg-primary/20 text-primary">
              {analysis.confidence || "High Confidence"}
            </Badge>
          </div>

          <div className="space-y-4">
            {analysis.sentiment && (
              <div className="flex items-start gap-3">
                <TrendingUp className="h-5 w-5 text-success mt-1" />
                <div>
                  <p className="font-semibold">Market Sentiment</p>
                  <p className="text-muted-foreground">{analysis.sentiment}</p>
                </div>
              </div>
            )}

            {analysis.recommendation && (
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-primary mt-1" />
                <div>
                  <p className="font-semibold">Recommendation</p>
                  <p className="text-muted-foreground">{analysis.recommendation}</p>
                </div>
              </div>
            )}

            <div className="p-4 bg-background/50 rounded-lg border border-border">
              <p className="text-sm leading-relaxed">
                {analysis.analysis || analysis.message || "AI analysis will appear here"}
              </p>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3 mb-2">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
              analysis?.marketTrend === 'Bullish' ? 'bg-success/20' : 
              analysis?.marketTrend === 'Bearish' ? 'bg-danger/20' : 'bg-muted/20'
            }`}>
              {analysis?.marketTrend === 'Bullish' ? <TrendingUp className="h-5 w-5 text-success" /> :
               analysis?.marketTrend === 'Bearish' ? <TrendingDown className="h-5 w-5 text-danger" /> :
               <Activity className="h-5 w-5 text-muted-foreground" />}
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Market Trend</p>
              <p className={`text-lg font-bold ${
                analysis?.marketTrend === 'Bullish' ? 'text-success' :
                analysis?.marketTrend === 'Bearish' ? 'text-danger' : 'text-muted-foreground'
              }`}>
                {analysis?.marketTrend || 'Neutral'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">AI Score</p>
              <p className="text-lg font-bold">{analysis?.marketScore || '5.0'}/10</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3 mb-2">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
              analysis?.riskLevel === 'High' ? 'bg-danger/20' :
              analysis?.riskLevel === 'Medium' ? 'bg-warning/20' : 'bg-success/20'
            }`}>
              <AlertCircle className={`h-5 w-5 ${
                analysis?.riskLevel === 'High' ? 'text-danger' :
                analysis?.riskLevel === 'Medium' ? 'text-warning' : 'text-success'
              }`} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <p className={`text-lg font-bold ${
                analysis?.riskLevel === 'High' ? 'text-danger' :
                analysis?.riskLevel === 'Medium' ? 'text-warning' : 'text-success'
              }`}>
                {analysis?.riskLevel || 'Medium'}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Sentiment Timeline */}
      {timelineData.length > 0 && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Sentiment Timeline
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
              <YAxis domain={[0, 10]} stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))' 
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="score" 
                stroke="hsl(var(--primary))" 
                strokeWidth={2}
                dot={{ fill: 'hsl(var(--primary))' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Analysis History */}
      {history.length > 0 && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            Recent Analysis History
          </h3>
          <div className="space-y-3">
            {history.slice(0, 5).map((item) => (
              <div 
                key={item.id}
                className="p-3 bg-background/50 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => setAnalysis(item)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{item.query}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {item.symbol && (
                        <Badge variant="outline" className="text-xs">{item.symbol}</Badge>
                      )}
                      <span className={`text-xs ${
                        item.sentiment?.includes('bullish') ? 'text-success' :
                        item.sentiment?.includes('bearish') ? 'text-danger' : 'text-muted-foreground'
                      }`}>
                        {item.sentiment}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <Badge variant={item.confidence === 'High' ? 'default' : 'secondary'}>
                    {item.confidence}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default AIAnalysis;
