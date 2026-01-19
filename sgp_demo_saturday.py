#!/usr/bin/env python3
"""
SGP Demo Production Run - Saturday Games

Demonstrates full player props and SGP analysis using realistic data
from today's 10 NBA games.
"""

import sys
import numpy as np

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

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


def run_monte_carlo(probability, odds, n_sims=10000):
    """Run Monte Carlo simulation"""
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


# Realistic player props for today's games (Saturday, Jan 17, 2026)
TODAYS_PROPS = [
    # Orlando Magic @ Memphis Grizzlies (12:10 PM EST)
    {'player': 'Paolo Banchero', 'team': 'Magic', 'opponent': 'Grizzlies', 'prop_type': 'points', 'line': 22.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Franz Wagner', 'team': 'Magic', 'opponent': 'Grizzlies', 'prop_type': 'points', 'line': 18.5, 'over_odds': -115, 'under_odds': -105, 'home_away': 'away'},
    {'player': 'Jaren Jackson Jr', 'team': 'Grizzlies', 'opponent': 'Magic', 'prop_type': 'points', 'line': 21.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Desmond Bane', 'team': 'Grizzlies', 'opponent': 'Magic', 'prop_type': 'points', 'line': 24.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'home'},

    # Utah Jazz @ Dallas Mavericks (5:10 PM EST)
    {'player': 'Luka Doncic', 'team': 'Mavericks', 'opponent': 'Jazz', 'prop_type': 'points', 'line': 32.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Luka Doncic', 'team': 'Mavericks', 'opponent': 'Jazz', 'prop_type': 'assists', 'line': 8.5, 'over_odds': -105, 'under_odds': -115, 'home_away': 'home'},
    {'player': 'Luka Doncic', 'team': 'Mavericks', 'opponent': 'Jazz', 'prop_type': 'rebounds', 'line': 9.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Kyrie Irving', 'team': 'Mavericks', 'opponent': 'Jazz', 'prop_type': 'points', 'line': 25.5, 'over_odds': -115, 'under_odds': -105, 'home_away': 'home'},
    {'player': 'Lauri Markkanen', 'team': 'Jazz', 'opponent': 'Mavericks', 'prop_type': 'points', 'line': 23.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},

    # Phoenix Suns @ New York Knicks (7:40 PM EST)
    {'player': 'Jalen Brunson', 'team': 'Knicks', 'opponent': 'Suns', 'prop_type': 'points', 'line': 27.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Jalen Brunson', 'team': 'Knicks', 'opponent': 'Suns', 'prop_type': 'assists', 'line': 6.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'home'},
    {'player': 'Karl-Anthony Towns', 'team': 'Knicks', 'opponent': 'Suns', 'prop_type': 'points', 'line': 24.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Karl-Anthony Towns', 'team': 'Knicks', 'opponent': 'Suns', 'prop_type': 'rebounds', 'line': 12.5, 'over_odds': -115, 'under_odds': -105, 'home_away': 'home'},
    {'player': 'Kevin Durant', 'team': 'Suns', 'opponent': 'Knicks', 'prop_type': 'points', 'line': 27.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Devin Booker', 'team': 'Suns', 'opponent': 'Knicks', 'prop_type': 'points', 'line': 26.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},

    # Oklahoma City Thunder @ Miami Heat (8:10 PM EST)
    {'player': 'Shai Gilgeous-Alexander', 'team': 'Thunder', 'opponent': 'Heat', 'prop_type': 'points', 'line': 30.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'away'},
    {'player': 'Shai Gilgeous-Alexander', 'team': 'Thunder', 'opponent': 'Heat', 'prop_type': 'assists', 'line': 6.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Chet Holmgren', 'team': 'Thunder', 'opponent': 'Heat', 'prop_type': 'points', 'line': 16.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Chet Holmgren', 'team': 'Thunder', 'opponent': 'Heat', 'prop_type': 'rebounds', 'line': 7.5, 'over_odds': -105, 'under_odds': -115, 'home_away': 'away'},
    {'player': 'Tyler Herro', 'team': 'Heat', 'opponent': 'Thunder', 'prop_type': 'points', 'line': 22.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Bam Adebayo', 'team': 'Heat', 'opponent': 'Thunder', 'prop_type': 'points', 'line': 18.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Bam Adebayo', 'team': 'Heat', 'opponent': 'Thunder', 'prop_type': 'rebounds', 'line': 10.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},

    # Charlotte Hornets @ Golden State Warriors (8:40 PM EST)
    {'player': 'Stephen Curry', 'team': 'Warriors', 'opponent': 'Hornets', 'prop_type': 'points', 'line': 27.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Stephen Curry', 'team': 'Warriors', 'opponent': 'Hornets', 'prop_type': 'threes', 'line': 4.5, 'over_odds': -120, 'under_odds': +100, 'home_away': 'home'},
    {'player': 'Stephen Curry', 'team': 'Warriors', 'opponent': 'Hornets', 'prop_type': 'assists', 'line': 5.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'Andrew Wiggins', 'team': 'Warriors', 'opponent': 'Hornets', 'prop_type': 'points', 'line': 16.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
    {'player': 'LaMelo Ball', 'team': 'Hornets', 'opponent': 'Warriors', 'prop_type': 'points', 'line': 28.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'LaMelo Ball', 'team': 'Hornets', 'opponent': 'Warriors', 'prop_type': 'assists', 'line': 7.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},

    # Los Angeles Lakers @ Portland Trail Blazers (10:10 PM EST)
    {'player': 'LeBron James', 'team': 'Lakers', 'opponent': 'Trail Blazers', 'prop_type': 'points', 'line': 25.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'LeBron James', 'team': 'Lakers', 'opponent': 'Trail Blazers', 'prop_type': 'assists', 'line': 7.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'LeBron James', 'team': 'Lakers', 'opponent': 'Trail Blazers', 'prop_type': 'rebounds', 'line': 7.5, 'over_odds': -105, 'under_odds': -115, 'home_away': 'away'},
    {'player': 'Anthony Davis', 'team': 'Lakers', 'opponent': 'Trail Blazers', 'prop_type': 'points', 'line': 26.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Anthony Davis', 'team': 'Lakers', 'opponent': 'Trail Blazers', 'prop_type': 'rebounds', 'line': 11.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'away'},
    {'player': 'Anfernee Simons', 'team': 'Trail Blazers', 'opponent': 'Lakers', 'prop_type': 'points', 'line': 22.5, 'over_odds': -110, 'under_odds': -110, 'home_away': 'home'},
]


def main():
    """Run demo SGP analysis"""

    print()
    print("=" * 100)
    print("🏀 NBA SAME GAME PARLAY BUILDER - SATURDAY PRODUCTION RUN")
    print("=" * 100)
    print()
    print("Analyzing player props from today's 10 NBA games...")
    print()

    # Initialize components
    stats_model = PlayerStatsModel()
    sgp_analyzer = SGPAnalyzer()
    efficiency_analyzer = MarketEfficiencyAnalyzer()

    # Analyze all props
    prop_analyses = []

    for prop in TODAYS_PROPS:
        # Project player performance
        projection = stats_model.project_player_prop(
            player_name=prop['player'],
            prop_type=prop['prop_type'],
            line=prop['line'],
            opponent=prop['opponent'],
            home_away=prop['home_away'],
            injury_status='healthy',
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
        edge_analysis['warnings'] = reality_check['warnings']
        edge_analysis['home_away'] = prop['home_away']
        edge_analysis['team'] = prop['team']
        edge_analysis['opponent'] = prop['opponent']

        prop_analyses.append(edge_analysis)

    # Filter for positive EV
    positive_props = [
        p for p in prop_analyses
        if p['recommendation'] in ['PROCEED', 'PROCEED WITH CAUTION']
        and p['adjusted_ev'] > 3.0
    ]

    positive_props.sort(key=lambda x: x['adjusted_ev'], reverse=True)

    print(f"📊 ANALYSIS SUMMARY")
    print("=" * 100)
    print(f"Total Props Analyzed: {len(TODAYS_PROPS)}")
    print(f"Positive EV Props Found: {len(positive_props)}")
    print()

    # Display top individual props
    print("=" * 100)
    print("🔥 TOP 10 INDIVIDUAL PLAYER PROPS")
    print("=" * 100)

    for i, prop in enumerate(positive_props[:10], 1):
        # Run Monte Carlo
        mc_stats = run_monte_carlo(
            prop['best_prob'],
            prop['best_odds']
        )

        print(f"\n{'=' * 100}")
        print(f"#{i}: {prop['player']} - {prop['prop_type'].upper()} {prop['best_side'].upper()} {prop['line']}")
        print(f"{'=' * 100}")
        print(f"\nGame: {prop['team']} @ {prop['opponent']}")
        print(f"Projection: {prop['expected_value']:.1f} (Line: {prop['line']})")
        print(f"Best Side: {prop['best_side'].upper()} ({prop['best_odds']:+d})")
        print(f"Model Probability: {prop['best_prob']*100:.1f}%")
        print(f"Edge: {prop['best_edge']*100:+.1f}%")
        print(f"Adjusted EV: {prop['adjusted_ev']:+.1f}%")
        print(f"Recommendation: {prop['recommendation']}")

        if prop['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in prop['warnings'][:2]:
                level = warning['level']
                emoji = "🔴" if level == "CRITICAL" else "⚠️" if level == "MODERATE" else "ℹ️"
                print(f"  {emoji} [{level}] {warning['message']}")

        # Probability distribution
        market_prob = american_to_probability(prop['best_odds'])
        print(create_probability_bar(
            prop['best_prob'],
            market_prob,
            f"{prop['player']} {prop['prop_type']} {prop['best_side']}"
        ))

        # Monte Carlo results
        print("\n🎲 MONTE CARLO SIMULATION (10,000 trials)")
        print("-" * 100)
        print(f"  Expected Profit:       ${mc_stats['mean']:>8.2f}")
        print(f"  Median Outcome:        ${mc_stats['median']:>8.2f}")
        print(f"  Probability of Win:    {mc_stats['prob_profit']*100:>7.1f}%")
        print(f"")
        print(f"  Best Case (95th):      +${mc_stats['p95']:>7.2f}")
        print(f"  Upper Quartile:        ${mc_stats['p75']:>8.2f}")
        print(f"  Lower Quartile:        ${mc_stats['p25']:>8.2f}")
        print(f"  Worst Case (5th):      ${mc_stats['p5']:>8.2f}")
        print("")
        print(create_ascii_histogram(mc_stats['results'], "PROFIT DISTRIBUTION"))

    # Build SGPs for same game
    if len(positive_props) >= 2:
        print("\n\n")
        print("=" * 100)
        print("🎯 SAME GAME PARLAY OPPORTUNITIES")
        print("=" * 100)
        print()

        # Group props by game
        games = {}
        for prop in positive_props:
            game_key = f"{prop['team']} @ {prop['opponent']}"
            if game_key not in games:
                games[game_key] = []
            games[game_key].append(prop)

        # Build SGPs for each game with 3+ props
        sgp_count = 0
        for game_key, game_props in games.items():
            if len(game_props) >= 2:
                print(f"\n📍 {game_key}")
                print("-" * 100)

                # Try 2-leg and 3-leg combinations
                from itertools import combinations

                for num_legs in [2, 3]:
                    if len(game_props) < num_legs:
                        continue

                    for combo in list(combinations(game_props, num_legs))[:3]:  # Top 3 combos
                        # Calculate parlay odds
                        parlay_decimal = 1.0
                        for prop in combo:
                            odds = prop['best_odds']
                            if odds > 0:
                                parlay_decimal *= ((odds / 100) + 1)
                            else:
                                parlay_decimal *= ((100 / abs(odds)) + 1)

                        if parlay_decimal >= 2.0:
                            parlay_odds = int((parlay_decimal - 1) * 100)
                        else:
                            parlay_odds = int(-100 / (parlay_decimal - 1))

                        # Calculate probabilities
                        naive_prob = np.prod([p['best_prob'] for p in combo])

                        # Estimate correlation effect
                        # Simplified: Check if same player or teammates
                        same_player = len(set(p['player'] for p in combo)) == 1
                        same_team = len(set(p['team'] for p in combo)) == 1

                        if same_player:
                            correlation_factor = 1.15  # Positive correlation (playing time, hot hand)
                        elif same_team:
                            correlation_factor = 0.95  # Slight negative (limited possessions)
                        else:
                            correlation_factor = 1.05  # Opponents benefit from pace

                        true_prob = naive_prob * correlation_factor
                        true_prob = max(0.0, min(1.0, true_prob))

                        # Calculate edge
                        implied_prob = american_to_probability(parlay_odds)
                        edge = true_prob - implied_prob

                        if edge > 0.01:  # At least 1% edge
                            sgp_count += 1

                            print(f"\n🎯 SGP #{sgp_count}: {num_legs}-Leg Parlay ({parlay_odds:+d})")
                            print("-" * 100)

                            for j, prop in enumerate(combo, 1):
                                print(f"  {j}. {prop['player']} {prop['prop_type']} {prop['best_side']} {prop['line']} ({prop['best_odds']:+d})")

                            print(f"\nCORRELATION ANALYSIS:")
                            print(f"  Naive Probability (independent):  {naive_prob*100:.2f}%")
                            print(f"  True Probability (correlated):    {true_prob*100:.2f}%")
                            print(f"  Correlation Impact:                {(true_prob - naive_prob)*100:+.2f}%")
                            print(f"  Implied Probability (odds):        {implied_prob*100:.2f}%")
                            print(f"  Edge:                              {edge*100:+.2f}%")

                            # Monte Carlo for parlay
                            parlay_mc = run_monte_carlo(true_prob, parlay_odds)

                            print(f"\n🎲 MONTE CARLO SIMULATION (10,000 trials)")
                            print(f"  Expected Profit:       ${parlay_mc['mean']:>8.2f}")
                            print(f"  Median Outcome:        ${parlay_mc['median']:>8.2f}")
                            print(f"  Probability of Win:    {parlay_mc['prob_profit']*100:>7.1f}%")
                            print(f"  Best Case (95th):      +${parlay_mc['p95']:>7.2f}")
                            print(f"  Worst Case (5th):      ${parlay_mc['p5']:>8.2f}")

                            if sgp_count >= 5:  # Limit output
                                break

                    if sgp_count >= 5:
                        break

        if sgp_count == 0:
            print("\nNo profitable SGP combinations found.")
            print("This is normal - most SGPs are correctly priced by bookmakers.")

    print("\n\n")
    print("=" * 100)
    print("⚠️  CRITICAL REMINDERS")
    print("=" * 100)
    print()
    print("1. ALWAYS CHECK LATEST INJURY REPORTS")
    print("   - Player status can change up to 30 minutes before tipoff")
    print("   - Late scratches invalidate entire analysis")
    print()
    print("2. PLAYER PROPS HAVE HIGH VARIANCE")
    print("   - Blowouts, foul trouble, coach decisions all impact outcomes")
    print("   - Even 60% probability props lose 40% of the time")
    print()
    print("3. SGP CORRELATIONS ARE ESTIMATES")
    print("   - Same player props: Generally positive (playing time)")
    print("   - Teammate scoring: Negative (limited possessions)")
    print("   - Opponent props: Positive (game pace)")
    print()
    print("4. BANKROLL MANAGEMENT")
    print("   - Individual props: 1-3% of bankroll")
    print("   - SGPs: 0.5-2% of bankroll (higher variance)")
    print("   - Never chase losses with bigger stakes")
    print()
    print("5. TRACK YOUR RESULTS")
    print("   - Log every bet: python3 log_bet_results.py")
    print("   - Need 200+ prop bets to validate edge")
    print("   - Monitor win rate vs model expectations")
    print()
    print("Good luck! 🍀")
    print()


if __name__ == '__main__':
    main()
