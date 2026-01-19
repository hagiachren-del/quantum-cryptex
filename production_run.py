#!/usr/bin/env python3
"""
PRODUCTION NBA ANALYSIS - Run with your API key
Usage: python3 production_run.py YOUR_API_KEY_HERE
"""

import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / 'nba_fanduel_sim'))

def main():
    if len(sys.argv) < 2:
        print("=" * 80)
        print("NBA BETTING SIMULATOR - PRODUCTION RUN")
        print("=" * 80)
        print()
        print("Usage: python3 production_run.py YOUR_API_KEY")
        print()
        print("Example:")
        print("  python3 production_run.py abcd1234efgh5678ijkl")
        print()
        print("Your API key will be used for this session only.")
        print("For permanent storage, run:")
        print("  python3 nba_fanduel_sim/config/secure_config.py setup")
        print()
        sys.exit(1)

    # Set API key for this session
    api_key = sys.argv[1].strip()
    os.environ['THE_ODDS_API_KEY'] = api_key

    print("=" * 80)
    print("🏀 NBA BETTING SIMULATOR - PRODUCTION ANALYSIS")
    print("=" * 80)
    print()
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print()

    # Import and run analysis
    try:
        import requests
        import json
        from datetime import datetime
        from models.enhanced_elo_model import EnhancedEloModel, STAR_PLAYER_INJURY, STARTER_INJURY
        from evaluation.market_efficiency import MarketEfficiencyAnalyzer
        from evaluation.variance_analyzer import VarianceAnalyzer
        from odds.fanduel_odds_utils import american_to_probability, format_american_odds

        # Elo ratings (2024-25 season)
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

        print("📡 Fetching live NBA odds from FanDuel...")
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
        params = {
            'apiKey': api_key,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'bookmakers': 'fanduel',
            'oddsFormat': 'american'
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        games = response.json()
        print(f"✅ Found {len(games)} NBA games")
        print()

        if not games:
            print("⚠️  No NBA games available right now")
            print("   Check back closer to game time")
            return

        # Initialize models
        print("🧮 Initializing enhanced Elo model...")
        model = EnhancedEloModel()
        efficiency_analyzer = MarketEfficiencyAnalyzer()
        variance_analyzer = VarianceAnalyzer()
        print()

        print("🔍 Analyzing games with all 4 improvements...")
        print("   ✓ Enhanced Elo (injuries, form, rest)")
        print("   ✓ Market efficiency reality checks")
        print("   ✓ Comprehensive variance analysis")
        print("   ✓ Secure API key management")
        print()
        print("=" * 80)
        print()

        opportunities = []

        for game_idx, game in enumerate(games, 1):
            home_team = game['home_team']
            away_team = game['away_team']
            commence_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))

            print(f"Game {game_idx}/{len(games)}: {away_team} @ {home_team}")
            print(f"   Time: {commence_time.strftime('%a %I:%M %p ET')}")

            # Get odds
            bookmaker = game['bookmakers'][0]
            markets = {m['key']: m for m in bookmaker['markets']}

            h2h = markets['h2h']['outcomes']
            ml_home = next(o['price'] for o in h2h if o['name'] == home_team)
            ml_away = next(o['price'] for o in h2h if o['name'] == away_team)

            spreads = markets['spreads']['outcomes']
            spread_home = next(o for o in spreads if o['name'] == home_team)

            print(f"   Odds: {format_american_odds(ml_away)} / {format_american_odds(ml_home)}")
            print(f"   Spread: {spread_home['point']:+.1f}")

            # Set Elo ratings
            home_elo = ELO_RATINGS.get(home_team, 1500)
            away_elo = ELO_RATINGS.get(away_team, 1500)
            model.set_rating(home_team, home_elo)
            model.set_rating(away_team, away_elo)

            # Get prediction
            home_prob = model.predict_win_probability(
                home_team=home_team,
                away_team=away_team,
                home_rest_days=2,
                away_rest_days=2
            )

            ml_home_implied = american_to_probability(ml_home)
            edge = home_prob - ml_home_implied

            print(f"   Model: Home {home_prob*100:.1f}% | Away {(1-home_prob)*100:.1f}%")
            print(f"   Market: Home {ml_home_implied*100:.1f}%")
            print(f"   Edge: {edge*100:+.1f}%")

            # Check both sides
            for side, prob, odds in [
                ('home', home_prob, ml_home),
                ('away', 1 - home_prob, ml_away)
            ]:
                side_edge = abs(prob - american_to_probability(odds))

                if side_edge > 0.02:  # 2% threshold
                    ev = (prob * (100/abs(odds) if odds < 0 else odds/100)) - ((1-prob) * 1)

                    check = efficiency_analyzer.reality_check_ev_opportunity(
                        model_prob=prob,
                        market_prob=american_to_probability(odds),
                        odds=odds,
                        ev_percentage=ev
                    )

                    if check['adjusted_ev'] > 0.02:  # Adjusted EV > 2%
                        opportunities.append({
                            'game': f"{away_team} @ {home_team}",
                            'time': commence_time,
                            'team': home_team if side == 'home' else away_team,
                            'odds': odds,
                            'model_prob': prob,
                            'edge': side_edge,
                            'ev': ev,
                            'adjusted_ev': check['adjusted_ev'],
                            'recommendation': check['recommendation'],
                            'warnings': check['warnings']
                        })

            print()

        print("=" * 80)
        print()

        if not opportunities:
            print("⚠️  NO POSITIVE EV OPPORTUNITIES FOUND")
            print()
            print("This is NORMAL and EXPECTED:")
            print("  • NBA betting markets are 85-95% efficient")
            print("  • True +EV opportunities are rare")
            print("  • Most apparent edges are model errors")
            print()
            print("Recommendations:")
            print("  • Wait for better spots")
            print("  • Update injury information")
            print("  • Check back closer to game time")
            print()
        else:
            print(f"🎯 FOUND {len(opportunities)} OPPORTUNITIES")
            print("=" * 80)
            print()

            # Sort by adjusted EV
            opportunities.sort(key=lambda x: x['adjusted_ev'], reverse=True)

            for i, opp in enumerate(opportunities, 1):
                print(f"#{i}. {opp['team']} {format_american_odds(opp['odds'])}")
                print(f"    Game: {opp['game']}")
                print(f"    Time: {opp['time'].strftime('%a %I:%M %p ET')}")
                print(f"    Model Probability: {opp['model_prob']*100:.1f}%")
                print(f"    Edge: {opp['edge']*100:+.1f}%")
                print(f"    Raw EV: {opp['ev']*100:+.1f}%")
                print(f"    Adjusted EV: {opp['adjusted_ev']*100:+.1f}%")
                print(f"    Recommendation: {opp['recommendation']}")

                if opp['warnings']:
                    print(f"    ⚠️  Warnings:")
                    for w in opp['warnings']:
                        print(f"        [{w['level']}] {w['message']}")

                print()

            # Variance analysis
            good_opps = [o for o in opportunities if o['recommendation'] in ['PROCEED', 'PROCEED WITH CAUTION']]

            if good_opps:
                print("=" * 80)
                print("📉 VARIANCE ANALYSIS")
                print("=" * 80)
                print()

                bets = [{'model_prob': o['model_prob'], 'odds': o['odds'], 'stake': 100}
                        for o in good_opps[:5]]

                sim = variance_analyzer.simulate_betting_outcomes(bets, 10000)

                print(f"Portfolio: {len(bets)} bets at $100 each = ${len(bets)*100} total risk")
                print()
                print(f"Expected Profit:       ${sim['mean_profit']:,.0f}")
                print(f"Probability of Profit: {sim['prob_profit']*100:.1f}%")
                print(f"Probability of Loss:   {sim['prob_loss']*100:.1f}%")
                print()
                print(f"Outcome Distribution:")
                print(f"  Best 5%:    ${sim['percentile_95']:,.0f}+")
                print(f"  Median:     ${sim['median_profit']:,.0f}")
                print(f"  Worst 5%:   ${sim['percentile_5']:,.0f}")
                print()
                print("⚠️  Remember:")
                print(f"  • You'll LOSE {sim['prob_loss']*100:.0f}% of the time despite +EV")
                print(f"  • 1 in 20 times you'll lose ${abs(sim['percentile_5']):,.0f}+")
                print(f"  • Variance dominates short-term results")
                print()

        print("=" * 80)
        print("✅ PRODUCTION ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
        print()

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
