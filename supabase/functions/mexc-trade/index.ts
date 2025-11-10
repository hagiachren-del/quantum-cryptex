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
    
    if (!MEXC_API_KEY || !MEXC_SECRET_KEY) {
      throw new Error('MEXC API credentials not configured');
    }

    const { symbol, amount, price, orderType, side } = await req.json();

    console.log(`Processing ${side} order for ${amount} ${symbol}`);

    // Prepare order parameters
    const timestamp = Date.now();
    const params: any = {
      symbol: symbol.replace('/', ''),
      side: side.toUpperCase(),
      type: orderType.toUpperCase(),
      quantity: amount,
      timestamp,
    };

    if (orderType === 'limit' && price) {
      params.price = price;
      params.timeInForce = 'GTC';
    }

    // Create query string and signature
    const queryString = Object.keys(params)
      .sort()
      .map(key => `${key}=${params[key]}`)
      .join('&');

    const signature = createHmac('sha256', MEXC_SECRET_KEY)
      .update(queryString)
      .digest('hex');

    // Place order on MEXC
    const response = await fetch(`https://api.mexc.com/api/v3/order?${queryString}&signature=${signature}`, {
      method: 'POST',
      headers: {
        'X-MEXC-APIKEY': MEXC_API_KEY,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.msg || 'Failed to place order');
    }

    const orderData = await response.json();
    console.log('Order placed successfully:', orderData.orderId);

    return new Response(
      JSON.stringify({ 
        success: true,
        orderId: orderData.orderId,
        message: `${side.toUpperCase()} order placed successfully`,
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('Error in mexc-trade:', error);
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
