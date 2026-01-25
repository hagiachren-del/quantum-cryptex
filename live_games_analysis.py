#!/usr/bin/env python3
"""
Quick Live Games Analysis for Specific Matchups
Usage: python3 live_games_analysis.py [BALLDONTLIE_API_KEY]
"""

import sys
import os

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from models.enhanced_elo_model import EnhancedEloModel
from odds.fanduel_odds_utils import probability_to_american
from data.balldontlie_api import BallDontLieAPI

def analyze_matchup(home_team, away_team, elo_model, balldontlie_api=None):
    """Analyze a specific matchup"""

    print("\n" + "=" * 80)
    print(f"🏀 {away_team} @ {home_team}")
    print("=" * 80)

    # Current Elo ratings (2024-25 season estimates)
    ELO_RATINGS = {
        'Miami Heat': 1525,
        'Utah Jazz': 1425,
        'Los Angeles Lakers': 1565,
        'Dallas Mavericks': 1550,
    }

    home_elo = ELO_RATINGS.get(home_team, 1500)
    away_elo = ELO_RATINGS.get(away_team, 1500)

    elo_model.set_rating(home_team, home_elo)
    elo_model.set_rating(away_team, away_elo)

    print(f"\n📊 ELO RATINGS")
    print(f"   {home_team}: {home_elo}")
    print(f"   {away_team}: {away_elo}")

    # Get prediction
    home_prob = elo_model.predict_win_probability(
        home_team=home_team,
        away_team=away_team,
        home_rest_days=2,
        away_rest_days=2
    )

    away_prob = 1 - home_prob

    # Calculate fair odds
    home_fair_odds = probability_to_american(home_prob)
    away_fair_odds = probability_to_american(away_prob)

    print(f"\n🎯 MODEL PREDICTION")
    print(f"   {home_team}: {home_prob*100:.1f}% ({int(home_fair_odds):+d})")
    print(f"   {away_team}: {away_prob*100:.1f}% ({int(away_fair_odds):+d})")

    # Check for injuries if API available
    if balldontlie_api:
        print(f"\n🏥 CHECKING INJURIES...")
        try:
            injuries = balldontlie_api.get_injuries()

            home_injuries = [inj for inj in injuries if inj.team == home_team]
            away_injuries = [inj for inj in injuries if inj.team == away_team]

            if home_injuries:
                print(f"\n   {home_team} Injuries:")
                for inj in home_injuries[:5]:
                    print(f"      • {inj.player_name}: {inj.status} - {inj.injury}")
            else:
                print(f"   {home_team}: No major injuries")

            if away_injuries:
                print(f"\n   {away_team} Injuries:")
                for inj in away_injuries[:5]:
                    print(f"      • {inj.player_name}: {inj.status} - {inj.injury}")
            else:
                print(f"   {away_team}: No major injuries")
        except Exception as e:
            print(f"   ⚠️  Could not fetch injury data: {e}")

    print(f"\n💡 RECOMMENDATION")
    if abs(home_prob - 0.5) < 0.05:
        print(f"   This is a TOSS-UP game - avoid betting without real odds")
    elif home_prob > 0.60:
        print(f"   Model favors {home_team} - look for value on {home_team} ML")
    elif away_prob > 0.60:
        print(f"   Model favors {away_team} - look for value on {away_team} ML")
    else:
        print(f"   Competitive game - check live odds for value")

    print("=" * 80)

def main():
    """Main analysis"""

    print("\n" + "=" * 80)
    print("🏀 LIVE GAMES ANALYSIS")
    print("=" * 80)

    # Check for BallDontLie API key
    balldontlie_api = None
    if len(sys.argv) >= 2:
        api_key = sys.argv[1].strip()
        print(f"\n✓ Using BallDontLie API for injury data")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        balldontlie_api = BallDontLieAPI(api_key)
    else:
        print(f"\n⚠️  No BallDontLie API key provided")
        print(f"   Usage: python3 live_games_analysis.py YOUR_BALLDONTLIE_KEY")
        print(f"   Continuing with Elo analysis only...")

    # Initialize Elo model
    print(f"\n🧮 Initializing Enhanced Elo model...")
    elo_model = EnhancedEloModel()

    # Analyze specific matchups
    print(f"\n{'='*80}")
    print("ANALYZING REQUESTED GAMES")
    print('='*80)

    analyze_matchup("Utah Jazz", "Miami Heat", elo_model, balldontlie_api)
    analyze_matchup("Dallas Mavericks", "Los Angeles Lakers", elo_model, balldontlie_api)

    print(f"\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Compare these predictions with FanDuel odds")
    print(f"   2. Look for 3%+ edge on either side")
    print(f"   3. Check injury reports 90 mins before tipoff")
    print(f"   4. Consider live betting if odds drift significantly")
    print()

if __name__ == '__main__':
    main()
