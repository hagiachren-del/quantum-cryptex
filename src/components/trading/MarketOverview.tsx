import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";

const MarketOverview = () => {
  const { data: marketData, isLoading } = useQuery({
    queryKey: ['market-data'],
    queryFn: async () => {
      const { data, error } = await supabase.functions.invoke('mexc-market-data');
      if (error) throw error;
      return data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const cryptos = marketData?.symbols || [
    { symbol: "BTC/USDT", price: "43,250.00", change: "+2.45", changePercent: "+2.45%" },
    { symbol: "ETH/USDT", price: "2,280.50", change: "+1.82", changePercent: "+1.82%" },
    { symbol: "BNB/USDT", price: "305.20", change: "-0.85", changePercent: "-0.85%" },
    { symbol: "SOL/USDT", price: "98.75", change: "+5.20", changePercent: "+5.20%" },
    { symbol: "XRP/USDT", price: "0.5840", change: "+3.15", changePercent: "+3.15%" },
    { symbol: "ADA/USDT", price: "0.4520", change: "-1.25", changePercent: "-1.25%" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Market Overview</h2>
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Activity className="h-4 w-4 animate-spin" />
            <span className="text-sm">Loading...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cryptos.map((crypto) => {
          const isPositive = !crypto.changePercent.startsWith("-");
          return (
            <Card 
              key={crypto.symbol}
              className="p-6 bg-card/50 backdrop-blur-sm border-border hover:border-primary/50 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold group-hover:text-primary transition-colors">
                    {crypto.symbol}
                  </h3>
                  <p className="text-2xl font-bold mt-1">${crypto.price}</p>
                </div>
                {isPositive ? (
                  <TrendingUp className="h-5 w-5 text-success" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-danger" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge 
                  variant={isPositive ? "default" : "destructive"}
                  className={isPositive ? "bg-success/20 text-success hover:bg-success/30" : "bg-danger/20 text-danger hover:bg-danger/30"}
                >
                  {crypto.changePercent}
                </Badge>
                <span className={`text-sm ${isPositive ? "text-success" : "text-danger"}`}>
                  {isPositive ? "+" : ""}{crypto.change}
                </span>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default MarketOverview;
