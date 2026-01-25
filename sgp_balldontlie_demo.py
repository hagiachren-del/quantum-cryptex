#!/usr/bin/env python3
"""
Same Game Parlay Production Run with BallDontLie API Integration

This script demonstrates using real player stats from BallDontLie API
for accurate player prop projections and SGP analysis.

Usage:
  With BallDontLie API key (for real stats):
    python3 sgp_balldontlie_demo.py YOUR_ODDS_API_KEY YOUR_BALLDONTLIE_API_KEY

  Without BallDontLie API key (demo mode):
    python3 sgp_balldontlie_demo.py YOUR_ODDS_API_KEY
"""

import sys
import os
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from player_props.player_stats_model import PlayerStatsModel
from player_props.sgp_analyzer import SGPAnalyzer
from data.balldontlie_api import BallDontLieAPI
from odds.fanduel_odds_utils import american_to_probability, calculate_profit
from evaluation.market_efficiency import MarketEfficiencyAnalyzer


# Demo player props for Saturday, January 17, 2026
DEMO_PROPS = [
    # Lakers @ Warriors - 3:30 PM EST
    {'player': 'LeBron James', 'team': 'LAL', 'opponent': 'GSW', 'prop_type': 'points',
     'line': 24.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'LeBron James', 'team': 'LAL', 'opponent': 'GSW', 'prop_type': 'rebounds',
     'line': 7.5, 'over_odds': -115, 'under_odds': -105, 'home_away': 'away'},
    {'player': 'LeBron James', 'team': 'LAL', 'opponent': 'GSW', 'prop_type': 'assists',
     'line': 7.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'away'},

    {'player': 'Stephen Curry', 'team': 'GSW', 'opponent': 'LAL', 'prop_type': 'points',
     'line': 27.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Stephen Curry', 'team': 'GSW', 'opponent': 'LAL', 'prop_type': 'threes',
     'line': 4.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'home'},
    {'player': 'Stephen Curry', 'team': 'GSW', 'opponent': 'LAL', 'prop_type': 'assists',
     'line': 6.5, 'over_odds': -105, 'under_odds': -115, 'home_away': 'home'},

    # Celtics @ Nuggets - 8:00 PM EST
    {'player': 'Jayson Tatum', 'team': 'BOS', 'opponent': 'DEN', 'prop_type': 'points',
     'line': 28.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Jayson Tatum', 'team': 'BOS', 'opponent': 'DEN', 'prop_type': 'rebounds',
     'line': 8.5, 'over_odds': -115, 'under_odds': -105, 'home_away': 'away'},

    {'player': 'Nikola Jokic', 'team': 'DEN', 'opponent': 'BOS', 'prop_type': 'points',
     'line': 26.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Nikola Jokic', 'team': 'DEN', 'opponent': 'BOS', 'prop_type': 'rebounds',
     'line': 12.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'home'},
    {'player': 'Nikola Jokic', 'team': 'DEN', 'opponent': 'BOS', 'prop_type': 'assists',
     'line': 9.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
]


def test_balldontlie_api(api_key: str):
    """Test BallDontLie API connection"""

    print("\n" + "=" * 100)
    print("🔍 TESTING BALLDONTLIE API CONNECTION")
    print("=" * 100)
    print()

    api = BallDontLieAPI(api_key)

    # Test with a few prominent players
    test_players = ['LeBron James', 'Stephen Curry', 'Nikola Jokic']

    for player_name in test_players:
        print(f"Testing: {player_name}")

        try:
            # Search for player
            player_info = api.get_player_by_name(player_name)

            if player_info:
                print(f"  ✓ Found: {player_info.first_name} {player_info.last_name}")
                print(f"    Team: {player_info.team}")
                print(f"    Position: {player_info.position}")

                # Get season stats
                stats = api.get_player_season_averages(player_info.player_id, season=2024)

                if stats:
                    print(f"    Stats: {stats.points:.1f} PPG, {stats.rebounds:.1f} RPG, {stats.assists:.1f} APG")
                else:
                    print(f"    ⚠ No stats found for 2024 season")
            else:
                print(f"  ✗ Player not found")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")

        print()

    # Test injury report
    try:
        print("Fetching current injury report...")
        injuries = api.get_injuries()

        if injuries:
            print(f"  ✓ Found {len(injuries)} injured players")
            # Show first 3
            for injury in injuries[:3]:
                print(f"    - {injury.player_name}: {injury.status} ({injury.injury})")
        else:
            print(f"  ℹ No injuries found (or API endpoint unavailable)")

    except Exception as e:
        print(f"  ⚠ Could not fetch injuries: {str(e)}")

    print()


def run_sgp_analysis_with_real_stats(balldontlie_api_key: Optional[str] = None):
    """Run SGP analysis using BallDontLie API if key provided"""

    print("\n" + "=" * 100)
    print("🏀 NBA SAME GAME PARLAY BUILDER - WITH REAL PLAYER STATS")
    print("=" * 100)
    print()

    # Initialize BallDontLie API if key provided
    balldontlie_api = None
    if balldontlie_api_key:
        print("✓ Initializing BallDontLie API for real player stats...")
        balldontlie_api = BallDontLieAPI(balldontlie_api_key)
        test_balldontlie_api(balldontlie_api_key)
    else:
        print("ℹ No BallDontLie API key provided - using demo stats")
        print("  (Provide API key as 2nd argument to use real player data)")
        print()

    # Initialize models
    stats_model = PlayerStatsModel(balldontlie_api=balldontlie_api)
    sgp_analyzer = SGPAnalyzer()
    efficiency_analyzer = MarketEfficiencyAnalyzer()

    print("=" * 100)
    print("🎯 ANALYZING PLAYER PROPS")
    print("=" * 100)
    print()

    # Analyze props
    prop_analyses = []

    for prop in DEMO_PROPS:
        # Auto-fetch injury status if API available
        injury_status = None
        if balldontlie_api:
            injury_status = stats_model.get_player_injury_status(prop['player'])
            if injury_status and injury_status != 'healthy':
                print(f"⚠ {prop['player']} - Injury Status: {injury_status.upper()}")

        # Project player performance
        projection = stats_model.project_player_prop(
            player_name=prop['player'],
            prop_type=prop['prop_type'],
            line=prop['line'],
            opponent=prop['opponent'],
            home_away=prop['home_away'],
            injury_status=injury_status,
            days_rest=1
        )

        # Calculate edge
        edge_analysis = stats_model.estimate_prop_edge(
            projection,
            prop['over_odds'],
            prop['under_odds']
        )

        # Reality check
        reality_check = efficiency_analyzer.reality_check_ev_opportunity(
            model_prob=edge_analysis['best_prob'],
            market_prob=american_to_probability(edge_analysis['best_odds']),
            odds=edge_analysis['best_odds'],
            ev_percentage=edge_analysis['best_edge'] * 100
        )

        edge_analysis['adjusted_ev'] = reality_check['adjusted_ev']
        edge_analysis['recommendation'] = reality_check['recommendation']

        prop_analyses.append(edge_analysis)

    # Filter for positive EV
    positive_props = [
        p for p in prop_analyses
        if p['recommendation'] in ['PROCEED', 'PROCEED WITH CAUTION']
        and p['adjusted_ev'] > 3.0
    ]

    positive_props.sort(key=lambda x: x['adjusted_ev'], reverse=True)

    print(f"\nFound {len(positive_props)} props with positive adjusted EV > 3%")
    print()

    # Display results
    if positive_props:
        print("=" * 100)
        print("🔥 POSITIVE EV PLAYER PROPS")
        print("=" * 100)

        for i, prop in enumerate(positive_props, 1):
            print(f"\n{i}. {prop['player']} - {prop['prop_type'].upper()} {prop['best_side'].upper()} {prop['line']}")
            print(f"   Projection: {prop['expected_value']:.1f}")
            print(f"   Odds: {prop['best_odds']:+d}")
            print(f"   Model Probability: {prop['best_prob']*100:.1f}%")
            print(f"   Adjusted EV: {prop['adjusted_ev']:+.1f}%")
            print(f"   Recommendation: {prop['recommendation']}")
    else:
        print("No positive EV props found.")
        print("This is normal - player props markets are ~80-85% efficient.")

    # Build SGP combinations
    if len(positive_props) >= 2:
        print("\n")
        print("=" * 100)
        print("🎯 BUILDING SAME GAME PARLAY COMBINATIONS")
        print("=" * 100)
        print()

        game_context = {'game_id': '1'}  # Simplified

        sgp_opportunities = sgp_analyzer.find_sgp_opportunities(
            all_props=positive_props,
            game_context=game_context,
            max_legs=3,
            min_odds=200
        )

        if sgp_opportunities:
            print(f"Found {len(sgp_opportunities)} SGP opportunities\n")

            for i, parlay in enumerate(sgp_opportunities[:3], 1):
                print(f"\n{'=' * 100}")
                print(f"SGP #{i} - {len(parlay.props)} LEGS - {parlay.combined_odds:+d} ODDS")
                print('=' * 100)

                for j, prop in enumerate(parlay.props, 1):
                    print(f"  {j}. {prop['player']} {prop['prop_type']} {prop['best_side']} {prop.get('line', '')}")

                print()
                print(f"  Naive Probability:  {parlay.naive_probability*100:.2f}%")
                print(f"  True Probability:   {parlay.true_probability*100:.2f}%")
                print(f"  Correlation Impact: {parlay.correlation_impact*100:+.2f}%")
                print(f"  Edge:               {parlay.edge*100:+.2f}%")
                print(f"  Adjusted EV:        {parlay.adjusted_ev:+.1f}%")
        else:
            print("No profitable SGP combinations found.")
            print("Bookmakers price SGPs well - most are correctly priced.")

    print("\n")
    print("=" * 100)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 100)
    print()

    if balldontlie_api:
        print("✓ Used real player stats from BallDontLie API")
    else:
        print("ℹ Used demo stats - provide BallDontLie API key for real data")

    print()
    print("For full SGP analysis with Monte Carlo simulations, see:")
    print("  - sgp_production_run.py")
    print("  - SGP_GUIDE.md")
    print()


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  With BallDontLie API key:")
        print("    python3 sgp_balldontlie_demo.py YOUR_ODDS_API_KEY YOUR_BALLDONTLIE_API_KEY")
        print()
        print("  Without BallDontLie API key (demo mode):")
        print("    python3 sgp_balldontlie_demo.py YOUR_ODDS_API_KEY")
        sys.exit(1)

    # For now, just run with demo data
    # The Odds API key isn't used in this demo, but kept for consistency

    balldontlie_api_key = sys.argv[2].strip() if len(sys.argv) >= 3 else None

    run_sgp_analysis_with_real_stats(balldontlie_api_key)


if __name__ == '__main__':
    main()
