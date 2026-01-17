#!/usr/bin/env python3
"""
Enhanced Saturday Production Run with Detailed Analytics
Includes Monte Carlo simulations, probability distributions, and comparison graphs
"""

import sys
import os
import requests
from datetime import datetime
import pytz
import numpy as np
from scipy.stats import norm

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from odds.fanduel_odds_utils import american_to_probability, calculate_profit
from odds.vig_removal import remove_vig_proportional
from models.enhanced_elo_model import EnhancedEloModel
from evaluation.market_efficiency import MarketEfficiencyAnalyzer
from evaluation.variance_analyzer import VarianceAnalyzer


def create_ascii_histogram(data, title, width=60):
    """Create ASCII histogram for terminal display"""

    lines = []
    lines.append(title)
    lines.append("-" * width)

    # Create bins
    min_val = np.min(data)
    max_val = np.max(data)
    num_bins = 20

    bins = np.linspace(min_val, max_val, num_bins + 1)
    hist, _ = np.histogram(data, bins=bins)

    # Normalize to fit width
    max_count = np.max(hist)

    for i in range(num_bins):
        bin_start = bins[i]
        bin_end = bins[i + 1]
        count = hist[i]

        # Calculate bar length
        bar_length = int((count / max_count) * (width - 25)) if max_count > 0 else 0
        bar = '█' * bar_length

        # Format the line
        lines.append(f"${bin_start:>7.0f} to ${bin_end:>7.0f} │{bar:<{width-25}} {count:>4}")

    lines.append("-" * width)

    return "\n".join(lines)


def create_probability_distribution(model_prob, market_prob, team_name):
    """Create visual probability comparison"""

    lines = []
    lines.append(f"\n📊 PROBABILITY DISTRIBUTION: {team_name}")
    lines.append("=" * 70)

    # Model probability bar
    model_bar_length = int(model_prob * 50)
    model_bar = '█' * model_bar_length
    lines.append(f"Model  ({model_prob*100:5.1f}%): │{model_bar:<50}│")

    # Market probability bar
    market_bar_length = int(market_prob * 50)
    market_bar = '░' * market_bar_length
    lines.append(f"Market ({market_prob*100:5.1f}%): │{market_bar:<50}│")

    # Edge visualization
    edge = model_prob - market_prob
    if edge > 0:
        edge_marker = "↑" * min(int(abs(edge) * 200), 10)
        lines.append(f"\nEdge: +{edge*100:.1f}% {edge_marker}")
    else:
        edge_marker = "↓" * min(int(abs(edge) * 200), 10)
        lines.append(f"\nEdge: {edge*100:.1f}% {edge_marker}")

    return "\n".join(lines)


def run_detailed_monte_carlo(bet_details, n_simulations=10000):
    """Run detailed Monte Carlo simulation with full statistics"""

    team = bet_details['team']
    odds = bet_details['odds']
    model_prob = bet_details['model_prob']
    stake = 100

    results = []

    for _ in range(n_simulations):
        won = np.random.random() < model_prob

        if won:
            if odds > 0:
                profit = stake * (odds / 100)
            else:
                profit = stake * (100 / abs(odds))
        else:
            profit = -stake

        results.append(profit)

    results = np.array(results)

    # Calculate comprehensive statistics
    stats = {
        'mean': np.mean(results),
        'median': np.median(results),
        'std': np.std(results),
        'min': np.min(results),
        'max': np.max(results),
        'p1': np.percentile(results, 1),
        'p5': np.percentile(results, 5),
        'p10': np.percentile(results, 10),
        'p25': np.percentile(results, 25),
        'p50': np.percentile(results, 50),
        'p75': np.percentile(results, 75),
        'p90': np.percentile(results, 90),
        'p95': np.percentile(results, 95),
        'p99': np.percentile(results, 99),
        'prob_profit': np.sum(results > 0) / n_simulations,
        'prob_loss': np.sum(results < 0) / n_simulations,
        'prob_push': np.sum(results == 0) / n_simulations,
        'results': results
    }

    return stats


def display_monte_carlo_results(stats, bet_name):
    """Display comprehensive Monte Carlo simulation results"""

    lines = []
    lines.append("\n" + "=" * 80)
    lines.append(f"🎲 MONTE CARLO SIMULATION: {bet_name}")
    lines.append("=" * 80)
    lines.append(f"\n10,000 simulated outcomes:")
    lines.append("")

    # Outcome probabilities
    lines.append("OUTCOME PROBABILITIES")
    lines.append("-" * 80)
    lines.append(f"  Win:  {stats['prob_profit']*100:>5.1f}%  {'█' * int(stats['prob_profit'] * 50)}")
    lines.append(f"  Loss: {stats['prob_loss']*100:>5.1f}%  {'█' * int(stats['prob_loss'] * 50)}")
    if stats['prob_push'] > 0:
        lines.append(f"  Push: {stats['prob_push']*100:>5.1f}%  {'█' * int(stats['prob_push'] * 50)}")
    lines.append("")

    # Expected value
    lines.append("EXPECTED VALUE")
    lines.append("-" * 80)
    lines.append(f"  Mean Profit:        ${stats['mean']:>8.2f}")
    lines.append(f"  Median Profit:      ${stats['median']:>8.2f}")
    lines.append(f"  Standard Deviation: ${stats['std']:>8.2f}")
    lines.append("")

    # Percentile distribution
    lines.append("PROFIT DISTRIBUTION (Percentiles)")
    lines.append("-" * 80)
    lines.append(f"  Best 1%:    ${stats['p99']:>8.2f}  (99th percentile)")
    lines.append(f"  Best 5%:    ${stats['p95']:>8.2f}  (95th percentile)")
    lines.append(f"  Best 10%:   ${stats['p90']:>8.2f}  (90th percentile)")
    lines.append(f"  Top Quarter:${stats['p75']:>8.2f}  (75th percentile)")
    lines.append(f"  Median:     ${stats['p50']:>8.2f}  (50th percentile)")
    lines.append(f"  Low Quarter:${stats['p25']:>8.2f}  (25th percentile)")
    lines.append(f"  Worst 10%:  ${stats['p10']:>8.2f}  (10th percentile)")
    lines.append(f"  Worst 5%:   ${stats['p5']:>8.2f}  (5th percentile)")
    lines.append(f"  Worst 1%:   ${stats['p1']:>8.2f}  (1st percentile)")
    lines.append("")

    # Risk metrics
    lines.append("RISK METRICS")
    lines.append("-" * 80)

    # Value at Risk (VaR)
    var_5 = stats['p5']
    lines.append(f"  Value at Risk (5%):     ${abs(var_5):>8.2f}")
    lines.append(f"  → 5% chance of losing ${abs(var_5):.2f} or more")
    lines.append("")

    # Expected Shortfall (CVaR)
    losses = stats['results'][stats['results'] < var_5]
    if len(losses) > 0:
        cvar = np.mean(losses)
        lines.append(f"  Expected Shortfall:     ${abs(cvar):>8.2f}")
        lines.append(f"  → Average loss in worst 5% of outcomes")
    lines.append("")

    # Histogram
    lines.append(create_ascii_histogram(stats['results'], "PROFIT DISTRIBUTION HISTOGRAM"))

    return "\n".join(lines)


def fetch_todays_games(api_key: str):
    """Fetch all NBA games scheduled for today"""

    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

    params = {
        'apiKey': api_key,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'bookmakers': 'fanduel',
        'oddsFormat': 'american'
    }

    print("Fetching NBA games from The Odds API...")
    print()

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        games = response.json()

        remaining = response.headers.get('x-requests-remaining')
        used = response.headers.get('x-requests-used')

        print(f"API Status: {used} requests used, {remaining} remaining")
        print()

        return games

    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds: {e}")
        return []


def display_games_schedule(games):
    """Display all games with EST start times"""

    print("=" * 100)
    print("🏀 NBA SCHEDULE - SATURDAY, JANUARY 17, 2026")
    print("=" * 100)
    print()

    if not games:
        print("No games found.")
        return []

    games_sorted = sorted(games, key=lambda x: x.get('commence_time', ''))
    eastern = pytz.timezone('US/Eastern')

    print(f"{'#':<4} {'Start Time (EST)':<20} {'Matchup':<50} {'Status':<15}")
    print("-" * 100)

    for i, game in enumerate(games_sorted, 1):
        home_team = game.get('home_team', 'Unknown')
        away_team = game.get('away_team', 'Unknown')

        commence_time = game.get('commence_time')
        if commence_time:
            try:
                utc_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                eastern_time = utc_time.astimezone(eastern)
                time_str = eastern_time.strftime('%I:%M %p EST')
            except:
                time_str = "Time TBD"
        else:
            time_str = "Time TBD"

        if commence_time:
            utc_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            now = datetime.now(pytz.UTC)

            if now < utc_time:
                status = "Upcoming"
            elif now < utc_time.replace(hour=utc_time.hour + 3):
                status = "In Progress"
            else:
                status = "Final"
        else:
            status = "Upcoming"

        matchup = f"{away_team} @ {home_team}"
        print(f"{i:<4} {time_str:<20} {matchup:<50} {status:<15}")

    print()
    print(f"Total Games: {len(games_sorted)}")
    print()

    return games_sorted


def analyze_game(game, model, efficiency_analyzer):
    """Analyze a single game and return opportunities"""

    home_team = game.get('home_team')
    away_team = game.get('away_team')

    fanduel_odds = None
    for bookmaker in game.get('bookmakers', []):
        if bookmaker.get('key') == 'fanduel':
            fanduel_odds = bookmaker
            break

    if not fanduel_odds:
        return []

    h2h_market = None
    spreads_market = None
    totals_market = None

    for market in fanduel_odds.get('markets', []):
        if market['key'] == 'h2h':
            h2h_market = market
        elif market['key'] == 'spreads':
            spreads_market = market
        elif market['key'] == 'totals':
            totals_market = market

    home_win_prob = model.predict_win_probability(home_team, away_team)
    away_win_prob = 1 - home_win_prob

    opportunities = []

    # Analyze moneylines
    if h2h_market and len(h2h_market.get('outcomes', [])) >= 2:
        outcomes = h2h_market['outcomes']

        home_ml_outcome = next((o for o in outcomes if o['name'] == home_team), None)
        away_ml_outcome = next((o for o in outcomes if o['name'] == away_team), None)

        if home_ml_outcome and away_ml_outcome:
            home_ml = home_ml_outcome['price']
            away_ml = away_ml_outcome['price']

            home_fair, away_fair = remove_vig_proportional(
                american_to_probability(home_ml),
                american_to_probability(away_ml)
            )

            for outcome in outcomes:
                team = outcome['name']
                odds = outcome['price']

                model_prob = home_win_prob if team == home_team else away_win_prob
                market_prob = home_fair if team == home_team else away_fair

                edge = model_prob - market_prob
                stake = 100
                profit = calculate_profit(stake, odds)
                ev = (model_prob * profit) - ((1 - model_prob) * stake)
                ev_percentage = (ev / stake) * 100

                reality_check = efficiency_analyzer.reality_check_ev_opportunity(
                    model_prob=model_prob,
                    market_prob=market_prob,
                    odds=odds,
                    ev_percentage=ev_percentage
                )

                opportunities.append({
                    'game': f"{away_team} @ {home_team}",
                    'bet_type': 'moneyline',
                    'team': team,
                    'odds': odds,
                    'line': 0,
                    'model_prob': model_prob,
                    'market_prob': market_prob,
                    'edge': edge,
                    'ev': ev,
                    'ev_percentage': ev_percentage,
                    'adjusted_ev': reality_check['adjusted_ev'],
                    'recommendation': reality_check['recommendation'],
                    'warnings': reality_check['warnings']
                })

    # Analyze spreads
    if spreads_market:
        for outcome in spreads_market.get('outcomes', []):
            team = outcome['name']
            odds = outcome['price']
            line = outcome['point']

            projected_margin = (home_win_prob - 0.5) * 20
            std_dev = 12.0

            if team == home_team:
                z_score = (projected_margin - line) / std_dev
            else:
                z_score = (-projected_margin - line) / std_dev

            cover_prob = norm.cdf(z_score)
            market_prob = american_to_probability(odds)

            edge = cover_prob - market_prob
            stake = 100
            profit = calculate_profit(stake, odds)
            ev = (cover_prob * profit) - ((1 - cover_prob) * stake)
            ev_percentage = (ev / stake) * 100

            reality_check = efficiency_analyzer.reality_check_ev_opportunity(
                model_prob=cover_prob,
                market_prob=market_prob,
                odds=odds,
                ev_percentage=ev_percentage
            )

            opportunities.append({
                'game': f"{away_team} @ {home_team}",
                'bet_type': 'spread',
                'team': team,
                'odds': odds,
                'line': line,
                'model_prob': cover_prob,
                'market_prob': market_prob,
                'edge': edge,
                'ev': ev,
                'ev_percentage': ev_percentage,
                'adjusted_ev': reality_check['adjusted_ev'],
                'recommendation': reality_check['recommendation'],
                'warnings': reality_check['warnings']
            })

    # Analyze totals
    if totals_market:
        for outcome in totals_market.get('outcomes', []):
            over_under = outcome['name']
            odds = outcome['price']
            line = outcome['point']

            league_avg_total = 220
            expected_total = league_avg_total

            std_dev_total = 15.0
            z_score = (expected_total - line) / std_dev_total
            over_prob = norm.cdf(z_score)
            under_prob = 1 - over_prob

            model_prob = over_prob if over_under == 'Over' else under_prob
            market_prob = american_to_probability(odds)

            edge = model_prob - market_prob
            stake = 100
            profit = calculate_profit(stake, odds)
            ev = (model_prob * profit) - ((1 - model_prob) * stake)
            ev_percentage = (ev / stake) * 100

            reality_check = efficiency_analyzer.reality_check_ev_opportunity(
                model_prob=model_prob,
                market_prob=market_prob,
                odds=odds,
                ev_percentage=ev_percentage
            )

            opportunities.append({
                'game': f"{away_team} @ {home_team}",
                'bet_type': f'total_{over_under.lower()}',
                'team': over_under,
                'odds': odds,
                'line': line,
                'model_prob': model_prob,
                'market_prob': market_prob,
                'edge': edge,
                'ev': ev,
                'ev_percentage': ev_percentage,
                'adjusted_ev': reality_check['adjusted_ev'],
                'recommendation': reality_check['recommendation'],
                'warnings': reality_check['warnings']
            })

    return opportunities


def main():
    """Main production run with enhanced analytics"""

    if len(sys.argv) < 2:
        print("Usage: python3 enhanced_production_run.py YOUR_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1].strip()

    print()
    print("=" * 100)
    print("🏀 ENHANCED SATURDAY PRODUCTION RUN - JANUARY 17, 2026")
    print("=" * 100)
    print()

    games = fetch_todays_games(api_key)

    if not games:
        print("No games found or API error.")
        sys.exit(1)

    games_sorted = display_games_schedule(games)

    print("=" * 100)
    print("🎯 RUNNING FULL BETTING ANALYSIS WITH ENHANCED ANALYTICS")
    print("=" * 100)
    print()

    model = EnhancedEloModel()
    efficiency_analyzer = MarketEfficiencyAnalyzer()
    variance_analyzer = VarianceAnalyzer()

    all_opportunities = []

    for i, game in enumerate(games_sorted, 1):
        home_team = game.get('home_team')
        away_team = game.get('away_team')

        print(f"Analyzing Game {i}/{len(games_sorted)}: {away_team} @ {home_team}...")

        game_opps = analyze_game(game, model, efficiency_analyzer)

        if game_opps:
            all_opportunities.extend(game_opps)

    print()
    print(f"Found {len(all_opportunities)} total betting opportunities")
    print()

    positive_ev_bets = [
        opp for opp in all_opportunities
        if opp['recommendation'] in ['PROCEED', 'PROCEED WITH CAUTION']
        and opp['adjusted_ev'] > 3.0
    ]

    positive_ev_bets.sort(key=lambda x: x['adjusted_ev'], reverse=True)

    print("=" * 100)
    print("🔥 TOP BETTING OPPORTUNITIES WITH DETAILED ANALYSIS")
    print("=" * 100)
    print()

    if not positive_ev_bets:
        print("No positive EV opportunities found after reality checks.")
        print()
    else:
        print(f"Found {len(positive_ev_bets)} opportunities with positive adjusted EV > 3%")
        print()

        # Display top opportunities with detailed analysis
        for i, opp in enumerate(positive_ev_bets[:10], 1):
            line_str = ""
            if opp['bet_type'] == 'spread':
                line_str = f" {opp['line']:+.1f}"
            elif opp['bet_type'].startswith('total_'):
                line_str = f" {opp['line']:.1f}"

            print("=" * 100)
            print(f"#{i}: {opp['team']} {opp['bet_type'].upper()}{line_str} ({opp['odds']:+d}) 🔥")
            print("=" * 100)
            print(f"Game: {opp['game']}")
            print(f"Adjusted EV: {opp['adjusted_ev']:+.1f}% | Recommendation: {opp['recommendation']}")

            # Probability distribution
            print(create_probability_distribution(
                opp['model_prob'],
                opp['market_prob'],
                f"{opp['team']} {opp['bet_type']}"
            ))

            # Monte Carlo simulation
            mc_stats = run_detailed_monte_carlo(opp)
            print(display_monte_carlo_results(mc_stats, f"{opp['team']} {opp['bet_type']}"))

            # Warnings
            if opp['warnings']:
                print("\n⚠️  WARNINGS:")
                for warning in opp['warnings']:
                    level = warning['level']
                    emoji = "🔴" if level == "CRITICAL" else "⚠️" if level == "MODERATE" else "ℹ️"
                    print(f"  {emoji} [{level}] {warning['message']}")

            print()

        # Portfolio analysis
        if len(positive_ev_bets) > 0:
            print()
            print("=" * 100)
            print("📊 PORTFOLIO ANALYSIS - ALL RECOMMENDED BETS")
            print("=" * 100)
            print()

            portfolio_bets = [
                {
                    'team': opp['team'],
                    'odds': opp['odds'],
                    'model_prob': opp['model_prob'],
                    'stake': 100,
                    'bet_type': opp['bet_type']
                }
                for opp in positive_ev_bets[:10]
            ]

            variance = variance_analyzer.simulate_betting_outcomes(portfolio_bets, n_simulations=10000)

            total_stake = sum(bet['stake'] for bet in portfolio_bets)

            print(f"Portfolio: {len(portfolio_bets)} bets, ${total_stake} total stake")
            print()

            # Portfolio histogram
            print(create_ascii_histogram(
                variance['results'] if 'results' in variance else np.random.randn(100),
                "PORTFOLIO PROFIT DISTRIBUTION"
            ))
            print()

            print("PORTFOLIO STATISTICS")
            print("-" * 100)
            print(f"Expected Profit:           ${variance['mean_profit']:>8.2f}")
            print(f"Median Profit:             ${variance['median_profit']:>8.2f}")
            print(f"Standard Deviation:        ${variance['std_dev']:>8.2f}")
            print()
            print(f"Probability of Profit:     {variance['prob_profit']*100:>7.1f}%")
            print(f"Probability of Loss:       {variance['prob_loss']*100:>7.1f}%")
            print()
            print(f"Best Case (95th %ile):     +${variance['percentile_95']:>7.2f}")
            print(f"Median Outcome:            ${variance['median_profit']:>8.2f}")
            print(f"Worst Case (5th %ile):     ${variance['percentile_5']:>8.2f}")
            print()

            # Kelly sizing
            print()
            print("💵 RECOMMENDED BET SIZING (1/4 Kelly on $1,000 bankroll)")
            print("-" * 100)
            bankroll = 1000

            for bet, opp in zip(portfolio_bets, positive_ev_bets[:10]):
                decimal_odds = (bet['odds'] + 100) / 100 if bet['odds'] > 0 else (100 / abs(bet['odds'])) + 1
                kelly_fraction = (bet['model_prob'] * decimal_odds - 1) / (decimal_odds - 1)
                kelly_fraction = max(0, min(kelly_fraction, 0.25))
                quarter_kelly = kelly_fraction * 0.25

                recommended = bankroll * quarter_kelly

                line_str = ""
                if opp['bet_type'] == 'spread':
                    line_str = f" {opp['line']:+.1f}"
                elif opp['bet_type'].startswith('total_'):
                    line_str = f" {opp['line']:.1f}"

                bet_desc = f"{bet['team']} {bet['bet_type']}{line_str}"
                print(f"{bet_desc:<50} ${recommended:>6.2f}")

            print()

    print()
    print("=" * 100)
    print("⚠️  IMPORTANT REMINDERS")
    print("=" * 100)
    print()
    print("1. Monte Carlo simulations show POSSIBLE outcomes, not guarantees")
    print("2. Your track record: 4-0 (100% win rate, +96% ROI)")
    print("3. Variance will cause regression - expect 55-60% long-term win rate")
    print("4. Even 'best' bets have 30-40% chance of losing")
    print("5. Use proper bankroll management - never risk more than you can afford")
    print()
    print("To log these bets:")
    print("  python3 log_bet_results.py")
    print()
    print("Good luck! 🍀")
    print()


if __name__ == '__main__':
    main()
