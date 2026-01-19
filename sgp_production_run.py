#!/usr/bin/env python3
"""
Same Game Parlay Production Run

Comprehensive player props and SGP analysis with:
- Live player prop odds
- Injury status integration
- Player performance projections
- Correlation analysis for SGPs
- Monte Carlo simulations
- Probability distributions
- ASCII visualizations
"""

import sys
import os
import numpy as np
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from player_props.player_props import PlayerPropsAPI, PlayerProp
from player_props.player_stats_model import PlayerStatsModel
from player_props.sgp_analyzer import SGPAnalyzer
from odds.fanduel_odds_utils import american_to_probability, calculate_profit
from evaluation.market_efficiency import MarketEfficiencyAnalyzer


def create_ascii_histogram(data, title, width=60):
    """Create ASCII histogram"""

    lines = []
    lines.append(title)
    lines.append("-" * width)

    if len(data) == 0:
        lines.append("No data")
        return "\n".join(lines)

    min_val = np.min(data)
    max_val = np.max(data)
    num_bins = 20

    bins = np.linspace(min_val, max_val, num_bins + 1)
    hist, _ = np.histogram(data, bins=bins)

    max_count = np.max(hist)

    for i in range(num_bins):
        bin_start = bins[i]
        bin_end = bins[i + 1]
        count = hist[i]

        bar_length = int((count / max_count) * (width - 25)) if max_count > 0 else 0
        bar = '█' * bar_length

        lines.append(f"${bin_start:>7.0f} to ${bin_end:>7.0f} │{bar:<{width-25}} {count:>4}")

    lines.append("-" * width)

    return "\n".join(lines)


def create_probability_bar(model_prob, market_prob, label):
    """Create visual probability comparison"""

    lines = []
    lines.append(f"\n📊 {label}")
    lines.append("=" * 70)

    model_bar = '█' * int(model_prob * 50)
    lines.append(f"Model  ({model_prob*100:5.1f}%): │{model_bar:<50}│")

    market_bar = '░' * int(market_prob * 50)
    lines.append(f"Market ({market_prob*100:5.1f}%): │{market_bar:<50}│")

    edge = model_prob - market_prob
    if edge > 0:
        edge_marker = "↑" * min(int(abs(edge) * 200), 10)
        lines.append(f"\nEdge: +{edge*100:.1f}% {edge_marker}")
    else:
        edge_marker = "↓" * min(int(abs(edge) * 200), 10)
        lines.append(f"\nEdge: {edge*100:.1f}% {edge_marker}")

    return "\n".join(lines)


def run_prop_monte_carlo(player_name, prop_type, line, side, odds, probability, n_sims=10000):
    """Run Monte Carlo simulation for single prop"""

    results = []
    stake = 100

    for _ in range(n_sims):
        won = np.random.random() < probability

        if won:
            if odds > 0:
                profit = stake * (odds / 100)
            else:
                profit = stake * (100 / abs(odds))
        else:
            profit = -stake

        results.append(profit)

    results = np.array(results)

    return {
        'mean': np.mean(results),
        'median': np.median(results),
        'std': np.std(results),
        'p5': np.percentile(results, 5),
        'p25': np.percentile(results, 25),
        'p75': np.percentile(results, 75),
        'p95': np.percentile(results, 95),
        'prob_profit': np.sum(results > 0) / n_sims,
        'results': results
    }


def run_sgp_monte_carlo(parlay_props, parlay_odds, true_prob, n_sims=10000):
    """Run Monte Carlo simulation for SGP"""

    results = []
    stake = 100

    for _ in range(n_sims):
        # Simulate parlay win
        won = np.random.random() < true_prob

        if won:
            if parlay_odds > 0:
                profit = stake * (parlay_odds / 100)
            else:
                profit = stake * (100 / abs(parlay_odds))
        else:
            profit = -stake

        results.append(profit)

    results = np.array(results)

    return {
        'mean': np.mean(results),
        'median': np.median(results),
        'std': np.std(results),
        'p5': np.percentile(results, 5),
        'p95': np.percentile(results, 95),
        'prob_profit': np.sum(results > 0) / n_sims,
        'results': results
    }


def display_prop_analysis(prop_analysis, mc_stats):
    """Display single prop analysis with Monte Carlo results"""

    lines = []
    lines.append("\n" + "=" * 100)
    lines.append(f"🏀 {prop_analysis['player']} - {prop_analysis['prop_type'].upper()} {prop_analysis['best_side'].upper()} {prop_analysis['line']}")
    lines.append("=" * 100)

    lines.append(f"\nProjection: {prop_analysis['expected_value']:.1f} (Line: {prop_analysis['line']})")
    lines.append(f"Best Side: {prop_analysis['best_side'].upper()} ({prop_analysis['best_odds']:+d})")
    lines.append(f"Model Probability: {prop_analysis['best_prob']*100:.1f}%")
    lines.append(f"Edge: {prop_analysis['best_edge']*100:+.1f}%")

    # Probability distribution
    market_prob = american_to_probability(prop_analysis['best_odds'])
    lines.append(create_probability_bar(
        prop_analysis['best_prob'],
        market_prob,
        f"{prop_analysis['player']} {prop_analysis['prop_type']} {prop_analysis['best_side']}"
    ))

    # Monte Carlo results
    lines.append("\n")
    lines.append("🎲 MONTE CARLO SIMULATION (10,000 trials)")
    lines.append("-" * 100)
    lines.append(f"  Expected Profit:       ${mc_stats['mean']:>8.2f}")
    lines.append(f"  Median Outcome:        ${mc_stats['median']:>8.2f}")
    lines.append(f"  Probability of Win:    {mc_stats['prob_profit']*100:>7.1f}%")
    lines.append(f"")
    lines.append(f"  Best Case (95th):      +${mc_stats['p95']:>7.2f}")
    lines.append(f"  Upper Quartile:        ${mc_stats['p75']:>8.2f}")
    lines.append(f"  Lower Quartile:        ${mc_stats['p25']:>8.2f}")
    lines.append(f"  Worst Case (5th):      ${mc_stats['p5']:>8.2f}")
    lines.append("")

    # Histogram
    lines.append(create_ascii_histogram(mc_stats['results'], "PROFIT DISTRIBUTION"))

    return "\n".join(lines)


def display_sgp_analysis(parlay, mc_stats):
    """Display SGP analysis with correlations"""

    lines = []
    lines.append("\n" + "=" * 100)
    lines.append(f"🎯 SAME GAME PARLAY ({len(parlay.props)} LEGS) - {parlay.combined_odds:+d} ODDS")
    lines.append("=" * 100)

    # List legs
    lines.append("\nParlay Legs:")
    for i, prop in enumerate(parlay.props, 1):
        lines.append(f"  {i}. {prop['player']} {prop['prop_type']} {prop['best_side']} {prop.get('line', '')} ({prop['best_odds']:+d})")

    lines.append("")
    lines.append("CORRELATION ANALYSIS")
    lines.append("-" * 100)
    lines.append(f"  Naive Probability (independent):  {parlay.naive_probability*100:.2f}%")
    lines.append(f"  True Probability (correlated):    {parlay.true_probability*100:.2f}%")
    lines.append(f"  Correlation Impact:                {parlay.correlation_impact*100:+.2f}%")
    lines.append("")

    # Edge analysis
    implied_prob = american_to_probability(parlay.combined_odds)
    lines.append(f"  Implied Probability (odds):        {implied_prob*100:.2f}%")
    lines.append(f"  Edge:                              {parlay.edge*100:+.2f}%")
    lines.append(f"  Adjusted EV:                       {parlay.adjusted_ev:+.1f}%")

    # Monte Carlo
    lines.append("\n")
    lines.append("🎲 MONTE CARLO SIMULATION (10,000 trials)")
    lines.append("-" * 100)
    lines.append(f"  Expected Profit:       ${mc_stats['mean']:>8.2f}")
    lines.append(f"  Median Outcome:        ${mc_stats['median']:>8.2f}")
    lines.append(f"  Probability of Win:    {mc_stats['prob_profit']*100:>7.1f}%")
    lines.append(f"")
    lines.append(f"  Best Case (95th):      +${mc_stats['p95']:>7.2f}")
    lines.append(f"  Worst Case (5th):      ${mc_stats['p5']:>8.2f}")
    lines.append("")

    # Histogram
    lines.append(create_ascii_histogram(mc_stats['results'], "PARLAY PROFIT DISTRIBUTION"))

    return "\n".join(lines)


def main():
    """Main SGP production run"""

    if len(sys.argv) < 2:
        print("Usage: python3 sgp_production_run.py YOUR_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1].strip()

    print()
    print("=" * 100)
    print("🏀 NBA SAME GAME PARLAY BUILDER - PRODUCTION RUN")
    print("=" * 100)
    print()

    # Initialize components
    print("Initializing analysis components...")
    props_api = PlayerPropsAPI(api_key)
    stats_model = PlayerStatsModel()
    sgp_analyzer = SGPAnalyzer()
    efficiency_analyzer = MarketEfficiencyAnalyzer()

    # Fetch player props
    print("Fetching player props from The Odds API...")
    print("(This may take 30-60 seconds for all prop markets)")
    print()

    all_props = props_api.fetch_player_props(
        markets=['player_points', 'player_rebounds', 'player_assists', 'player_threes']
    )

    if not all_props:
        print("No player props found.")
        sys.exit(1)

    print(f"Found {len(all_props)} player props")
    print()

    # Analyze each prop
    print("=" * 100)
    print("🎯 ANALYZING INDIVIDUAL PLAYER PROPS")
    print("=" * 100)
    print()

    prop_analyses = []

    for prop in all_props[:50]:  # Limit to first 50 for performance
        # Project player performance
        projection = stats_model.project_player_prop(
            player_name=prop.player_name,
            prop_type=prop.prop_type,
            line=prop.line,
            opponent=prop.opponent,
            home_away=prop.home_away
        )

        # Calculate edge
        edge_analysis = stats_model.estimate_prop_edge(
            projection,
            prop.over_odds,
            prop.under_odds
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

    print(f"Found {len(positive_props)} props with positive adjusted EV > 3%")
    print()

    # Display top 5 individual props
    print("=" * 100)
    print("🔥 TOP INDIVIDUAL PLAYER PROPS")
    print("=" * 100)

    for i, prop in enumerate(positive_props[:5], 1):
        # Run Monte Carlo
        mc_stats = run_prop_monte_carlo(
            prop['player'],
            prop['prop_type'],
            prop['line'],
            prop['best_side'],
            prop['best_odds'],
            prop['best_prob']
        )

        print(display_prop_analysis(prop, mc_stats))

    # Build SGP combinations
    if len(positive_props) >= 2:
        print("\n")
        print("=" * 100)
        print("🎯 BUILDING SAME GAME PARLAY COMBINATIONS")
        print("=" * 100)
        print()

        # Group by game (simplified - would need game context)
        game_context = {'game_id': '1'}  # Placeholder

        sgp_opportunities = sgp_analyzer.find_sgp_opportunities(
            all_props=positive_props,
            game_context=game_context,
            max_legs=3,
            min_odds=200
        )

        if sgp_opportunities:
            print(f"Found {len(sgp_opportunities)} SGP opportunities")
            print()

            # Display top 3 SGPs
            for i, parlay in enumerate(sgp_opportunities[:3], 1):
                # Run Monte Carlo
                mc_stats = run_sgp_monte_carlo(
                    parlay.props,
                    parlay.combined_odds,
                    parlay.true_probability
                )

                print(display_sgp_analysis(parlay, mc_stats))

        else:
            print("No profitable SGP combinations found.")
            print("This is normal - most SGPs are correctly priced by bookmakers.")
    else:
        print("\n")
        print("Not enough positive EV props to build SGPs.")

    print("\n")
    print("=" * 100)
    print("⚠️  CRITICAL REMINDERS")
    print("=" * 100)
    print()
    print("1. PLAYER PROPS ARE HIGHLY VARIABLE")
    print("   - Injuries, foul trouble, blowouts can all affect outcomes")
    print("   - Even strong projections lose 30-40% of the time")
    print()
    print("2. SGP CORRELATIONS ARE ESTIMATES")
    print("   - True correlations are complex and context-dependent")
    print("   - Bookmakers have sophisticated SGP pricing models")
    print()
    print("3. INJURY STATUS IS CRITICAL")
    print("   - Always check latest injury reports before betting")
    print("   - Late scratches can invalidate entire analysis")
    print()
    print("4. SAMPLE SIZE MATTERS")
    print("   - Player performance varies game-to-game")
    print("   - Need 50+ prop bets to validate edge")
    print()
    print("To log bets:")
    print("  python3 log_bet_results.py")
    print()
    print("Good luck! 🍀")
    print()


if __name__ == '__main__':
    main()
