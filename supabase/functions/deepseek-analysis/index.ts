import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const DEEPSEEK_API_KEY = Deno.env.get('DEEPSEEK_API_KEY');
    
    if (!DEEPSEEK_API_KEY) {
      throw new Error('DEEPSEEK_API_KEY not configured');
    }

    const { query } = await req.json();

    console.log('Generating AI analysis for query:', query);

    // Call DeepSeek API for market analysis
    const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          {
            role: 'system',
            content: 'You are an expert crypto market analyst. Provide concise, actionable market insights and trading recommendations based on technical and fundamental analysis. Format your response with clear sections for sentiment, recommendation, and detailed analysis.',
          },
          {
            role: 'user',
            content: query,
          },
        ],
        temperature: 0.7,
        max_tokens: 1000,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || 'DeepSeek API error');
    }

    const data = await response.json();
    const analysisText = data.choices[0].message.content;

    // Parse the analysis into structured format
    const analysis = {
      analysis: analysisText,
      confidence: 'High',
      sentiment: extractSentiment(analysisText),
      recommendation: extractRecommendation(analysisText),
      timestamp: new Date().toISOString(),
    };

    console.log('Analysis generated successfully');

    return new Response(
      JSON.stringify(analysis),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('Error in deepseek-analysis:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        analysis: 'Unable to generate analysis at this time. Please try again later.',
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    );
  }
});

function extractSentiment(text: string): string {
  const lowerText = text.toLowerCase();
  if (lowerText.includes('bullish') || lowerText.includes('positive') || lowerText.includes('uptrend')) {
    return 'Bullish - Market shows positive momentum';
  } else if (lowerText.includes('bearish') || lowerText.includes('negative') || lowerText.includes('downtrend')) {
    return 'Bearish - Market shows negative momentum';
  } else {
    return 'Neutral - Market consolidating';
  }
}

function extractRecommendation(text: string): string {
  const lowerText = text.toLowerCase();
  if (lowerText.includes('buy') || lowerText.includes('accumulate')) {
    return 'Consider buying opportunities with proper risk management';
  } else if (lowerText.includes('sell') || lowerText.includes('exit')) {
    return 'Consider taking profits or reducing exposure';
  } else {
    return 'Hold current positions and monitor market conditions';
  }
}
