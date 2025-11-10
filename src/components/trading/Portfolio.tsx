import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wallet, TrendingUp, TrendingDown, Activity } from "lucide-react";

const Portfolio = () => {
  const holdings = [
    { symbol: "BTC", amount: "0.5432", value: "$23,478.50", change: "+5.2%", changeValue: "+$1,234.50", positive: true },
    { symbol: "ETH", amount: "8.25", value: "$18,814.12", change: "+3.1%", changeValue: "+$567.23", positive: true },
    { symbol: "BNB", amount: "45.60", value: "$13,917.12", change: "-1.2%", changeValue: "-$168.45", positive: false },
    { symbol: "SOL", amount: "120.00", value: "$11,850.00", change: "+8.5%", changeValue: "+$928.75", positive: true },
  ];

  const totalValue = holdings.reduce((acc, h) => acc + parseFloat(h.value.replace(/[$,]/g, "")), 0);
  const totalChange = holdings.reduce((acc, h) => acc + parseFloat(h.changeValue.replace(/[$,+]/g, "")), 0);
  const changePercent = ((totalChange / totalValue) * 100).toFixed(2);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Wallet className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-3xl font-bold">Portfolio</h2>
          <p className="text-muted-foreground">Track your crypto holdings</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 bg-gradient-to-br from-primary/20 to-accent/20 backdrop-blur-sm border-primary/50">
          <p className="text-sm text-muted-foreground mb-2">Total Portfolio Value</p>
          <p className="text-3xl font-bold mb-2">${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
          <div className="flex items-center gap-2">
            {totalChange >= 0 ? (
              <TrendingUp className="h-4 w-4 text-success" />
            ) : (
              <TrendingDown className="h-4 w-4 text-danger" />
            )}
            <span className={`text-sm font-semibold ${totalChange >= 0 ? "text-success" : "text-danger"}`}>
              {totalChange >= 0 ? "+" : ""}{changePercent}%
            </span>
            <span className={`text-sm ${totalChange >= 0 ? "text-success" : "text-danger"}`}>
              {totalChange >= 0 ? "+" : ""}${Math.abs(totalChange).toFixed(2)}
            </span>
          </div>
        </Card>

        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <p className="text-sm text-muted-foreground mb-2">24h Change</p>
          <p className={`text-3xl font-bold mb-2 ${totalChange >= 0 ? "text-success" : "text-danger"}`}>
            {totalChange >= 0 ? "+" : ""}${Math.abs(totalChange).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <Badge 
            variant={totalChange >= 0 ? "default" : "destructive"}
            className={totalChange >= 0 ? "bg-success/20 text-success" : "bg-danger/20 text-danger"}
          >
            {totalChange >= 0 ? "+" : ""}{changePercent}%
          </Badge>
        </Card>

        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <p className="text-sm text-muted-foreground mb-2">Total Assets</p>
          <p className="text-3xl font-bold mb-2">{holdings.length}</p>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Activity className="h-4 w-4" />
            <span className="text-sm">Active holdings</span>
          </div>
        </Card>
      </div>

      <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
        <h3 className="text-xl font-bold mb-6">Holdings</h3>
        <div className="space-y-4">
          {holdings.map((holding) => (
            <div 
              key={holding.symbol}
              className="flex items-center justify-between p-4 rounded-lg bg-background/50 border border-border hover:border-primary/50 transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                  <span className="font-bold text-primary">{holding.symbol.substring(0, 2)}</span>
                </div>
                <div>
                  <p className="font-bold">{holding.symbol}</p>
                  <p className="text-sm text-muted-foreground">{holding.amount} {holding.symbol}</p>
                </div>
              </div>

              <div className="text-right">
                <p className="font-bold text-lg">{holding.value}</p>
                <div className="flex items-center gap-2 justify-end">
                  {holding.positive ? (
                    <TrendingUp className="h-4 w-4 text-success" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-danger" />
                  )}
                  <span className={`text-sm font-semibold ${holding.positive ? "text-success" : "text-danger"}`}>
                    {holding.change}
                  </span>
                  <span className={`text-sm ${holding.positive ? "text-success" : "text-danger"}`}>
                    {holding.changeValue}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default Portfolio;
