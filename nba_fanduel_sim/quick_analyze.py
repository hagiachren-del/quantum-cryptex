#!/usr/bin/env python3
"""
Quick NBA Betting Analysis Script
Uses all 4 improvements: secure API, enhanced Elo, reality checks, variance analysis
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.append(str(Path(__file__).parent))

from config.secure_config import SecureConfig
from models.enhanced_elo_model import EnhancedEloModel, STAR_PLAYER_INJURY, STARTER_INJURY
from evaluation.market_efficiency import MarketEfficiencyAnalyzer
from evaluation.variance_analyzer import VarianceAnalyzer
from odds.fanduel_odds_utils import american_to_probability, format_american_odds


# Current season Elo ratings (simplified - you can update these)
ELO_RATINGS = {
    'Cleveland Cavaliers': 1650, 'Boston Celtics': 1640, 'Oklahoma City Thunder': 1635,
    'Houston Rockets': 1610, 'Memphis Grizzlies': 1590, 'New York Knicks': 1580,
    'Denver Nuggets': 1575, 'Milwaukee Bucks': 1570, 'Los Angeles Lakers': 1565,
    'Golden State Warriors': 1560, 'Orlando Magic': 1555, 'Dallas Mavericks': 1550,
    'Los Angeles Clippers': 1530, 'Miami Heat': 1525, 'Minnesota Timberwolves': 1520,
    'Sacramento Kings': 1515, 'Indiana Pacers': 1510, 'Phoenix Suns': 1505,
    'Atlanta Hawks': 1500, 'San Antonio Spurs': 1480, 'Chicago Bulls': 1475,
    'Philadelphia 76ers': 1470, 'Detroit Pistons': 1465, 'Brooklyn Nets': 1460,
    'Portland Trail Blazers': 1450, 'Toronto Raptors': 1440, 'Charlotte Hornets': 1430,
    'Utah Jazz': 1425, 'New Orleans Pelicans': 1420, 'Washington Wizards': 1400,
}


def fetch_live_odds(api_key: str):
    """Fetch live NBA odds from The Odds API."""
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
    params = {
        'apiKey': api_key,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'bookmakers': 'fanduel',
        'oddsFormat': 'american'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ API Error: {response.status_code}")
        return None


def analyze_game(game, model, efficiency_analyzer):
    """Analyze a single game with all improvements."""
    home_team = game['home_team']
    away_team = game['away_team']

    # Get odds
    bookmaker = game['bookmakers'][0]
    markets = {m['key']: m for m in bookmaker['markets']}

    h2h = markets['h2h']['outcomes']
    ml_home = next(o['price'] for o in h2h if o['name'] == home_team)
    ml_away = next(o['price'] for o in h2h if o['name'] == away_team)

    spreads = markets['spreads']['outcomes']
    spread_home = next(o for o in spreads if o['name'] == home_team)

    # Get model prediction with enhanced Elo
    home_elo = ELO_RATINGS.get(home_team, 1500)
    away_elo = ELO_RATINGS.get(away_team, 1500)

    model.set_rating(home_team, home_elo)
    model.set_rating(away_team, away_elo)

    # TODO: Add actual injury data here
    # injuries = [STAR_PLAYER_INJURY("Player Name", "POS")]

    home_prob = model.predict_win_probability(
        home_team=home_team,
        away_team=away_team,
        home_rest_days=2,  # TODO: Get real rest days
        away_rest_days=2
    )

    # Calculate market probability
    ml_home_implied = american_to_probability(ml_home)

    # Reality check moneyline
    edge = home_prob - ml_home_implied

    if abs(edge) > 0.02:  # 2% edge threshold
        ev = (home_prob * (100/abs(ml_home) if ml_home < 0 else ml_home/100)) - ((1-home_prob) * 1)

        # Reality check
        check = efficiency_analyzer.reality_check_ev_opportunity(
            model_prob=home_prob,
            market_prob=ml_home_implied,
            odds=ml_home,
            ev_percentage=ev
        )

        return {
            'game': f"{away_team} @ {home_team}",
            'time': game['commence_time'],
            'home_ml': ml_home,
            'away_ml': ml_away,
            'spread': spread_home['point'],
            'model_prob': home_prob,
            'market_prob': ml_home_implied,
            'edge': edge,
            'ev': ev,
            'reality_check': check
        }

    return None


def main():
    """Main analysis workflow."""
    print("=" * 80)
    print("NBA BETTING SIMULATOR - LIVE ANALYSIS")
    print("=" * 80)
    print()

    # Step 1: Get API key securely
    print("📡 Step 1: Loading API key...")
    config = SecureConfig()

    if not config.validate_api_key():
        print("\n❌ Please run setup first:")
        print("   python3 nba_fanduel_sim/config/secure_config.py setup")
        return

    api_key = config.get_api_key('the_odds_api')
    print()

    # Step 2: Fetch live odds
    print("📊 Step 2: Fetching live NBA odds from FanDuel...")
    games = fetch_live_odds(api_key)

    if not games:
        print("❌ No games found or API error")
        return

    print(f"✅ Found {len(games)} NBA games\n")

    # Step 3: Initialize enhanced model
    print("🧮 Step 3: Initializing enhanced Elo model...")
    model = EnhancedEloModel()
    efficiency_analyzer = MarketEfficiencyAnalyzer()
    variance_analyzer = VarianceAnalyzer()
    print()

    # Step 4: Analyze each game
    print("🔍 Step 4: Analyzing games with reality checks...")
    print("=" * 80)
    print()

    opportunities = []

    for game in games:
        result = analyze_game(game, model, efficiency_analyzer)
        if result:
            opportunities.append(result)

    # Step 5: Display results
    if not opportunities:
        print("⚠️  No positive EV opportunities found")
        print("    (This is normal - NBA markets are very efficient)")
        print()
    else:
        print(f"🎯 FOUND {len(opportunities)} POTENTIAL OPPORTUNITIES")
        print("=" * 80)
        print()

        for i, opp in enumerate(opportunities, 1):
            check = opp['reality_check']

            print(f"#{i}. {opp['game']}")
            print(f"    ML: {format_american_odds(opp['home_ml'])} / {format_american_odds(opp['away_ml'])}")
            print(f"    Spread: {opp['spread']:+.1f}")
            print(f"    Model Prob: {opp['model_prob']*100:.1f}%")
            print(f"    Market Prob: {opp['market_prob']*100:.1f}%")
            print(f"    Edge: {opp['edge']*100:+.1f}%")
            print(f"    Raw EV: {opp['ev']*100:+.1f}%")
            print()
            print(f"    Reality Check: {check['recommendation']}")
            print(f"    Adjusted EV: {check['adjusted_ev']*100:+.1f}%")

            if check['warnings']:
                print(f"    ⚠️  Warnings:")
                for w in check['warnings']:
                    print(f"        [{w['level']}] {w['message']}")

            print()
            print("-" * 80)
            print()

        # Step 6: Variance analysis for top opportunities
        good_opps = [o for o in opportunities if o['reality_check']['recommendation'] == 'PROCEED']

        if good_opps:
            print()
            print("📉 VARIANCE ANALYSIS FOR RECOMMENDED BETS")
            print("=" * 80)
            print()

            bets = []
            for opp in good_opps[:5]:  # Top 5
                bets.append({
                    'model_prob': opp['model_prob'],
                    'odds': opp['home_ml'],
                    'stake': 100  # $100 per bet
                })

            sim = variance_analyzer.simulate_betting_outcomes(bets, 10000)

            print(f"Portfolio: {len(bets)} bets at $100 each = ${len(bets)*100} total risk")
            print()
            print(f"Expected Profit:     ${sim['mean_profit']:,.0f}")
            print(f"Probability Profit:  {sim['prob_profit']*100:.1f}%")
            print(f"Probability Loss:    {sim['prob_loss']*100:.1f}%")
            print()
            print(f"Best 5%:   ${sim['percentile_95']:,.0f}+")
            print(f"Median:    ${sim['median_profit']:,.0f}")
            print(f"Worst 5%:  ${sim['percentile_5']:,.0f}")
            print()

    print()
    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("💡 Tips:")
    print("   • Add real injury data for better predictions")
    print("   • Update Elo ratings with recent results")
    print("   • Track actual bet outcomes")
    print("   • Generate efficiency reports weekly")
    print()


if __name__ == "__main__":
    main()
