#!/usr/bin/env python3
"""
Production Quarter-by-Quarter Live Betting Analysis
Analyzes multiple live quarter betting opportunities simultaneously
"""

import sys
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add project to path
sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from odds.fanduel_odds_utils import american_to_probability, calculate_profit
from odds.vig_removal import remove_vig_proportional
from evaluation.market_efficiency import MarketEfficiencyAnalyzer
from evaluation.variance_analyzer import VarianceAnalyzer


@dataclass
class QuarterBet:
    """Represents a quarter betting line"""
    team: str
    bet_type: str  # 'spread', 'moneyline', 'total_over', 'total_under'
    odds: int
    line: float = 0  # For spread/total


@dataclass
class LiveGameState:
    """Current state of a live game in a specific quarter"""
    home_team: str
    away_team: str
    quarter: int  # 1, 2, 3, 4
    time_remaining_minutes: float
    current_score_home: int
    current_score_away: int
    home_fouls: int
    away_fouls: int
    # Betting lines
    home_spread: QuarterBet
    away_spread: QuarterBet
    home_ml: QuarterBet
    away_ml: QuarterBet
    over: QuarterBet
    under: QuarterBet


class ProductionQuarterAnalyzer:
    """Production-grade analyzer for live quarter betting"""

    def __init__(self):
        self.efficiency_analyzer = MarketEfficiencyAnalyzer()
        self.variance_analyzer = VarianceAnalyzer()

    def estimate_quarter_probabilities(self, game: LiveGameState) -> Dict[str, float]:
        """
        Estimate probabilities for quarter outcomes based on current game state

        Methodology:
        - Blend current pace with historical averages
        - Weight changes based on time elapsed in quarter
        - Account for foul trouble and current momentum
        """
        total_quarter_minutes = 12.0
        elapsed = total_quarter_minutes - game.time_remaining_minutes
        remaining_pct = game.time_remaining_minutes / total_quarter_minutes

        # Current point differential
        current_diff = game.current_score_home - game.current_score_away

        # Historical quarter averages by quarter number
        # Q1/Q3 typically highest scoring (fresh legs), Q2/Q4 slightly lower
        historical_avg_by_quarter = {
            1: 27.0,  # ~27 points per team
            2: 26.5,  # Slightly lower (end of first half fatigue)
            3: 27.5,  # Highest (halftime adjustments, fresh)
            4: 27.0   # Similar to Q1
        }

        historical_q_avg_per_team = historical_avg_by_quarter.get(game.quarter, 27.0)
        historical_q_total = historical_q_avg_per_team * 2

        # Current total in quarter
        current_total = game.current_score_home + game.current_score_away

        # For halftime (0:00 remaining), use pure historical
        if game.time_remaining_minutes == 0:
            pace_weight = 0.0
            historical_weight = 1.0
        else:
            # Weight current pace vs historical (early in quarter = trust historical more)
            pace_weight = min(0.6, elapsed / total_quarter_minutes)  # Max 60% weight to current pace
            historical_weight = 1 - pace_weight

        # Calculate blended expected total for the quarter
        if elapsed > 0:
            current_projected_total = (current_total / elapsed) * total_quarter_minutes
        else:
            current_projected_total = historical_q_total

        blended_expected_total = (pace_weight * current_projected_total) + (historical_weight * historical_q_total)

        # Expected remaining points (split equally between teams as baseline)
        expected_remaining_total = max(0, blended_expected_total - current_total)
        expected_remaining_per_team = expected_remaining_total / 2

        # Project final quarter scores
        projected_home_total = game.current_score_home + expected_remaining_per_team
        projected_away_total = game.current_score_away + expected_remaining_per_team

        # Adjust for foul trouble (more fouls = defensive disadvantage)
        foul_diff = game.home_fouls - game.away_fouls
        foul_adjustment_per_foul = 0.4  # Each foul difference worth ~0.4 points in a quarter
        foul_adjustment = foul_diff * foul_adjustment_per_foul

        projected_home_total += foul_adjustment
        projected_away_total -= foul_adjustment

        # Adjust for current momentum (if one team is on a run)
        # If current pace significantly differs from historical, adjust projections
        if elapsed > 3:  # Need some data
            current_pace_per_minute = current_total / elapsed
            historical_pace_per_minute = historical_q_total / total_quarter_minutes

            # If current pace is much higher/lower, adjust remaining expectations
            pace_diff_factor = current_pace_per_minute / historical_pace_per_minute
            if pace_diff_factor > 1.2 or pace_diff_factor < 0.8:
                # Significant pace difference - weight it more
                momentum_adjustment = (current_projected_total - historical_q_total) * 0.2
                projected_home_total += momentum_adjustment / 2
                projected_away_total += momentum_adjustment / 2

        # Calculate win probability using logistic model
        # Based on projected point differential at end of quarter
        projected_diff = projected_home_total - projected_away_total

        # Logistic regression: P(home wins quarter) = 1 / (1 + e^(-k * projected_diff))
        # k = 0.18 for quarter betting (less certainty than full game due to variance)
        k = 0.18
        home_win_prob = 1 / (1 + np.exp(-k * projected_diff))
        away_win_prob = 1 - home_win_prob

        # Expected total points in quarter
        expected_total = projected_home_total + projected_away_total

        # Calculate over/under probabilities using the betting line
        over_line = game.over.line
        over_prob = self._estimate_total_probability(
            current_total, expected_total, over_line, game.time_remaining_minutes
        )

        return {
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'expected_total': expected_total,
            'over_prob': over_prob,
            'under_prob': 1 - over_prob,
            'projected_home_score': projected_home_total,
            'projected_away_score': projected_away_total,
            'projected_spread': projected_diff
        }

    def _estimate_total_probability(self, current_total: float, expected_total: float,
                                    line: float, time_remaining_minutes: float) -> float:
        """Estimate probability of going OVER the total"""

        # Calculate how many more points needed for over
        points_needed_for_over = line - current_total
        remaining_pct = time_remaining_minutes / 12.0
        expected_remaining = expected_total - current_total

        # Use normal distribution to estimate probability
        # Standard deviation for quarter scoring varies by time remaining
        # Full quarter: ~6 points total, scales down with time
        std_dev = 6.0 * np.sqrt(remaining_pct)

        # Minimum std dev even with little time left (last-second variance)
        std_dev = max(std_dev, 2.0)

        # Z-score: (expected - threshold) / std_dev
        if std_dev > 0:
            z_score = (expected_remaining - points_needed_for_over) / std_dev

            # Convert to probability using cumulative normal distribution
            from scipy.stats import norm
            over_prob = norm.cdf(z_score)
        else:
            # No time left
            over_prob = 1.0 if current_total > line else 0.0

        return over_prob

    def analyze_opportunity(self, bet: QuarterBet, model_prob: float) -> Dict:
        """Analyze a specific betting opportunity"""

        # Calculate market probability
        market_prob = american_to_probability(bet.odds)

        # Calculate EV
        stake = 100
        profit = calculate_profit(stake, bet.odds)
        ev = (model_prob * profit) - ((1 - model_prob) * stake)
        ev_percentage = (ev / stake) * 100

        # Apply reality check
        reality_check = self.efficiency_analyzer.reality_check_ev_opportunity(
            model_prob=model_prob,
            market_prob=market_prob,
            odds=bet.odds,
            ev_percentage=ev_percentage
        )

        return {
            'bet_type': bet.bet_type,
            'team': bet.team,
            'odds': bet.odds,
            'line': bet.line,
            'model_prob': model_prob,
            'market_prob': market_prob,
            'ev': ev,
            'ev_percentage': ev_percentage,
            'adjusted_ev': reality_check['adjusted_ev'],
            'recommendation': reality_check['recommendation'],
            'warnings': reality_check['warnings']
        }

    def analyze_spread_opportunity(self, team: str, spread_bet: QuarterBet,
                                   projected_spread: float) -> Dict:
        """Analyze spread betting opportunity"""

        # For spread betting, calculate probability of covering
        # If home team spread is -4.5, they need to win by 5+
        # projected_spread is home_score - away_score

        # Determine if this is home or away team bet
        # and what spread they need to cover

        # The spread line represents what the team needs to do
        # E.g., Kings +4.5 means they can lose by up to 4 and still win bet
        # Wizards -4.5 means they need to win by 5+

        # For home team with negative spread (favorite)
        # P(cover) = P(win by more than |spread|)

        # For away team with positive spread (underdog)
        # P(cover) = P(lose by less than spread OR win)

        # Use normal distribution around projected spread
        std_dev = 4.5  # Standard deviation for quarter spreads

        # Calculate probability based on which side of spread
        from scipy.stats import norm

        # The bet wins if: actual_spread > line (for underdog getting points)
        # or actual_spread < line (for favorite giving points)

        # Standardize: need to beat the line
        z_score = (projected_spread - spread_bet.line) / std_dev

        # If spread_bet.line is negative (favorite), we need projected > line
        # If spread_bet.line is positive (underdog), we need projected > line (which is negative)
        cover_prob = norm.cdf(z_score)

        return self.analyze_opportunity(spread_bet, cover_prob)

    def analyze_game(self, game: LiveGameState) -> Dict:
        """Analyze all betting opportunities for a live game"""

        # Get model projections
        probs = self.estimate_quarter_probabilities(game)

        # Analyze each bet type
        opportunities = []

        # Moneylines
        home_ml_analysis = self.analyze_opportunity(game.home_ml, probs['home_win_prob'])
        away_ml_analysis = self.analyze_opportunity(game.away_ml, probs['away_win_prob'])
        opportunities.extend([home_ml_analysis, away_ml_analysis])

        # Spreads
        home_spread_analysis = self.analyze_spread_opportunity(
            game.home_team, game.home_spread, probs['projected_spread']
        )
        away_spread_analysis = self.analyze_spread_opportunity(
            game.away_team, game.away_spread, probs['projected_spread']
        )
        opportunities.extend([home_spread_analysis, away_spread_analysis])

        # Totals
        over_analysis = self.analyze_opportunity(game.over, probs['over_prob'])
        under_analysis = self.analyze_opportunity(game.under, probs['under_prob'])
        opportunities.extend([over_analysis, under_analysis])

        # Sort by adjusted EV
        opportunities.sort(key=lambda x: x['adjusted_ev'], reverse=True)

        return {
            'game': f"{game.away_team} @ {game.home_team}",
            'quarter': game.quarter,
            'time_remaining': game.time_remaining_minutes,
            'current_score': f"{game.away_team} {game.current_score_away}, {game.home_team} {game.current_score_home}",
            'projections': probs,
            'opportunities': opportunities
        }


def print_game_analysis(analysis: Dict, game_num: int, total_games: int):
    """Print formatted analysis for a single game"""

    print("=" * 80)
    print(f"GAME {game_num}/{total_games}: {analysis['game']} - Q{analysis['quarter']}")
    print("=" * 80)
    print()

    print("📊 CURRENT STATE")
    print("-" * 80)
    print(f"Score: {analysis['current_score']}")
    print(f"Time Remaining: {analysis['time_remaining']:.1f} minutes")
    print()

    probs = analysis['projections']
    print("🧮 MODEL PROJECTIONS")
    print("-" * 80)
    home_team = analysis['game'].split('@')[1].strip()
    away_team = analysis['game'].split('@')[0].strip()
    print(f"Projected Q{analysis['quarter']} Final: {away_team} {probs['projected_away_score']:.1f}, {home_team} {probs['projected_home_score']:.1f}")
    print(f"Expected Total: {probs['expected_total']:.1f} points")
    print(f"Projected Spread: {probs['projected_spread']:+.1f} (positive = home favored)")
    print()
    print(f"{home_team} Win Q{analysis['quarter']}: {probs['home_win_prob']*100:.1f}%")
    print(f"{away_team} Win Q{analysis['quarter']}: {probs['away_win_prob']*100:.1f}%")
    print()

    print("🎯 BETTING OPPORTUNITIES (Ranked by Adjusted EV)")
    print("=" * 80)
    print()

    positive_ev_bets = []
    for i, opp in enumerate(analysis['opportunities'], 1):
        line_str = f" {opp['line']:+.1f}" if opp['bet_type'] in ['spread'] else ""

        print(f"#{i}. {opp['team']} - {opp['bet_type'].upper()}{line_str} ({opp['odds']:+d})")
        print(f"    Model Probability: {opp['model_prob']*100:.1f}%")
        print(f"    Market Probability: {opp['market_prob']*100:.1f}%")
        print(f"    Edge: {(opp['model_prob'] - opp['market_prob'])*100:+.1f}%")
        print(f"    Raw EV: {opp['ev_percentage']:+.1f}%")
        print(f"    Adjusted EV: {opp['adjusted_ev']:+.1f}%")
        print(f"    📋 Recommendation: {opp['recommendation']}")

        if opp['warnings']:
            for warning in opp['warnings']:
                level = warning['level']
                emoji = "🔴" if level == "CRITICAL" else "⚠️" if level == "MODERATE" else "ℹ️"
                print(f"    {emoji} [{level}] {warning['message']}")

        print()

        # Track positive EV bets for portfolio analysis
        if opp['recommendation'] in ['PROCEED', 'PROCEED WITH CAUTION'] and opp['adjusted_ev'] > 3:
            positive_ev_bets.append({
                'team': opp['team'],
                'odds': opp['odds'],
                'model_prob': opp['model_prob'],
                'stake': 100,
                'bet_type': opp['bet_type']
            })

    return positive_ev_bets


def main():
    """Run production analysis on live quarter betting opportunities"""

    print()
    print("=" * 80)
    print("🏀 NBA LIVE QUARTER BETTING - PRODUCTION ANALYSIS")
    print("=" * 80)
    print()

    analyzer = ProductionQuarterAnalyzer()

    # Define the two live game scenarios from screenshots

    # Game 1: Wizards @ Kings - 2nd Quarter
    game1 = LiveGameState(
        home_team="Kings",
        away_team="Wizards",
        quarter=2,
        time_remaining_minutes=6.45,  # 6:27
        current_score_home=50,
        current_score_away=36,
        home_fouls=3,
        away_fouls=3,
        # Lines from screenshot
        home_spread=QuarterBet(team="Kings", bet_type="spread", odds=-122, line=4.5),
        away_spread=QuarterBet(team="Wizards", bet_type="spread", odds=-108, line=-4.5),
        home_ml=QuarterBet(team="Kings", bet_type="moneyline", odds=260),
        away_ml=QuarterBet(team="Wizards", bet_type="moneyline", odds=-370),
        over=QuarterBet(team="Over", bet_type="total_over", odds=100, line=56.5),
        under=QuarterBet(team="Under", bet_type="total_under", odds=-132, line=56.5)
    )

    # Game 2: Timberwolves @ Rockets - 3rd Quarter (Halftime)
    game2 = LiveGameState(
        home_team="Rockets",
        away_team="Timberwolves",
        quarter=3,
        time_remaining_minutes=12.0,  # Halftime - full quarter ahead
        current_score_home=53,
        current_score_away=55,
        home_fouls=0,  # Reset for new quarter
        away_fouls=0,
        # Lines from screenshot
        home_spread=QuarterBet(team="Rockets", bet_type="spread", odds=-128, line=-0.5),
        away_spread=QuarterBet(team="Timberwolves", bet_type="spread", odds=-104, line=0.5),
        home_ml=QuarterBet(team="Rockets", bet_type="moneyline", odds=-138),
        away_ml=QuarterBet(team="Timberwolves", bet_type="moneyline", odds=108),
        over=QuarterBet(team="Over", bet_type="total_over", odds=102, line=57.5),
        under=QuarterBet(team="Under", bet_type="total_under", odds=-136, line=57.5)
    )

    games = [game1, game2]
    all_positive_bets = []

    # Analyze each game
    for i, game in enumerate(games, 1):
        analysis = analyzer.analyze_game(game)
        positive_bets = print_game_analysis(analysis, i, len(games))
        all_positive_bets.extend(positive_bets)
        print()

    # Portfolio analysis if we have multiple positive EV opportunities
    if all_positive_bets:
        print()
        print("=" * 80)
        print("📊 PORTFOLIO ANALYSIS")
        print("=" * 80)
        print()

        variance_analyzer = VarianceAnalyzer()
        variance = variance_analyzer.simulate_betting_outcomes(all_positive_bets, n_simulations=10000)

        total_stake = sum(bet['stake'] for bet in all_positive_bets)

        print(f"Portfolio: {len(all_positive_bets)} opportunities across {len(games)} games")
        print(f"Total Stake: ${total_stake}")
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
        print("💵 RECOMMENDED BET SIZING (1/4 Kelly)")
        print("-" * 80)
        bankroll = 1000
        for bet in all_positive_bets:
            # Calculate Kelly
            decimal_odds = (bet['odds'] + 100) / 100 if bet['odds'] > 0 else (100 / abs(bet['odds'])) + 1
            kelly_fraction = (bet['model_prob'] * decimal_odds - 1) / (decimal_odds - 1)
            kelly_fraction = max(0, kelly_fraction)  # No negative Kelly
            quarter_kelly = kelly_fraction * 0.25

            recommended = bankroll * quarter_kelly

            print(f"{bet['team']} {bet['bet_type']}: ${recommended:.2f} (on ${bankroll} bankroll)")

        print()
    else:
        print()
        print("=" * 80)
        print("❌ NO POSITIVE EV OPPORTUNITIES FOUND")
        print("=" * 80)
        print()
        print("All opportunities failed reality checks or had negative adjusted EV.")
        print("This is common in live quarter betting - markets are extremely efficient.")

    print()
    print("=" * 80)
    print("⚠️  CRITICAL WARNINGS - LIVE QUARTER BETTING")
    print("=" * 80)
    print()
    print("1. EXTREME MARKET EFFICIENCY:")
    print("   - Live quarter markets are among the most efficient in sports betting")
    print("   - Professional algorithms adjust lines in real-time")
    print("   - True edges are extremely rare (< 1-2% of opportunities)")
    print()
    print("2. RAPID LINE MOVEMENT:")
    print("   - These odds were from a screenshot - they've likely already changed")
    print("   - A single basket can move lines by 1-2 points")
    print("   - By the time you place bet, odds may be different")
    print()
    print("3. HIGH VARIANCE:")
    print("   - Quarter betting has extreme variance vs full game")
    print("   - One hot streak can swing entire quarter")
    print("   - Need 500+ bets to see true edge emerge")
    print()
    print("4. INFORMATION DISADVANTAGE:")
    print("   - You're competing against traders watching live feed")
    print("   - They see plays before odds update")
    print("   - This model uses only score/time - limited information")
    print()
    print("5. BANKROLL MANAGEMENT:")
    print("   - Use 1/4 Kelly or smaller")
    print("   - Never bet more than 2-3% of bankroll on single quarter")
    print("   - Losing streaks of 10+ bets are normal")
    print()
    print("Only bet what you can afford to lose. Gambling involves significant risk.")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
