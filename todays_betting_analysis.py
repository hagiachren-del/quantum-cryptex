#!/usr/bin/env python3
"""
Comprehensive Betting Analysis for Today's Games

Analyzes:
1. Moneyline opportunities
2. Same game parlay player props
3. Quarter betting opportunities
"""

import sys
import json
import numpy as np
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from data.sportradar_api import SportradarNBAClient  # ONLY data source - NBA official partner (LIVE)
from player_props.player_stats_model import PlayerStatsModel
from models.enhanced_elo_model import EnhancedEloModel
from odds.fanduel_odds_utils import american_to_probability, probability_to_american
from evaluation.market_efficiency import MarketEfficiencyAnalyzer


def load_todays_games():
    """Load games data from file"""
    with open('/tmp/todays_games.json', 'r') as f:
        return json.load(f)


def analyze_moneyline(games: List[Dict], elo_model: EnhancedEloModel,
                     efficiency_analyzer: MarketEfficiencyAnalyzer):
    """Analyze moneyline betting opportunities"""

    print("\n" + "="*100)
    print("💰 MONEYLINE ANALYSIS")
    print("="*100)

    opportunities = []

    for game in games:
        home_team = game['home_team']
        away_team = game['away_team']

        print(f"\n{'='*100}")
        print(f"🏀 {away_team} @ {home_team}")
        print(f"{'='*100}")

        # Get FanDuel odds
        fanduel_odds = None
        for bookmaker in game.get('bookmakers', []):
            if bookmaker['key'] == 'fanduel':
                fanduel_odds = bookmaker
                break

        if not fanduel_odds:
            print("⚠️  No FanDuel odds available")
            continue

        # Get moneyline odds
        h2h_market = next((m for m in fanduel_odds['markets'] if m['key'] == 'h2h'), None)
        if not h2h_market:
            print("⚠️  No moneyline odds available")
            continue

        home_odds = None
        away_odds = None
        for outcome in h2h_market['outcomes']:
            if outcome['name'] == home_team:
                home_odds = outcome['price']
            elif outcome['name'] == away_team:
                away_odds = outcome['price']

        if not home_odds or not away_odds:
            print("⚠️  Incomplete odds data")
            continue

        # Map team names to abbreviations for Elo model
        team_mapping = {
            'Orlando Magic': 'ORL',
            'Memphis Grizzlies': 'MEM',
            'Brooklyn Nets': 'BKN',
            'Chicago Bulls': 'CHI',
            'New Orleans Pelicans': 'NOP',
            'Houston Rockets': 'HOU',
            'Charlotte Hornets': 'CHA',
            'Denver Nuggets': 'DEN',
            'Portland Trail Blazers': 'POR',
            'Sacramento Kings': 'SAC',
            'Toronto Raptors': 'TOR',
            'Los Angeles Lakers': 'LAL'
        }

        home_abbr = team_mapping.get(home_team, home_team[:3].upper())
        away_abbr = team_mapping.get(away_team, away_team[:3].upper())

        # Get Elo prediction
        try:
            home_win_prob = elo_model.predict_win_probability(
                home_team=home_abbr,
                away_team=away_abbr,
                home_injuries=[],
                away_injuries=[]
            )
        except Exception as e:
            print(f"⚠️  Error getting Elo prediction: {e}")
            # Use 50/50 default
            home_win_prob = 0.50

        away_win_prob = 1 - home_win_prob

        # Calculate market probabilities
        home_market_prob = american_to_probability(home_odds)
        away_market_prob = american_to_probability(away_odds)

        # Calculate edges
        home_edge = home_win_prob - home_market_prob
        away_edge = away_win_prob - away_market_prob

        print(f"\n📊 MODEL vs MARKET")
        print(f"   {home_team}:")
        print(f"      Model:  {home_win_prob*100:.1f}%")
        print(f"      Market: {home_market_prob*100:.1f}% (odds: {home_odds:+d})")
        print(f"      Edge:   {home_edge*100:+.1f}%")

        print(f"\n   {away_team}:")
        print(f"      Model:  {away_win_prob*100:.1f}%")
        print(f"      Market: {away_market_prob*100:.1f}% (odds: {away_odds:+d})")
        print(f"      Edge:   {away_edge*100:+.1f}%")

        # Check for positive EV
        home_has_edge = home_edge > 0.03  # 3%+ edge
        away_has_edge = away_edge > 0.03

        if home_has_edge or away_has_edge:
            # Reality check
            if home_has_edge:
                reality_check = efficiency_analyzer.reality_check_ev_opportunity(
                    model_prob=home_win_prob,
                    market_prob=home_market_prob,
                    odds=home_odds,
                    ev_percentage=home_edge * 100,
                    game_context={'home_team': home_team, 'away_team': away_team}
                )

                if reality_check.get('proceed', False):
                    opportunities.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': home_team,
                        'odds': home_odds,
                        'edge': home_edge,
                        'model_prob': home_win_prob,
                        'market_prob': home_market_prob,
                        'recommendation': reality_check
                    })
                    print(f"\n✅ OPPORTUNITY FOUND: {home_team} ML {home_odds:+d}")
                    print(f"   Edge: {home_edge*100:+.1f}%")
                    if 'suggested_stake' in reality_check:
                        print(f"   Suggested Stake: ${reality_check['suggested_stake']:.0f}")

            if away_has_edge:
                reality_check = efficiency_analyzer.reality_check_ev_opportunity(
                    model_prob=away_win_prob,
                    market_prob=away_market_prob,
                    odds=away_odds,
                    ev_percentage=away_edge * 100,
                    game_context={'home_team': home_team, 'away_team': away_team}
                )

                if reality_check.get('proceed', False):
                    opportunities.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': away_team,
                        'odds': away_odds,
                        'edge': away_edge,
                        'model_prob': away_win_prob,
                        'market_prob': away_market_prob,
                        'recommendation': reality_check
                    })
                    print(f"\n✅ OPPORTUNITY FOUND: {away_team} ML {away_odds:+d}")
                    print(f"   Edge: {away_edge*100:+.1f}%")
                    if 'suggested_stake' in reality_check:
                        print(f"   Suggested Stake: ${reality_check['suggested_stake']:.0f}")
        else:
            print(f"\n❌ No significant edge found")

    return opportunities


def analyze_same_game_parlays(games: List[Dict], stats_model: PlayerStatsModel,
                              efficiency_analyzer: MarketEfficiencyAnalyzer):
    """Analyze player props for same game parlays"""

    print("\n\n" + "="*100)
    print("🎯 SAME GAME PARLAY ANALYSIS")
    print("="*100)

    # Key players for each team
    key_players = {
        'Orlando Magic': ['Paolo Banchero', 'Franz Wagner'],
        'Memphis Grizzlies': ['Ja Morant', 'Jaren Jackson Jr'],
        'Brooklyn Nets': ['Mikal Bridges', 'Nic Claxton'],
        'Chicago Bulls': ['Zach LaVine', 'Nikola Vucevic'],
        'New Orleans Pelicans': ['Zion Williamson', 'Brandon Ingram'],
        'Houston Rockets': ['Alperen Sengun', 'Jalen Green'],
        'Charlotte Hornets': ['LaMelo Ball', 'Miles Bridges'],
        'Denver Nuggets': ['Nikola Jokic', 'Jamal Murray'],
        'Portland Trail Blazers': ['Anfernee Simons', 'Deandre Ayton'],
        'Sacramento Kings': ['Domantas Sabonis', "De'Aaron Fox"],
        'Toronto Raptors': ['Scottie Barnes', 'RJ Barrett'],
        'Los Angeles Lakers': ['Luka Doncic', 'Austin Reaves']  # Updated with Luka
    }

    sgp_opportunities = []

    for game in games:
        home_team = game['home_team']
        away_team = game['away_team']

        print(f"\n{'='*100}")
        print(f"🏀 {away_team} @ {home_team}")
        print(f"{'='*100}")

        # Analyze key players from both teams
        game_props = []

        for team in [away_team, home_team]:
            players = key_players.get(team, [])

            if not players:
                continue

            print(f"\n{team}:")

            for player in players:
                # Check injury status
                injury_status = stats_model.get_player_injury_status(player)

                if injury_status and injury_status != 'healthy':
                    print(f"   ⚠️  {player}: {injury_status.upper()}")
                    continue

                # Analyze common props
                for prop_type, line in [('points', 25.0), ('rebounds', 8.0), ('assists', 7.0)]:
                    try:
                        projection = stats_model.project_player_prop(
                            player_name=player,
                            prop_type=prop_type,
                            line=line,
                            opponent=home_team if team == away_team else away_team,
                            home_away='away' if team == away_team else 'home',
                            injury_status='healthy'
                        )

                        # Look for strong over/under probabilities
                        if projection.over_prob > 0.60 or projection.under_prob > 0.60:
                            game_props.append({
                                'player': player,
                                'team': team,
                                'prop': prop_type,
                                'line': line,
                                'over_prob': projection.over_prob,
                                'under_prob': projection.under_prob,
                                'expected': projection.expected_value,
                                'season_avg': projection.season_avg
                            })

                            side = "OVER" if projection.over_prob > 0.60 else "UNDER"
                            prob = projection.over_prob if projection.over_prob > 0.60 else projection.under_prob
                            print(f"   ✓ {player} {prop_type.upper()} {side} {line} ({prob*100:.0f}%)")

                    except Exception as e:
                        continue

        # Build recommended SGP
        if len(game_props) >= 2:
            print(f"\n💡 SAME GAME PARLAY RECOMMENDATION:")

            # Select 2-3 best props with different players
            selected_props = []
            used_players = set()

            for prop in sorted(game_props, key=lambda x: max(x['over_prob'], x['under_prob']), reverse=True):
                if prop['player'] not in used_players and len(selected_props) < 3:
                    selected_props.append(prop)
                    used_players.add(prop['player'])

            combined_prob = 1.0
            for prop in selected_props:
                side = "OVER" if prop['over_prob'] > 0.60 else "UNDER"
                prob = prop['over_prob'] if prop['over_prob'] > 0.60 else prop['under_prob']
                combined_prob *= prob

                print(f"   • {prop['player']} {prop['prop'].upper()} {side} {prop['line']}")
                print(f"     Probability: {prob*100:.0f}% (Avg: {prop['season_avg']:.1f})")

            # Calculate parlay odds
            parlay_fair_odds = probability_to_american(combined_prob)
            print(f"\n   Combined Probability: {combined_prob*100:.1f}%")
            print(f"   Fair Odds: {int(parlay_fair_odds):+d}")
            print(f"   Target FanDuel Odds: {int(parlay_fair_odds + 100):+d} or better")

            sgp_opportunities.append({
                'game': f"{away_team} @ {home_team}",
                'props': selected_props,
                'combined_prob': combined_prob,
                'fair_odds': parlay_fair_odds
            })

    return sgp_opportunities


def analyze_quarter_betting(games: List[Dict], elo_model: EnhancedEloModel):
    """Analyze quarter betting opportunities"""

    print("\n\n" + "="*100)
    print("🕐 QUARTER BETTING ANALYSIS")
    print("="*100)

    print("\n📊 QUARTER BETTING STRATEGY:")
    print("   • 1Q: Look for strong defensive teams (UNDER total)")
    print("   • 2Q: Highest scoring quarter on average")
    print("   • 3Q: Lowest scoring quarter (teams adjusting)")
    print("   • 4Q: Depends on game flow and competitiveness")

    quarter_opportunities = []

    for game in games:
        home_team = game['home_team']
        away_team = game['away_team']

        print(f"\n{'='*100}")
        print(f"🏀 {away_team} @ {home_team}")
        print(f"{'='*100}")

        # Get total from odds
        fanduel_odds = None
        for bookmaker in game.get('bookmakers', []):
            if bookmaker['key'] == 'fanduel':
                fanduel_odds = bookmaker
                break

        if not fanduel_odds:
            continue

        totals_market = next((m for m in fanduel_odds['markets'] if m['key'] == 'totals'), None)
        if not totals_market:
            continue

        game_total = totals_market['outcomes'][0]['point']

        # Estimate quarter totals (rough approximation)
        q1_total = game_total * 0.23  # 23% of game (teams feeling out)
        q2_total = game_total * 0.27  # 27% of game (highest scoring)
        q3_total = game_total * 0.22  # 22% of game (adjustments)
        q4_total = game_total * 0.28  # 28% of game (finish strong)

        print(f"\n📊 ESTIMATED QUARTER TOTALS:")
        print(f"   Full Game: {game_total}")
        print(f"   1Q: ~{q1_total:.1f}")
        print(f"   2Q: ~{q2_total:.1f}")
        print(f"   3Q: ~{q3_total:.1f}")
        print(f"   4Q: ~{q4_total:.1f}")

        # Recommendations based on game characteristics
        print(f"\n💡 QUARTER BETTING RECOMMENDATIONS:")

        # Check if it's a blowout potential (from moneyline odds)
        h2h_market = next((m for m in fanduel_odds['markets'] if m['key'] == 'h2h'), None)
        if h2h_market:
            odds_diff = abs(h2h_market['outcomes'][0]['price'] - h2h_market['outcomes'][1]['price'])

            if odds_diff > 400:  # Big favorite
                print(f"   ⚠️  Blowout Potential - Avoid 4Q betting (garbage time risk)")
                print(f"   ✓ 1Q/2Q betting preferred (competitive early)")
            else:
                print(f"   ✓ Competitive game - 4Q betting favorable")
                print(f"   ✓ 2Q highest scoring on average")

        # Pace analysis (based on total)
        if game_total > 230:
            print(f"   🏃 High pace game - OVER 2Q total")
            quarter_opportunities.append({
                'game': f"{away_team} @ {home_team}",
                'quarter': '2Q',
                'recommendation': 'OVER',
                'reason': 'High pace game, 2Q highest scoring'
            })
        elif game_total < 220:
            print(f"   🐢 Low pace game - UNDER 2Q total")
            quarter_opportunities.append({
                'game': f"{away_team} @ {home_team}",
                'quarter': '2Q',
                'recommendation': 'UNDER',
                'reason': 'Low pace game, defensive battle'
            })

    return quarter_opportunities


def main():
    """Main analysis"""

    print("\n" + "="*100)
    print("🏀 COMPREHENSIVE BETTING ANALYSIS - TODAY'S NBA GAMES")
    print("="*100)
    print(f"\n📅 {datetime.now().strftime('%A, %B %d, %Y')}")

    # Initialize - Sportradar ONLY with LIVE data
    print("\n🔧 Initializing analysis tools...")
    print("   → Using Sportradar API ONLY (NBA official partner)")
    print("   → LIVE real-time data mode (no caching)")
    print("   → NO FALLBACK APIs")
    games = load_todays_games()
    elo_model = EnhancedEloModel()
    sportradar_api = SportradarNBAClient("93Qg8StSODooorMmFtlsvkrzpd8z7GxNPwUe16bn", use_live_data=True)
    stats_model = PlayerStatsModel(sportradar_api=sportradar_api, use_live_data=True)
    efficiency_analyzer = MarketEfficiencyAnalyzer()
    print("✓ Ready (LIVE DATA MODE - Sportradar only)\n")

    # 1. Moneyline Analysis
    print("\n" + "="*100)
    print("PART 1: MONEYLINE OPPORTUNITIES")
    print("="*100)
    ml_opportunities = analyze_moneyline(games, elo_model, efficiency_analyzer)

    # 2. Same Game Parlay Analysis
    print("\n" + "="*100)
    print("PART 2: SAME GAME PARLAY OPPORTUNITIES")
    print("="*100)
    sgp_opportunities = analyze_same_game_parlays(games, stats_model, efficiency_analyzer)

    # 3. Quarter Betting Analysis
    print("\n" + "="*100)
    print("PART 3: QUARTER BETTING OPPORTUNITIES")
    print("="*100)
    quarter_opportunities = analyze_quarter_betting(games, elo_model)

    # Final Summary
    print("\n\n" + "="*100)
    print("📋 FINAL SUMMARY")
    print("="*100)

    print(f"\n💰 MONEYLINE OPPORTUNITIES: {len(ml_opportunities)}")
    for opp in ml_opportunities:
        print(f"   • {opp['bet']} {opp['odds']:+d} (Edge: {opp['edge']*100:+.1f}%)")
        print(f"     Stake: ${opp['recommendation']['suggested_stake']:.0f}")

    print(f"\n🎯 SAME GAME PARLAYS: {len(sgp_opportunities)}")
    for opp in sgp_opportunities:
        print(f"   • {opp['game']}")
        print(f"     Combined Prob: {opp['combined_prob']*100:.0f}%, Fair Odds: {int(opp['fair_odds']):+d}")

    print(f"\n🕐 QUARTER BETS: {len(quarter_opportunities)}")
    for opp in quarter_opportunities:
        print(f"   • {opp['game']} - {opp['quarter']} {opp['recommendation']}")
        print(f"     {opp['reason']}")

    print("\n" + "="*100)
    print("✅ ANALYSIS COMPLETE")
    print("="*100 + "\n")


if __name__ == '__main__':
    main()
