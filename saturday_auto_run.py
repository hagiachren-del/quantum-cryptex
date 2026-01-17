#!/usr/bin/env python3
"""
Saturday Auto-Run - January 17, 2026
Automatically runs full analysis without user prompts
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


def fetch_todays_games(api_key: str):
    """Fetch all NBA games scheduled for today from The Odds API."""

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

        # Check API usage
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
        return

    # Sort games by start time
    games_sorted = sorted(games, key=lambda x: x.get('commence_time', ''))

    # Eastern timezone
    eastern = pytz.timezone('US/Eastern')

    print(f"{'#':<4} {'Start Time (EST)':<20} {'Matchup':<50} {'Status':<15}")
    print("-" * 100)

    for i, game in enumerate(games_sorted, 1):
        home_team = game.get('home_team', 'Unknown')
        away_team = game.get('away_team', 'Unknown')

        # Parse start time
        commence_time = game.get('commence_time')
        if commence_time:
            try:
                # Parse UTC time
                utc_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                # Convert to Eastern
                eastern_time = utc_time.astimezone(eastern)
                time_str = eastern_time.strftime('%I:%M %p EST')
            except:
                time_str = "Time TBD"
        else:
            time_str = "Time TBD"

        # Check if game has started or finished
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

    # Get FanDuel odds
    fanduel_odds = None
    for bookmaker in game.get('bookmakers', []):
        if bookmaker.get('key') == 'fanduel':
            fanduel_odds = bookmaker
            break

    if not fanduel_odds:
        return []

    # Extract markets
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

    # Get model prediction
    home_win_prob = model.predict_win_probability(home_team, away_team)
    away_win_prob = 1 - home_win_prob

    opportunities = []

    # Analyze moneylines
    if h2h_market and len(h2h_market.get('outcomes', [])) >= 2:
        outcomes = h2h_market['outcomes']

        # Get both odds for vig removal
        home_ml_outcome = next((o for o in outcomes if o['name'] == home_team), None)
        away_ml_outcome = next((o for o in outcomes if o['name'] == away_team), None)

        if home_ml_outcome and away_ml_outcome:
            home_ml = home_ml_outcome['price']
            away_ml = away_ml_outcome['price']

            # Remove vig
            home_fair, away_fair = remove_vig_proportional(
                american_to_probability(home_ml),
                american_to_probability(away_ml)
            )

            for outcome in outcomes:
                team = outcome['name']
                odds = outcome['price']

                model_prob = home_win_prob if team == home_team else away_win_prob
                market_prob = home_fair if team == home_team else away_fair

                # Calculate EV
                edge = model_prob - market_prob
                stake = 100
                profit = calculate_profit(stake, odds)
                ev = (model_prob * profit) - ((1 - model_prob) * stake)
                ev_percentage = (ev / stake) * 100

                # Reality check
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

            # For spreads, estimate cover probability
            projected_margin = (home_win_prob - 0.5) * 20  # Rough approximation

            # Standard deviation for NBA spreads ~12 points
            std_dev = 12.0

            if team == home_team:
                # Home team needs to beat the spread (line is negative for favorites)
                z_score = (projected_margin - line) / std_dev
            else:
                # Away team needs to beat the spread (line is positive for underdogs)
                z_score = (-projected_margin - line) / std_dev

            cover_prob = norm.cdf(z_score)

            market_prob = american_to_probability(odds)

            # Calculate EV
            edge = cover_prob - market_prob
            stake = 100
            profit = calculate_profit(stake, odds)
            ev = (cover_prob * profit) - ((1 - cover_prob) * stake)
            ev_percentage = (ev / stake) * 100

            # Reality check
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
            over_under = outcome['name']  # 'Over' or 'Under'
            odds = outcome['price']
            line = outcome['point']

            # Estimate total points
            league_avg_total = 220
            expected_total = league_avg_total

            # Probability of over
            std_dev_total = 15.0
            z_score = (expected_total - line) / std_dev_total
            over_prob = norm.cdf(z_score)
            under_prob = 1 - over_prob

            model_prob = over_prob if over_under == 'Over' else under_prob
            market_prob = american_to_probability(odds)

            # Calculate EV
            edge = model_prob - market_prob
            stake = 100
            profit = calculate_profit(stake, odds)
            ev = (model_prob * profit) - ((1 - model_prob) * stake)
            ev_percentage = (ev / stake) * 100

            # Reality check
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
    """Main production run"""

    if len(sys.argv) < 2:
        print("Usage: python3 saturday_auto_run.py YOUR_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1].strip()

    print()
    print("=" * 100)
    print("🏀 SATURDAY PRODUCTION RUN - JANUARY 17, 2026")
    print("=" * 100)
    print()

    # Fetch games
    games = fetch_todays_games(api_key)

    if not games:
        print("No games found or API error.")
        sys.exit(1)

    # Display schedule
    games_sorted = display_games_schedule(games)

    # Automatically proceed with analysis
    print("=" * 100)
    print("🎯 RUNNING FULL BETTING ANALYSIS")
    print("=" * 100)
    print()

    # Initialize analysis components
    model = EnhancedEloModel()
    efficiency_analyzer = MarketEfficiencyAnalyzer()
    variance_analyzer = VarianceAnalyzer()

    # Analyze all games
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

    # Filter for positive adjusted EV
    positive_ev_bets = [
        opp for opp in all_opportunities
        if opp['recommendation'] in ['PROCEED', 'PROCEED WITH CAUTION']
        and opp['adjusted_ev'] > 3.0  # At least 3% adjusted EV
    ]

    # Sort by adjusted EV
    positive_ev_bets.sort(key=lambda x: x['adjusted_ev'], reverse=True)

    # Display top opportunities
    print("=" * 100)
    print("🔥 TOP BETTING OPPORTUNITIES")
    print("=" * 100)
    print()

    if not positive_ev_bets:
        print("No positive EV opportunities found after reality checks.")
        print()
        print("This is common and expected:")
        print("- NBA betting markets are 85-95% efficient")
        print("- Most apparent edges are false positives")
        print("- Reality checks filter out unrealistic opportunities")
        print()
    else:
        print(f"Found {len(positive_ev_bets)} opportunities with positive adjusted EV > 3%")
        print()

        for i, opp in enumerate(positive_ev_bets[:15], 1):  # Top 15
            line_str = ""
            if opp['bet_type'] == 'spread':
                line_str = f" {opp['line']:+.1f}"
            elif opp['bet_type'].startswith('total_'):
                line_str = f" {opp['line']:.1f}"

            print(f"#{i}: {opp['team']} {opp['bet_type'].upper()}{line_str} ({opp['odds']:+d}) 🔥")
            print(f"    Game: {opp['game']}")
            print(f"    Model Probability: {opp['model_prob']*100:.1f}%")
            print(f"    Market Probability: {opp['market_prob']*100:.1f}%")
            print(f"    Edge: {opp['edge']*100:+.1f}%")
            print(f"    Adjusted EV: {opp['adjusted_ev']:+.1f}%")
            print(f"    Recommendation: {opp['recommendation']}")

            if opp['warnings']:
                for warning in opp['warnings'][:2]:  # Show max 2 warnings
                    level = warning['level']
                    emoji = "⚠️" if level == "MODERATE" else "ℹ️"
                    print(f"    {emoji} {warning['message']}")

            print()

        # Portfolio analysis
        if len(positive_ev_bets) > 0:
            print()
            print("=" * 100)
            print("📊 PORTFOLIO ANALYSIS")
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
                for opp in positive_ev_bets[:10]  # Top 10
            ]

            variance = variance_analyzer.simulate_betting_outcomes(portfolio_bets, n_simulations=10000)

            total_stake = sum(bet['stake'] for bet in portfolio_bets)

            print(f"Portfolio: {len(portfolio_bets)} bets, ${total_stake} total stake")
            print()
            print(f"Expected Profit: ${variance['mean_profit']:.2f}")
            print(f"Probability of Profit: {variance['prob_profit']*100:.1f}%")
            print(f"Probability of Loss: {(1-variance['prob_profit'])*100:.1f}%")
            print()
            print(f"Best Case (95th percentile): +${variance['percentile_95']:.2f}")
            print(f"Median Outcome: ${variance['median_profit']:.2f}")
            print(f"Worst Case (5th percentile): ${variance['percentile_5']:.2f}")
            print(f"Standard Deviation: ${variance['std_dev']:.2f}")
            print()

            # Kelly sizing
            print("💵 RECOMMENDED BET SIZING (1/4 Kelly on $1,000 bankroll)")
            print("-" * 100)
            bankroll = 1000

            for bet in portfolio_bets:
                # Calculate Kelly
                decimal_odds = (bet['odds'] + 100) / 100 if bet['odds'] > 0 else (100 / abs(bet['odds'])) + 1
                kelly_fraction = (bet['model_prob'] * decimal_odds - 1) / (decimal_odds - 1)
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
                quarter_kelly = kelly_fraction * 0.25

                recommended = bankroll * quarter_kelly

                bet_desc = f"{bet['team']} {bet['bet_type']}"
                print(f"{bet_desc:<40} ${recommended:>6.2f}")

            print()

    print()
    print("=" * 100)
    print("⚠️  IMPORTANT REMINDERS")
    print("=" * 100)
    print()
    print("1. These are MODEL PREDICTIONS, not guarantees")
    print("2. Even positive EV bets lose frequently (variance)")
    print("3. Your track record: 4-0 (100% win rate, +96% ROI)")
    print("4. Sample size still small - expect regression toward 55-60% win rate")
    print("5. Never bet more than you can afford to lose")
    print()
    print("To log these bets for tracking:")
    print("  python3 log_bet_results.py")
    print()
    print("Good luck! 🍀")
    print()


if __name__ == '__main__':
    main()
