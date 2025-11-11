import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createHmac } from "https://deno.land/std@0.168.0/node/crypto.ts";

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
    const MEXC_SECRET_KEY = Deno.env.get('MEXC_SECRET_KEY');
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    
    if (!MEXC_API_KEY || !MEXC_SECRET_KEY || !LOVABLE_API_KEY) {
      throw new Error('Required API credentials not configured');
    }

    const { action } = await req.json();

    if (action === 'analyze') {
      // Fetch market data
      const tickerResponse = await fetch('https://api.mexc.com/api/v3/ticker/24hr', {
        headers: { 'X-MEXC-APIKEY': MEXC_API_KEY }
      });
      const tickers = await tickerResponse.json();

      // Focus on major pairs
      const majorPairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'];
      const marketData = tickers.filter((t: any) => majorPairs.includes(t.symbol));

      // Get account balance
      const timestamp = Date.now();
      const balanceParams = `timestamp=${timestamp}`;
      const balanceSignature = createHmac('sha256', MEXC_SECRET_KEY)
        .update(balanceParams)
        .digest('hex');

      const balanceResponse = await fetch(
        `https://api.mexc.com/api/v3/account?${balanceParams}&signature=${balanceSignature}`,
        { headers: { 'X-MEXC-APIKEY': MEXC_API_KEY } }
      );
      const accountData = await balanceResponse.json();
      const usdtBalance = accountData.balances?.find((b: any) => b.asset === 'USDT');
      const availableUSDT = parseFloat(usdtBalance?.free || '0');

      // Prepare market summary for AI
      const marketSummary = marketData.map((t: any) => ({
        symbol: t.symbol,
        price: parseFloat(t.lastPrice),
        change: parseFloat(t.priceChangePercent),
        volume: parseFloat(t.volume),
        high: parseFloat(t.highPrice),
        low: parseFloat(t.lowPrice),
      }));

      // Use Lovable AI to analyze and make trading decisions
      const aiResponse = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${LOVABLE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'google/gemini-2.5-flash',
          messages: [
            {
              role: 'system',
              content: `You are an expert crypto trading AI. Analyze market data and provide trading recommendations.
              
Rules:
- Only recommend trades if confidence is HIGH
- Consider price trends, volume, and momentum
- Maximum trade size: 10% of available balance
- Only trade if 24h change shows clear trend (> 3% or < -3%)
- Prefer buying on dips and selling on peaks
- Account for risk management

Respond with JSON only:
{
  "action": "buy" | "sell" | "hold",
  "symbol": "BTCUSDT" | "ETHUSDT" | "BNBUSDT" | "SOLUSDT",
  "confidence": "high" | "medium" | "low",
  "amount": number (in USDT for buy, in crypto for sell),
  "reasoning": "brief explanation",
  "sentiment": "bullish" | "bearish" | "neutral"
}`
            },
            {
              role: 'user',
              content: `Available USDT balance: ${availableUSDT}
              
Market Data:
${JSON.stringify(marketSummary, null, 2)}

Current Holdings:
${accountData.balances?.filter((b: any) => parseFloat(b.free) > 0 && b.asset !== 'USDT')
  .map((b: any) => `${b.asset}: ${b.free}`).join('\n') || 'None'}

Analyze the market and provide a trading recommendation.`
            }
          ],
        }),
      });

      if (!aiResponse.ok) {
        const errorText = await aiResponse.text();
        console.error('Lovable AI error:', aiResponse.status, errorText);
        throw new Error('AI analysis failed');
      }

      const aiData = await aiResponse.json();
      const aiDecision = aiData.choices[0].message.content;
      
      // Parse AI response
      let decision;
      try {
        // Extract JSON from markdown code blocks if present
        const jsonMatch = aiDecision.match(/```json\n([\s\S]*?)\n```/) || 
                         aiDecision.match(/```\n([\s\S]*?)\n```/);
        const jsonStr = jsonMatch ? jsonMatch[1] : aiDecision;
        decision = JSON.parse(jsonStr);
      } catch (e) {
        console.error('Failed to parse AI response:', aiDecision);
        throw new Error('Invalid AI response format');
      }

      console.log('AI Decision:', decision);

      return new Response(
        JSON.stringify({
          decision,
          marketData: marketSummary,
          availableBalance: availableUSDT,
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        }
      );

    } else if (action === 'execute') {
      const { decision } = await req.json();

      if (decision.action === 'hold') {
        return new Response(
          JSON.stringify({ 
            success: true,
            message: 'AI decided to hold position',
            decision 
          }),
          { 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
          }
        );
      }

      // Execute the trade
      const timestamp = Date.now();
      const symbol = decision.symbol;
      const side = decision.action.toUpperCase();
      
      const params: any = {
        symbol,
        side,
        type: 'MARKET',
        timestamp,
      };

      if (side === 'BUY') {
        params.quoteOrderQty = decision.amount; // Amount in USDT
      } else {
        params.quantity = decision.amount; // Amount in crypto
      }

      const queryString = Object.keys(params)
        .sort()
        .map(key => `${key}=${params[key]}`)
        .join('&');

      const signature = createHmac('sha256', MEXC_SECRET_KEY)
        .update(queryString)
        .digest('hex');

      const tradeResponse = await fetch(
        `https://api.mexc.com/api/v3/order?${queryString}&signature=${signature}`,
        {
          method: 'POST',
          headers: {
            'X-MEXC-APIKEY': MEXC_API_KEY,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!tradeResponse.ok) {
        const errorData = await tradeResponse.json();
        throw new Error(errorData.msg || 'Trade execution failed');
      }

      const orderData = await tradeResponse.json();
      console.log('Trade executed:', orderData);

      return new Response(
        JSON.stringify({ 
          success: true,
          orderId: orderData.orderId,
          decision,
          message: `AI executed ${decision.action} order for ${decision.symbol}`,
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        }
      );
    }

    throw new Error('Invalid action');

  } catch (error) {
    console.error('Error in ai-trader:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        success: false,
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    );
  }
});
