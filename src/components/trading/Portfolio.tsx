import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wallet, TrendingUp, TrendingDown, Activity, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface Balance {
  asset: string;
  free: number;
  locked: number;
  total: number;
}

interface AccountData {
  balances: Balance[];
  openOrders: any[];
  updateTime: number;
}

const Portfolio = () => {
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  const fetchAccountData = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('mexc-account');
      
      if (error) throw error;
      
      setAccountData(data);
      toast({
        title: "Portfolio Updated",
        description: "Your MEXC account data has been refreshed",
      });
    } catch (error) {
      console.error('Error fetching account data:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to fetch account data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAccountData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchAccountData, 30000);
    return () => clearInterval(interval);
  }, []);

  const holdings = accountData?.balances || [];
  const totalAssets = holdings.length;
  const totalOpenOrders = accountData?.openOrders.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Wallet className="h-8 w-8 text-primary" />
          <div>
            <h2 className="text-3xl font-bold">Portfolio</h2>
            <p className="text-muted-foreground">Your MEXC account holdings</p>
          </div>
        </div>
        <Button 
          onClick={fetchAccountData} 
          disabled={isLoading}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 bg-gradient-to-br from-primary/20 to-accent/20 backdrop-blur-sm border-primary/50">
          <p className="text-sm text-muted-foreground mb-2">Total Assets</p>
          <p className="text-3xl font-bold mb-2">{totalAssets}</p>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Activity className="h-4 w-4" />
            <span className="text-sm">Active holdings</span>
          </div>
        </Card>

        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <p className="text-sm text-muted-foreground mb-2">Open Orders</p>
          <p className="text-3xl font-bold mb-2">{totalOpenOrders}</p>
          <Badge variant="outline">
            Active positions
          </Badge>
        </Card>

        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <p className="text-sm text-muted-foreground mb-2">Account Status</p>
          <p className="text-3xl font-bold mb-2">
            {isLoading ? "..." : accountData ? "Active" : "Offline"}
          </p>
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${accountData ? 'bg-success animate-pulse' : 'bg-muted'}`} />
            <span className="text-sm text-muted-foreground">
              {accountData ? 'Connected to MEXC' : 'Disconnected'}
            </span>
          </div>
        </Card>
      </div>

      <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
        <h3 className="text-xl font-bold mb-6">Holdings</h3>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : holdings.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No assets found in your MEXC account</p>
          </div>
        ) : (
          <div className="space-y-4">
            {holdings.map((holding) => (
              <div 
                key={holding.asset}
                className="flex items-center justify-between p-4 rounded-lg bg-background/50 border border-border hover:border-primary/50 transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <span className="font-bold text-primary">{holding.asset.substring(0, 2)}</span>
                  </div>
                  <div>
                    <p className="font-bold">{holding.asset}</p>
                    <p className="text-sm text-muted-foreground">
                      {holding.total.toFixed(8)} {holding.asset}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">Available:</span>
                      <span className="font-semibold">{holding.free.toFixed(8)}</span>
                    </div>
                    {holding.locked > 0 && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">Locked:</span>
                        <span className="font-semibold text-warning">{holding.locked.toFixed(8)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {accountData && accountData.openOrders.length > 0 && (
        <Card className="p-6 bg-card/50 backdrop-blur-sm border-border">
          <h3 className="text-xl font-bold mb-6">Open Orders</h3>
          <div className="space-y-4">
            {accountData.openOrders.map((order) => (
              <div 
                key={order.orderId}
                className="flex items-center justify-between p-4 rounded-lg bg-background/50 border border-border"
              >
                <div>
                  <p className="font-bold">{order.symbol}</p>
                  <p className="text-sm text-muted-foreground">
                    {order.side} • {order.type}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{order.price}</p>
                  <p className="text-sm text-muted-foreground">
                    {order.executedQty}/{order.origQty}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default Portfolio;
