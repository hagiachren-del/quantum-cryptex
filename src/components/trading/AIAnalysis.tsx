import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Brain, Sparkles, TrendingUp, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";

const AIAnalysis = () => {
  const [query, setQuery] = useState("");
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

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
      const { data, error } = await supabase.functions.invoke('deepseek-analysis', {
        body: { query },
      });

      if (error) throw error;

      setAnalysis(data);
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
          <div>
            <label className="text-sm font-medium mb-2 block">Ask AI About Markets</label>
            <Textarea
              placeholder="e.g., What's the sentiment for Bitcoin? Should I buy ETH now? Analyze SOL market trends..."
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
            <div className="h-10 w-10 rounded-lg bg-success/20 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-success" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Market Trend</p>
              <p className="text-lg font-bold text-success">Bullish</p>
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
              <p className="text-lg font-bold">8.5/10</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card/50 backdrop-blur-sm border-border">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-10 w-10 rounded-lg bg-warning/20 flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-warning" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <p className="text-lg font-bold text-warning">Medium</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AIAnalysis;
