import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createHmac } from "https://deno.land/std@0.177.0/node/crypto.ts";

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

    const timestamp = Date.now();
    const queryString = `timestamp=${timestamp}`;
    const signature = createHmac('sha256', MEXC_SECRET_KEY)
      .update(queryString)
      .digest('hex');

    console.log('Fetching MEXC account information');

    // Fetch account balance
    const balanceResponse = await fetch(
      `https://api.mexc.com/api/v3/account?${queryString}&signature=${signature}`,
      {
        headers: {
          'X-MEXC-APIKEY': MEXC_API_KEY,
        },
      }
    );

    if (!balanceResponse.ok) {
      const errorText = await balanceResponse.text();
      console.error('MEXC account API error:', errorText);
      throw new Error(`MEXC API error: ${balanceResponse.status}`);
    }

    const accountData = await balanceResponse.json();

    // Filter balances to only show assets with non-zero balance
    const balances = accountData.balances
      .filter((b: any) => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0)
      .map((b: any) => ({
        asset: b.asset,
        free: parseFloat(b.free),
        locked: parseFloat(b.locked),
        total: parseFloat(b.free) + parseFloat(b.locked),
      }));

    // Fetch open orders
    const ordersQueryString = `timestamp=${Date.now()}`;
    const ordersSignature = createHmac('sha256', MEXC_SECRET_KEY)
      .update(ordersQueryString)
      .digest('hex');

    const ordersResponse = await fetch(
      `https://api.mexc.com/api/v3/openOrders?${ordersQueryString}&signature=${ordersSignature}`,
      {
        headers: {
          'X-MEXC-APIKEY': MEXC_API_KEY,
        },
      }
    );

    let openOrders = [];
    if (ordersResponse.ok) {
      openOrders = await ordersResponse.json();
    }

    console.log(`Account info fetched: ${balances.length} assets, ${openOrders.length} open orders`);

    return new Response(
      JSON.stringify({
        balances,
        openOrders: openOrders.map((order: any) => ({
          orderId: order.orderId,
          symbol: order.symbol,
          side: order.side,
          type: order.type,
          price: order.price,
          origQty: order.origQty,
          executedQty: order.executedQty,
          status: order.status,
          time: order.time,
        })),
        updateTime: accountData.updateTime,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('Error in mexc-account function:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    );
  }
});
