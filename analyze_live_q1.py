#!/usr/bin/env python3
"""
Live First Quarter Betting Analysis
Analyzes in-game first quarter betting opportunities with enhanced modeling
"""

import sys
import numpy as np
from typing import Dict, List, Tuple

# Add project to path
sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from odds.fanduel_odds_utils import american_to_probability, calculate_profit
from odds.vig_removal import remove_vig_proportional
from evaluation.market_efficiency import MarketEfficiencyAnalyzer
from evaluation.variance_analyzer import VarianceAnalyzer


class LiveQ1Analyzer:
    """Analyzes live first quarter betting scenarios"""

    def __init__(self):
        self.efficiency_analyzer = MarketEfficiencyAnalyzer()
        self.variance_analyzer = VarianceAnalyzer()

    def estimate_q1_probabilities(self,
                                   current_score_home: int,
                                   current_score_away: int,
                                   time_remaining_minutes: float,
                                   home_fouls: int,
                                   away_fouls: int) -> Dict[str, float]:
        """
        Estimate probabilities for Q1 outcomes based on current game state

        For first quarter with 9:16 remaining (77% of quarter left):
        - Current score matters significantly
        - Foul trouble impacts rotations
        - Momentum and pace are key factors
        """

        # Calculate time elapsed vs remaining
        total_q1_minutes = 12.0
        elapsed = total_q1_minutes - time_remaining_minutes
        remaining_pct = time_remaining_minutes / total_q1_minutes

        # Current point differential
        point_diff = current_score_home - current_score_away  # SAC 6 - WAS 7 = -1

        # Estimate expected scoring in remaining time
        # NBA Q1 average: ~26-28 points per team
        # Use weighted blend of current pace and historical average

        current_total = current_score_home + current_score_away  # 13 points

        # Historical Q1 average: ~27 points per team = ~54 total
        historical_q1_avg_per_team = 27.0
        historical_q1_total = historical_q1_avg_per_team * 2

        # Weight current pace vs historical (early game = trust historical more)
        pace_weight = min(0.5, elapsed / total_q1_minutes)  # Max 50% weight to current pace
        historical_weight = 1 - pace_weight

        # Calculate blended expected total
        current_projected_total = (current_total / elapsed) * total_q1_minutes if elapsed > 0 else historical_q1_total
        blended_expected_total = (pace_weight * current_projected_total) + (historical_weight * historical_q1_total)

        # Expected remaining points (split equally between teams as baseline)
        expected_remaining_total = blended_expected_total - current_total
        expected_remaining_per_team = expected_remaining_total / 2

        # Project final Q1 score
        projected_home_total = current_score_home + expected_remaining_per_team
        projected_away_total = current_score_away + expected_remaining_per_team

        # Adjust for foul trouble (more fouls = defensive disadvantage)
        foul_diff = home_fouls - away_fouls  # SAC 0 - WAS 3 = -3
        foul_adjustment = foul_diff * 0.3  # Each foul difference worth ~0.3 points

        projected_home_total += foul_adjustment
        projected_away_total -= foul_adjustment

        # Calculate win probability using logistic model
        # Based on projected point differential at end of Q1
        projected_diff = (projected_home_total - foul_adjustment) - (projected_away_total + foul_adjustment)

        # Logistic regression: P(home wins Q1) = 1 / (1 + e^(-k * projected_diff))
        # k = 0.15 for first quarter (less certainty than full game)
        k = 0.15
        home_win_prob = 1 / (1 + np.exp(-k * projected_diff))
        away_win_prob = 1 - home_win_prob

        # For tie probability: quarters rarely end in ties (~8-10% historically)
        # Adjust based on current score closeness
        base_tie_prob = 0.09
        closeness_factor = 1 + abs(point_diff) * -0.02  # Closer = more likely to tie
        tie_prob = max(0.05, min(0.15, base_tie_prob * closeness_factor))

        # Normalize to ensure probabilities sum to 1
        total_prob = home_win_prob + away_win_prob + tie_prob
        home_win_prob /= total_prob
        away_win_prob /= total_prob
        tie_prob /= total_prob

        # Expected total points
        expected_total = projected_home_total + projected_away_total
        over_prob = self._estimate_total_probability(current_total, expected_total, 62.5, time_remaining_minutes)

        return {
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'tie_prob': tie_prob,
            'expected_total': expected_total,
            'over_prob': over_prob,
            'under_prob': 1 - over_prob,
            'projected_home_score': projected_home_total,
            'projected_away_score': projected_away_total
        }

    def _estimate_total_probability(self, current_total: float, expected_total: float,
                                    line: float, time_remaining_minutes: float) -> float:
        """Estimate probability of going OVER the total"""

        # Calculate how many more points needed for over
        points_needed_for_over = line - current_total
        remaining_pct = time_remaining_minutes / 12.0
        expected_remaining = expected_total - current_total

        # Use normal distribution to estimate probability
        # Standard deviation for Q1 scoring: ~4 points per team, ~5.7 total
        std_dev = 5.7 * np.sqrt(remaining_pct)  # Scales with time remaining

        # Z-score: (expected - threshold) / std_dev
        z_score = (expected_remaining - points_needed_for_over) / std_dev

        # Convert to probability using cumulative normal distribution
        from scipy.stats import norm
        over_prob = norm.cdf(z_score)

        return over_prob

    def analyze_opportunity(self,
                           bet_type: str,
                           team: str,
                           odds: int,
                           model_prob: float,
                           market_prob: float) -> Dict:
        """Analyze a specific betting opportunity"""

        # Calculate EV
        stake = 100
        profit = calculate_profit(stake, odds)
        ev = (model_prob * profit) - ((1 - model_prob) * stake)
        ev_percentage = (ev / stake) * 100

        # Apply reality check
        reality_check = self.efficiency_analyzer.reality_check_ev_opportunity(
            model_prob=model_prob,
            market_prob=market_prob,
            odds=odds,
            ev_percentage=ev_percentage
        )

        return {
            'bet_type': bet_type,
            'team': team,
            'odds': odds,
            'model_prob': model_prob,
            'market_prob': market_prob,
            'ev': ev,
            'ev_percentage': ev_percentage,
            'adjusted_ev': reality_check['adjusted_ev'],
            'recommendation': reality_check['recommendation'],
            'warnings': reality_check['warnings']
        }


def main():
    """Run live Q1 analysis on Wizards @ Kings game"""

    print("=" * 80)
    print("🏀 LIVE FIRST QUARTER BETTING ANALYSIS")
    print("=" * 80)
    print()

    # Game state from screenshot
    print("📊 CURRENT GAME STATE")
    print("-" * 80)
    print("Game: Washington Wizards @ Sacramento Kings")
    print("Quarter: 1st Quarter, 9:16 remaining")
    print("Score: WAS 7, SAC 6")
    print("Fouls: WAS 3, SAC 0")
    print()

    analyzer = LiveQ1Analyzer()

    # Estimate probabilities based on current game state
    # Sacramento is home team
    probs = analyzer.estimate_q1_probabilities(
        current_score_home=6,      # SAC score
        current_score_away=7,      # WAS score
        time_remaining_minutes=9.27,  # 9:16
        home_fouls=0,              # SAC fouls
        away_fouls=3               # WAS fouls
    )

    print("🧮 MODEL PROJECTIONS")
    print("-" * 80)
    print(f"Projected Final Q1 Score: WAS {probs['projected_away_score']:.1f}, SAC {probs['projected_home_score']:.1f}")
    print(f"Expected Total: {probs['expected_total']:.1f} points")
    print()
    print(f"Kings Win Q1:  {probs['home_win_prob']*100:.1f}%")
    print(f"Wizards Win Q1: {probs['away_win_prob']*100:.1f}%")
    print(f"Tie Q1:         {probs['tie_prob']*100:.1f}%")
    print(f"Over 62.5:      {probs['over_prob']*100:.1f}%")
    print(f"Under 62.5:     {probs['under_prob']*100:.1f}%")
    print()

    # Market odds from screenshot
    print("💰 MARKET ODDS (FanDuel)")
    print("-" * 80)
    print("1st Quarter Lines:")
    print("  Wizards: +1.5 (-102), ML +140, O 62.5 (-106)")
    print("  Kings:   -1.5 (-130), ML -180, U 62.5 (-125)")
    print()
    print("1st Quarter Winner (3-Way):")
    print("  Wizards: +140")
    print("  Tie:     +1500")
    print("  Kings:   -175")
    print()

    # Extract market probabilities
    wiz_ml_market = american_to_probability(140)
    kings_ml_market = american_to_probability(-180)

    # Remove vig for fair probabilities
    wiz_fair, kings_fair = remove_vig_proportional(wiz_ml_market, kings_ml_market)

    tie_market = american_to_probability(1500)
    over_market = american_to_probability(-106)
    under_market = american_to_probability(-125)

    print("📈 MARKET IMPLIED PROBABILITIES (Vig-Removed)")
    print("-" * 80)
    print(f"Wizards Win Q1: {wiz_fair*100:.1f}% (raw: {wiz_ml_market*100:.1f}%)")
    print(f"Kings Win Q1:   {kings_fair*100:.1f}% (raw: {kings_ml_market*100:.1f}%)")
    print(f"Tie:            {tie_market*100:.1f}%")
    print(f"Over 62.5:      {over_market*100:.1f}%")
    print(f"Under 62.5:     {under_market*100:.1f}%")
    print()

    # Analyze opportunities
    print("🎯 OPPORTUNITY ANALYSIS")
    print("=" * 80)
    print()

    opportunities = []

    # Wizards ML
    wiz_ml_analysis = analyzer.analyze_opportunity(
        bet_type="Moneyline",
        team="Wizards",
        odds=140,
        model_prob=probs['away_win_prob'],
        market_prob=wiz_fair
    )
    opportunities.append(wiz_ml_analysis)

    # Kings ML
    kings_ml_analysis = analyzer.analyze_opportunity(
        bet_type="Moneyline",
        team="Kings",
        odds=-180,
        model_prob=probs['home_win_prob'],
        market_prob=kings_fair
    )
    opportunities.append(kings_ml_analysis)

    # Tie (3-way)
    tie_analysis = analyzer.analyze_opportunity(
        bet_type="3-Way Tie",
        team="Tie",
        odds=1500,
        model_prob=probs['tie_prob'],
        market_prob=tie_market
    )
    opportunities.append(tie_analysis)

    # Over/Under
    over_analysis = analyzer.analyze_opportunity(
        bet_type="Total Over 62.5",
        team="Over",
        odds=-106,
        model_prob=probs['over_prob'],
        market_prob=over_market
    )
    opportunities.append(over_analysis)

    under_analysis = analyzer.analyze_opportunity(
        bet_type="Total Under 62.5",
        team="Under",
        odds=-125,
        model_prob=probs['under_prob'],
        market_prob=under_market
    )
    opportunities.append(under_analysis)

    # Sort by adjusted EV
    opportunities.sort(key=lambda x: x['adjusted_ev'], reverse=True)

    # Display opportunities
    positive_ev_bets = []
    for i, opp in enumerate(opportunities, 1):
        print(f"#{i}. {opp['team']} - {opp['bet_type']} ({opp['odds']:+d})")
        print(f"    Model Probability: {opp['model_prob']*100:.1f}%")
        print(f"    Market Probability: {opp['market_prob']*100:.1f}%")
        print(f"    Edge: {(opp['model_prob'] - opp['market_prob'])*100:+.1f}%")
        print(f"    Raw EV: {opp['ev_percentage']:+.1f}%")
        print(f"    Adjusted EV: {opp['adjusted_ev']:+.1f}%")
        print(f"    Recommendation: {opp['recommendation']}")

        if opp['warnings']:
            for warning in opp['warnings']:
                level = warning['level']
                emoji = "🔴" if level == "CRITICAL" else "⚠️" if level == "MODERATE" else "ℹ️"
                print(f"    {emoji} [{level}] {warning['message']}")

        print()

        if opp['recommendation'] == 'PROCEED' or opp['recommendation'] == 'PROCEED WITH CAUTION':
            positive_ev_bets.append({
                'team': opp['team'],
                'odds': opp['odds'],
                'model_prob': opp['model_prob'],
                'stake': 100,
                'bet_type': opp['bet_type']
            })

    # Variance analysis on recommended bets
    if positive_ev_bets:
        print()
        print("📉 VARIANCE ANALYSIS")
        print("=" * 80)
        print()

        variance_analyzer = VarianceAnalyzer()
        variance = variance_analyzer.simulate_betting_outcomes(positive_ev_bets, n_simulations=10000)

        total_stake = sum(bet['stake'] for bet in positive_ev_bets)

        print(f"Portfolio: {len(positive_ev_bets)} bet(s), ${total_stake} total stake")
        print()
        print(f"Expected Profit: ${variance['mean_profit']:.2f}")
        print(f"Probability of Profit: {variance['prob_profit']*100:.1f}%")
        print(f"Probability of Loss: {(1-variance['prob_profit'])*100:.1f}%")
        print()
        print(f"Best Case (95th percentile): +${variance['percentile_95']:.2f}")
        print(f"Worst Case (5th percentile): ${variance['percentile_5']:.2f}")
        print(f"Standard Deviation: ${variance['std_dev']:.2f}")
        print()

        # Kelly sizing recommendations
        print("💵 KELLY CRITERION SIZING")
        print("-" * 80)
        bankroll = 1000  # Example bankroll
        for bet in positive_ev_bets:
            # Calculate Kelly fraction
            decimal_odds = (bet['odds'] + 100) / 100 if bet['odds'] > 0 else (100 / abs(bet['odds'])) + 1
            kelly_fraction = (bet['model_prob'] * decimal_odds - 1) / (decimal_odds - 1)
            quarter_kelly = kelly_fraction * 0.25

            # Recommended stake
            recommended = bankroll * quarter_kelly

            print(f"{bet['team']} {bet['bet_type']}:")
            print(f"  Full Kelly: {kelly_fraction*100:.1f}% of bankroll = ${bankroll * kelly_fraction:.2f}")
            print(f"  1/4 Kelly (Recommended): {quarter_kelly*100:.1f}% = ${recommended:.2f}")
            print()
    else:
        print("❌ NO POSITIVE EV OPPORTUNITIES FOUND")
        print()
        print("This is expected for live first quarter betting:")
        print("- In-game markets are extremely efficient")
        print("- Bookmakers have live data and adjust quickly")
        print("- First quarter variance is high")
        print("- True edges are rare in live betting")

    print()
    print("=" * 80)
    print("⚠️  CRITICAL DISCLAIMERS")
    print("=" * 80)
    print()
    print("1. LIVE BETTING CHALLENGES:")
    print("   - This analysis assumes game state at screenshot time")
    print("   - Odds and game state change every few seconds")
    print("   - By the time you place bet, situation may be different")
    print()
    print("2. FIRST QUARTER VARIANCE:")
    print("   - Small sample size = extreme variance")
    print("   - Single plays can swing entire quarter")
    print("   - Even 'good' bets lose frequently")
    print()
    print("3. MODEL LIMITATIONS:")
    print("   - No access to live play-by-play data")
    print("   - Cannot account for momentum, lineups, injuries")
    print("   - Simplified projection model")
    print()
    print("4. MARKET EFFICIENCY:")
    print("   - Live NBA markets are 90-95% efficient")
    print("   - Professional bettors and algos dominate")
    print("   - True edges are extremely rare")
    print()
    print("Only bet what you can afford to lose. Gambling involves risk.")
    print()


if __name__ == '__main__':
    main()
