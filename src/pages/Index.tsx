import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MarketOverview from "@/components/trading/MarketOverview";
import AIAnalysis from "@/components/trading/AIAnalysis";
import TradingPanel from "@/components/trading/TradingPanel";
import Portfolio from "@/components/trading/Portfolio";
import AITrader from "@/components/trading/AITrader";
import { Activity, Brain, TrendingUp, Wallet, Bot } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Activity className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Quantum Cryptex
              </h1>
              <p className="text-xs text-muted-foreground">AI-Powered Trading Terminal</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid bg-card/50 backdrop-blur-sm">
            <TabsTrigger value="overview" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              <span className="hidden sm:inline">Market</span>
            </TabsTrigger>
            <TabsTrigger value="ai" className="gap-2">
              <Brain className="h-4 w-4" />
              <span className="hidden sm:inline">AI Analysis</span>
            </TabsTrigger>
            <TabsTrigger value="ai-trader" className="gap-2">
              <Bot className="h-4 w-4" />
              <span className="hidden sm:inline">AI Trader</span>
            </TabsTrigger>
            <TabsTrigger value="trade" className="gap-2">
              <Activity className="h-4 w-4" />
              <span className="hidden sm:inline">Trade</span>
            </TabsTrigger>
            <TabsTrigger value="portfolio" className="gap-2">
              <Wallet className="h-4 w-4" />
              <span className="hidden sm:inline">Portfolio</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <MarketOverview />
          </TabsContent>

          <TabsContent value="ai" className="space-y-6">
            <AIAnalysis />
          </TabsContent>

          <TabsContent value="ai-trader" className="space-y-6">
            <AITrader />
          </TabsContent>

          <TabsContent value="trade" className="space-y-6">
            <TradingPanel />
          </TabsContent>

          <TabsContent value="portfolio" className="space-y-6">
            <Portfolio />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
