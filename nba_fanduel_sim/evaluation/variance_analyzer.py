"""
Comprehensive Variance Analysis

Addresses the critical reality that:
- Even +EV bets lose frequently
- Variance dominates short-term results
- Bankroll swings are inevitable
- Psychological pressure from losing streaks
"""

from typing import List, Dict, Tuple
import numpy as np
from scipy import stats
from dataclasses import dataclass


@dataclass
class VarianceMetrics:
    """Comprehensive variance metrics."""
    expected_roi: float
    actual_roi: float
    standard_deviation: float
    sharpe_ratio: float
    max_drawdown: float
    max_winning_streak: int
    max_losing_streak: int
    probability_of_ruin: float
    time_to_ruin_median: int  # bets
    variance_drag: float


class VarianceAnalyzer:
    """
    Analyzes variance and risk for betting strategies.

    Purpose: Set realistic expectations about short-term results.
    """

    def __init__(self):
        """Initialize variance analyzer."""
        pass

    def simulate_betting_outcomes(
        self,
        bets: List[Dict],
        n_simulations: int = 10000
    ) -> Dict[str, any]:
        """
        Monte Carlo simulation of betting outcomes.

        Shows the range of possible results given probabilities and odds.

        Args:
            bets: List of bets with prob, odds, stake
            n_simulations: Number of simulations to run

        Returns:
            Dictionary with simulation results
        """
        results = []

        for _ in range(n_simulations):
            total_profit = 0

            for bet in bets:
                prob = bet.get('model_prob', 0.5)
                odds = bet.get('odds', -110)
                stake = bet.get('stake', 100)

                # Simulate outcome
                won = np.random.random() < prob

                if won:
                    if odds < 0:
                        profit = stake * (100 / abs(odds))
                    else:
                        profit = stake * (odds / 100)
                else:
                    profit = -stake

                total_profit += profit

            results.append(total_profit)

        results = np.array(results)

        # Calculate statistics
        mean_profit = np.mean(results)
        median_profit = np.median(results)
        std_profit = np.std(results)

        # Percentiles
        p5 = np.percentile(results, 5)
        p25 = np.percentile(results, 25)
        p75 = np.percentile(results, 75)
        p95 = np.percentile(results, 95)

        # Probability of profit
        prob_profit = np.sum(results > 0) / n_simulations
        prob_loss = 1 - prob_profit

        # Worst/best cases
        worst_case = np.min(results)
        best_case = np.max(results)

        return {
            'mean_profit': mean_profit,
            'median_profit': median_profit,
            'std_dev': std_profit,
            'percentile_5': p5,
            'percentile_25': p25,
            'percentile_75': p75,
            'percentile_95': p95,
            'prob_profit': prob_profit,
            'prob_loss': prob_loss,
            'worst_case': worst_case,
            'best_case': best_case,
            'coefficient_of_variation': abs(std_profit / mean_profit) if mean_profit != 0 else float('inf')
        }

    def calculate_risk_of_ruin(
        self,
        bankroll: float,
        avg_bet_size: float,
        win_rate: float,
        avg_win_payoff: float,
        avg_loss_payoff: float,
        max_bets: int = 1000
    ) -> Dict[str, any]:
        """
        Calculate probability of going broke.

        Uses gambler's ruin formula adjusted for betting.

        Args:
            bankroll: Starting bankroll
            avg_bet_size: Average bet size
            win_rate: Probability of winning a bet
            avg_win_payoff: Average profit when winning
            avg_loss_payoff: Average loss when losing (positive number)
            max_bets: Maximum number of bets before stopping

        Returns:
            Risk of ruin analysis
        """
        # Calculate edge per bet
        expected_value_per_bet = (win_rate * avg_win_payoff) - ((1 - win_rate) * avg_loss_payoff)
        edge_per_bet = expected_value_per_bet / avg_bet_size

        # Units of bankroll
        units = bankroll / avg_bet_size

        # Simplified risk of ruin (for negative EV or break-even)
        if edge_per_bet <= 0:
            risk_of_ruin = 1.0  # Guaranteed ruin eventually
        else:
            # Kelly criterion suggests max bet size
            kelly_fraction = (win_rate * avg_win_payoff - (1 - win_rate) * avg_loss_payoff) / avg_win_payoff

            # Risk of ruin approximation
            # RoR ≈ ((1-edge) / (1+edge))^units for small edges
            if edge_per_bet < 0.2:
                risk_of_ruin = ((1 - edge_per_bet) / (1 + edge_per_bet)) ** units
            else:
                risk_of_ruin = 0.01  # Very low for large edges

        # Time to ruin (median bets if ruin occurs)
        if risk_of_ruin > 0.5:
            median_bets_to_ruin = units / (2 * abs(edge_per_bet)) if edge_per_bet != 0 else units
        else:
            median_bets_to_ruin = float('inf')

        # Safe bet sizing (to keep RoR < 1%)
        safe_bet_size = bankroll * (kelly_fraction * 0.25)  # Quarter Kelly

        return {
            'risk_of_ruin': risk_of_ruin,
            'bankroll_units': units,
            'edge_per_bet': edge_per_bet,
            'median_bets_to_ruin': median_bets_to_ruin,
            'kelly_fraction': kelly_fraction,
            'safe_bet_size': safe_bet_size,
            'current_risk_level': 'HIGH' if risk_of_ruin > 0.05 else 'MODERATE' if risk_of_ruin > 0.01 else 'LOW'
        }

    def analyze_losing_streaks(
        self,
        win_rate: float,
        num_bets: int = 100
    ) -> Dict[str, any]:
        """
        Analyze expected losing streaks.

        Purpose: Prepare bettors for inevitable cold streaks.

        Args:
            win_rate: Probability of winning each bet
            num_bets: Number of bets to analyze

        Returns:
            Losing streak analysis
        """
        # Expected max losing streak in N bets
        # E[max streak] ≈ log(N) / log(1/loss_rate)
        loss_rate = 1 - win_rate

        if loss_rate > 0:
            expected_max_streak = np.log(num_bets) / np.log(1 / loss_rate)
        else:
            expected_max_streak = 0

        # Probability of specific streak lengths
        streak_probabilities = {}
        for streak_length in [3, 5, 7, 10, 15, 20]:
            # P(lose streak_length in a row)
            prob_streak = loss_rate ** streak_length
            # P(at least one streak of this length in num_bets)
            prob_occurs = 1 - (1 - prob_streak) ** (num_bets - streak_length + 1)
            streak_probabilities[streak_length] = {
                'prob_streak': prob_streak,
                'prob_occurs_in_sample': prob_occurs
            }

        return {
            'win_rate': win_rate,
            'loss_rate': loss_rate,
            'expected_max_streak': expected_max_streak,
            'streak_probabilities': streak_probabilities,
            'warnings': [
                f"With {win_rate*100:.0f}% win rate, expect {expected_max_streak:.0f}-bet losing streak",
                f"A 5-bet losing streak will occur with {streak_probabilities.get(5, {}).get('prob_occurs_in_sample', 0)*100:.0f}% probability",
                "Losing streaks are NORMAL and EXPECTED, even with +EV",
                "Do not increase bet size to 'chase losses'"
            ]
        }

    def calculate_variance_drag(
        self,
        win_rate: float,
        avg_odds: float,
        bet_sizing_method: str = "flat"
    ) -> float:
        """
        Calculate variance drag on returns.

        Variance drag: The difference between arithmetic and geometric mean returns.
        Higher variance = lower compounded growth.

        Args:
            win_rate: Win rate
            avg_odds: Average odds (American format)
            bet_sizing_method: 'flat', 'kelly', 'fractional_kelly'

        Returns:
            Variance drag as percentage
        """
        # Convert odds to returns
        if avg_odds < 0:
            win_return = 100 / abs(avg_odds)
        else:
            win_return = avg_odds / 100

        loss_return = -1.0

        # Calculate arithmetic mean return
        arithmetic_mean = (win_rate * win_return) + ((1 - win_rate) * loss_return)

        # Calculate variance
        variance = (win_rate * (win_return - arithmetic_mean) ** 2 +
                   (1 - win_rate) * (loss_return - arithmetic_mean) ** 2)

        # Variance drag ≈ variance / (2 * (1 + arithmetic_mean)^2)
        variance_drag = variance / (2 * (1 + arithmetic_mean) ** 2) if arithmetic_mean > -1 else 0

        return variance_drag

    def generate_variance_report(
        self,
        bets: List[Dict],
        bankroll: float = 10000,
        num_simulations: int = 10000
    ) -> str:
        """
        Generate comprehensive variance analysis report.

        Args:
            bets: List of proposed bets
            bankroll: Current bankroll
            num_simulations: Monte Carlo simulations

        Returns:
            Formatted report string
        """
        # Run simulations
        sim_results = self.simulate_betting_outcomes(bets, num_simulations)

        # Calculate risk of ruin
        total_stake = sum(b.get('stake', 0) for b in bets)
        avg_stake = total_stake / len(bets) if bets else 0
        avg_prob = np.mean([b.get('model_prob', 0.5) for b in bets])

        # Estimate average payoffs
        avg_win_payoff = 0
        avg_loss_payoff = 0
        for bet in bets:
            odds = bet.get('odds', -110)
            stake = bet.get('stake', 100)
            if odds < 0:
                avg_win_payoff += stake * (100 / abs(odds))
            else:
                avg_win_payoff += stake * (odds / 100)
            avg_loss_payoff += stake

        avg_win_payoff /= len(bets)
        avg_loss_payoff /= len(bets)

        ruin_analysis = self.calculate_risk_of_ruin(
            bankroll=bankroll,
            avg_bet_size=avg_stake,
            win_rate=avg_prob,
            avg_win_payoff=avg_win_payoff,
            avg_loss_payoff=avg_loss_payoff
        )

        # Losing streak analysis
        streak_analysis = self.analyze_losing_streaks(avg_prob, len(bets))

        # Generate report
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE VARIANCE & RISK ANALYSIS")
        report.append("=" * 80)
        report.append("")
        report.append(f"Portfolio: {len(bets)} bets | Bankroll: ${bankroll:,.0f}")
        report.append("")
        report.append("MONTE CARLO SIMULATION RESULTS (10,000 trials)")
        report.append("-" * 80)
        report.append(f"  Expected Profit:       ${sim_results['mean_profit']:,.0f}")
        report.append(f"  Median Profit:         ${sim_results['median_profit']:,.0f}")
        report.append(f"  Standard Deviation:    ${sim_results['std_dev']:,.0f}")
        report.append("")
        report.append("  Outcome Distribution:")
        report.append(f"    Best Case (95%):     ${sim_results['percentile_95']:,.0f}")
        report.append(f"    Upper Quartile (75%):'${sim_results['percentile_75']:,.0f}")
        report.append(f"    Median (50%):        ${sim_results['median_profit']:,.0f}")
        report.append(f"    Lower Quartile (25%):${sim_results['percentile_25']:,.0f}")
        report.append(f"    Worst Case (5%):     ${sim_results['percentile_5']:,.0f}")
        report.append("")
        report.append(f"  Probability of Profit: {sim_results['prob_profit']*100:.1f}%")
        report.append(f"  Probability of Loss:   {sim_results['prob_loss']*100:.1f}%")
        report.append("")
        report.append("⚠️  VARIANCE REALITY CHECK:")
        report.append(f"  • Even with {sim_results['prob_profit']*100:.0f}% chance of profit, you can still lose")
        report.append(f"  • {sim_results['prob_loss']*100:.0f}% of the time you'll LOSE money on this portfolio")
        report.append(f"  • 5% of the time you'll lose ${abs(sim_results['percentile_5']):,.0f} or more")
        report.append(f"  • Coefficient of Variation: {sim_results['coefficient_of_variation']:.2f}")
        report.append("")
        report.append("")
        report.append("RISK OF RUIN ANALYSIS")
        report.append("-" * 80)
        report.append(f"  Risk of Ruin:          {ruin_analysis['risk_of_ruin']*100:.2f}%")
        report.append(f"  Current Risk Level:    {ruin_analysis['current_risk_level']}")
        report.append(f"  Bankroll in Units:     {ruin_analysis['bankroll_units']:.1f}")
        report.append(f"  Edge Per Bet:          {ruin_analysis['edge_per_bet']*100:+.2f}%")
        report.append(f"  Kelly Fraction:        {ruin_analysis['kelly_fraction']:.3f}")
        report.append(f"  Safe Bet Size:         ${ruin_analysis['safe_bet_size']:.0f}")
        report.append("")
        if ruin_analysis['median_bets_to_ruin'] != float('inf'):
            report.append(f"  ⚠️  Median Bets to Ruin:   {ruin_analysis['median_bets_to_ruin']:.0f}")
        report.append("")
        report.append("")
        report.append("LOSING STREAK ANALYSIS")
        report.append("-" * 80)
        report.append(f"  Win Rate:              {streak_analysis['win_rate']*100:.1f}%")
        report.append(f"  Expected Max Streak:   {streak_analysis['expected_max_streak']:.0f} bets")
        report.append("")
        report.append("  Probability of Losing Streaks:")
        for length, probs in streak_analysis['streak_probabilities'].items():
            report.append(f"    {length}-bet streak:       {probs['prob_occurs_in_sample']*100:.1f}% chance")
        report.append("")
        report.append("  🚨 CRITICAL WARNINGS:")
        for warning in streak_analysis['warnings']:
            report.append(f"    • {warning}")
        report.append("")
        report.append("")
        report.append("KEY TAKEAWAYS")
        report.append("-" * 80)
        report.append("  1. SHORT-TERM RESULTS ARE DOMINATED BY VARIANCE")
        report.append("     - Expected value only emerges over large samples (1000+ bets)")
        report.append("     - 100 bets is NOT enough to evaluate a strategy")
        report.append("")
        report.append("  2. LOSING STREAKS ARE INEVITABLE")
        report.append("     - Even 70% win rate → expect 5+ bet losing streaks")
        report.append("     - This is NORMAL, not a sign your model is broken")
        report.append("")
        report.append("  3. BANKROLL MANAGEMENT IS CRITICAL")
        report.append("     - Risk of ruin is REAL, even with +EV")
        report.append("     - Never bet more than Kelly fraction suggests")
        report.append("     - Fractional Kelly (1/4 to 1/2) is safer")
        report.append("")
        report.append("  4. PSYCHOLOGICAL PREPARATION")
        report.append("     - Accept that drawdowns will happen")
        report.append("     - Don't increase bet size to chase losses")
        report.append("     - Don't decrease bet size during cold streaks (if model is sound)")
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


if __name__ == "__main__":
    """Example usage."""

    analyzer = VarianceAnalyzer()

    # Example: 5 bets portfolio
    example_bets = [
        {'model_prob': 0.613, 'odds': +116, 'stake': 500},
        {'model_prob': 0.760, 'odds': -114, 'stake': 500},
        {'model_prob': 0.785, 'odds': -110, 'stake': 500},
        {'model_prob': 0.851, 'odds': -110, 'stake': 500},
        {'model_prob': 0.685, 'odds': +172, 'stake': 500},
    ]

    report = analyzer.generate_variance_report(
        bets=example_bets,
        bankroll=10000,
        num_simulations=10000
    )

    print(report)
