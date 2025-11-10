import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const MEXC_API_KEY = Deno.env.get('MEXC_API_KEY');
    
    if (!MEXC_API_KEY) {
      throw new Error('MEXC_API_KEY not configured');
    }

    console.log('Fetching market data from MEXC...');

    // Fetch ticker data from MEXC API
    const response = await fetch('https://api.mexc.com/api/v3/ticker/24hr', {
      headers: {
        'X-MEXC-APIKEY': MEXC_API_KEY,
      },
    });

    if (!response.ok) {
      throw new Error(`MEXC API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Filter for major pairs and format the data
    const majorPairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT'];
    const symbols = data
      .filter((item: any) => majorPairs.includes(item.symbol))
      .map((item: any) => ({
        symbol: `${item.symbol.replace('USDT', '')}/USDT`,
        price: parseFloat(item.lastPrice).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
        change: parseFloat(item.priceChange).toFixed(2),
        changePercent: `${parseFloat(item.priceChangePercent).toFixed(2)}%`,
        volume: item.volume,
        high: item.highPrice,
        low: item.lowPrice,
      }));

    console.log(`Successfully fetched ${symbols.length} symbols`);

    return new Response(
      JSON.stringify({ symbols }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('Error in mexc-market-data:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        // Fallback data in case of API failure
        symbols: [
          { symbol: "BTC/USDT", price: "43,250.00", change: "+2.45", changePercent: "+2.45%" },
          { symbol: "ETH/USDT", price: "2,280.50", change: "+1.82", changePercent: "+1.82%" },
          { symbol: "BNB/USDT", price: "305.20", change: "-0.85", changePercent: "-0.85%" },
          { symbol: "SOL/USDT", price: "98.75", change: "+5.20", changePercent: "+5.20%" },
        ]
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );
  }
});
