"""
Market Efficiency Analysis and Reality Checks

Addresses the reality that:
1. NBA betting markets are highly efficient
2. True +EV is extremely rare and difficult to sustain
3. Sportsbooks quickly adjust to winning patterns
4. Even +EV bets lose frequently due to variance
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class EfficiencyMetrics:
    """Metrics for assessing market efficiency."""
    vig_percentage: float
    market_accuracy: float
    closing_line_value: float
    professional_consensus: float
    sharp_money_indicator: float

    @property
    def efficiency_score(self) -> float:
        """
        Overall efficiency score (0-100).

        Higher = more efficient market = harder to beat

        NBA typically scores 85-95 (very efficient)
        """
        # Weighted average of metrics
        score = (
            (1 - self.vig_percentage / 0.10) * 20 +  # Low vig = efficient
            self.market_accuracy * 30 +  # Accurate predictions
            self.closing_line_value * 25 +  # Sharp closing lines
            self.professional_consensus * 15 +  # Pro agreement
            self.sharp_money_indicator * 10  # Sharp action aligned
        )
        return min(100, max(0, score))

    @property
    def efficiency_level(self) -> str:
        """Human-readable efficiency level."""
        score = self.efficiency_score
        if score >= 90:
            return "EXTREMELY EFFICIENT - Nearly impossible to beat"
        elif score >= 80:
            return "HIGHLY EFFICIENT - Very difficult to beat"
        elif score >= 70:
            return "MODERATELY EFFICIENT - Difficult to beat"
        elif score >= 60:
            return "SOMEWHAT EFFICIENT - Challenging to beat"
        else:
            return "LESS EFFICIENT - Opportunities may exist"


class MarketEfficiencyAnalyzer:
    """
    Analyzes betting market efficiency and provides reality checks.

    Purpose: Prevent overconfidence and unrealistic expectations.
    """

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze_game_efficiency(
        self,
        market_implied_prob: float,
        actual_outcome: float,
        vig: float,
        line_movement: float = 0,
        sharp_percentage: float = 50.0
    ) -> EfficiencyMetrics:
        """
        Analyze efficiency of a single game's market.

        Args:
            market_implied_prob: Market's implied probability
            actual_outcome: Actual result (1 if won, 0 if lost)
            vig: Market vig percentage
            line_movement: Points of line movement toward sharps
            sharp_percentage: Percentage of sharp money on this side

        Returns:
            EfficiencyMetrics object
        """
        # Market accuracy (how close prediction was)
        accuracy = 1 - abs(market_implied_prob - actual_outcome)

        # Closing line value (did sharps move line?)
        clv = min(1.0, abs(line_movement) / 3.0) if line_movement else 0.5

        # Professional consensus (are pros aligned?)
        consensus = sharp_percentage / 100.0

        # Sharp money indicator
        sharp_indicator = min(1.0, sharp_percentage / 70.0)

        return EfficiencyMetrics(
            vig_percentage=vig,
            market_accuracy=accuracy,
            closing_line_value=clv,
            professional_consensus=consensus,
            sharp_money_indicator=sharp_indicator
        )

    def reality_check_ev_opportunity(
        self,
        model_prob: float,
        market_prob: float,
        odds: float,
        ev_percentage: float,
        game_context: Dict = None
    ) -> Dict[str, any]:
        """
        Perform reality check on claimed +EV opportunity.

        Questions to ask:
        1. Is the edge realistic for NBA?
        2. Did I miss something the market knows?
        3. Am I overconfident in my model?
        4. Is this a trap line?

        Returns:
            Dictionary with warning flags and confidence adjustments
        """
        warnings = []
        confidence_multiplier = 1.0

        # Flag 1: Edge too large (probably wrong)
        if abs(model_prob - market_prob) > 0.15:
            warnings.append({
                'level': 'CRITICAL',
                'message': f'Edge of {abs(model_prob - market_prob)*100:.1f}% is unrealistic for NBA',
                'explanation': 'NBA markets are highly efficient. Edges >10% are extremely rare.',
                'action': 'Double-check your model. You likely missed key information.'
            })
            confidence_multiplier *= 0.3

        elif abs(model_prob - market_prob) > 0.10:
            warnings.append({
                'level': 'HIGH',
                'message': f'Edge of {abs(model_prob - market_prob)*100:.1f}% is very large',
                'explanation': 'Large edges in NBA usually indicate model error or missing data.',
                'action': 'Verify injury reports, lineups, and recent news.'
            })
            confidence_multiplier *= 0.5

        elif abs(model_prob - market_prob) > 0.05:
            warnings.append({
                'level': 'MODERATE',
                'message': f'Edge of {abs(model_prob - market_prob)*100:.1f}% is significant',
                'explanation': 'Moderate edges can exist but are uncommon.',
                'action': 'Proceed with caution. Reduce stake size.'
            })
            confidence_multiplier *= 0.75

        # Flag 2: Model prob too extreme
        if model_prob > 0.90 or model_prob < 0.10:
            warnings.append({
                'level': 'HIGH',
                'message': f'Model probability {model_prob*100:.1f}% is very extreme',
                'explanation': 'NBA games rarely have >90% or <10% true probabilities.',
                'action': 'Check for data errors or model overfitting.'
            })
            confidence_multiplier *= 0.6

        # Flag 3: High EV bet on favorite
        if ev_percentage > 0.10 and odds < 0 and abs(odds) > 150:
            warnings.append({
                'level': 'MODERATE',
                'message': 'High EV on heavy favorite is suspicious',
                'explanation': 'Heavy favorites are usually efficiently priced.',
                'action': 'Market may know something you don\'t (injury, motivation).'
            })
            confidence_multiplier *= 0.7

        # Flag 4: High EV on underdog
        if ev_percentage > 0.15 and odds > 150:
            warnings.append({
                'level': 'MODERATE',
                'message': 'Very high EV on underdog is unusual',
                'explanation': 'Public often overvalues underdogs, but not by this much.',
                'action': 'Verify you\'re not overvaluing recent performance.'
            })
            confidence_multiplier *= 0.75

        # Flag 5: Check for "trap lines"
        if game_context:
            if game_context.get('public_betting_percentage', 50) > 75:
                warnings.append({
                    'level': 'LOW',
                    'message': '>75% of public on your side',
                    'explanation': 'Heavy public action often indicates value on other side.',
                    'action': 'Proceed with extra caution.'
                })
                confidence_multiplier *= 0.9

        # Calculate adjusted edge
        adjusted_edge = (model_prob - market_prob) * confidence_multiplier
        adjusted_ev = ev_percentage * confidence_multiplier

        # Overall recommendation
        if not warnings:
            recommendation = "PROCEED"
            color = "GREEN"
        elif any(w['level'] == 'CRITICAL' for w in warnings):
            recommendation = "DO NOT BET"
            color = "RED"
        elif any(w['level'] == 'HIGH' for w in warnings):
            recommendation = "PROCEED WITH CAUTION"
            color = "YELLOW"
        else:
            recommendation = "PROCEED (REDUCED STAKE)"
            color = "YELLOW"

        return {
            'recommendation': recommendation,
            'color': color,
            'warnings': warnings,
            'confidence_multiplier': confidence_multiplier,
            'adjusted_edge': adjusted_edge,
            'adjusted_ev': adjusted_ev,
            'original_edge': model_prob - market_prob,
            'original_ev': ev_percentage
        }

    def estimate_long_term_viability(
        self,
        current_roi: float,
        sample_size: int,
        win_rate: float,
        avg_odds: float,
        bet_frequency: float  # Bets per day
    ) -> Dict[str, any]:
        """
        Estimate if current results can be sustained long-term.

        Reality: Most +EV strategies eventually get limited or bet out.

        Returns:
            Viability analysis with time-to-limit estimates
        """
        # Calculate confidence interval for ROI
        std_error = np.sqrt(win_rate * (1 - win_rate) / sample_size)
        ci_95_lower = current_roi - 1.96 * std_error
        ci_95_upper = current_roi + 1.96 * std_error

        # Estimate when FanDuel will notice
        if current_roi > 0.15 and sample_size > 100:
            days_until_limited = 30  # Very fast
            severity = "IMMEDIATE LIMITS"
        elif current_roi > 0.10 and sample_size > 200:
            days_until_limited = 60
            severity = "FAST LIMITS"
        elif current_roi > 0.05 and sample_size > 500:
            days_until_limited = 120
            severity = "EVENTUAL LIMITS"
        elif current_roi > 0.03:
            days_until_limited = 240
            severity = "SLOW LIMITS"
        else:
            days_until_limited = 999
            severity = "PROBABLY SAFE"

        # Calculate expected value at limiting
        bets_before_limited = days_until_limited * bet_frequency
        profit_before_limited = bets_before_limited * current_roi * 100  # Assume $100 avg stake

        # Reality check
        is_sustainable = current_roi > 0.03 and ci_95_lower > 0

        return {
            'is_sustainable': is_sustainable,
            'confidence_interval_95': (ci_95_lower, ci_95_upper),
            'days_until_limited': days_until_limited,
            'limit_severity': severity,
            'bets_before_limited': bets_before_limited,
            'expected_profit_before_limits': profit_before_limited,
            'warnings': [
                'FanDuel limits winning players',
                'ROI tends to regress toward market efficiency',
                'Small sample results are often luck',
                'Past performance ≠ future results'
            ]
        }

    def generate_efficiency_report(
        self,
        bet_history: List[Dict]
    ) -> str:
        """
        Generate comprehensive market efficiency report.

        Args:
            bet_history: List of bets with outcomes

        Returns:
            Formatted report string
        """
        if not bet_history:
            return "No bet history to analyze."

        # Calculate metrics
        total_bets = len(bet_history)
        wins = sum(1 for b in bet_history if b.get('won', False))
        win_rate = wins / total_bets if total_bets > 0 else 0

        total_staked = sum(b.get('stake', 0) for b in bet_history)
        total_profit = sum(b.get('profit', 0) for b in bet_history)
        roi = total_profit / total_staked if total_staked > 0 else 0

        # Average edge
        edges = [b.get('edge', 0) for b in bet_history if 'edge' in b]
        avg_claimed_edge = np.mean(edges) if edges else 0

        # Reality check
        viability = self.estimate_long_term_viability(
            current_roi=roi,
            sample_size=total_bets,
            win_rate=win_rate,
            avg_odds=-110,
            bet_frequency=5.0
        )

        # Generate report
        report = []
        report.append("=" * 80)
        report.append("MARKET EFFICIENCY & REALITY CHECK REPORT")
        report.append("=" * 80)
        report.append("")
        report.append("YOUR RESULTS:")
        report.append(f"  Total Bets:        {total_bets}")
        report.append(f"  Win Rate:          {win_rate*100:.1f}%")
        report.append(f"  ROI:               {roi*100:+.2f}%")
        report.append(f"  Avg Claimed Edge:  {avg_claimed_edge*100:+.2f}%")
        report.append("")
        report.append("REALITY CHECK:")
        report.append(f"  95% CI for ROI:    {viability['confidence_interval_95'][0]*100:.2f}% to {viability['confidence_interval_95'][1]*100:.2f}%")
        report.append(f"  Sustainable:       {'YES ✅' if viability['is_sustainable'] else 'NO ❌'}")
        report.append(f"  Days Until Limited: {viability['days_until_limited']} ({viability['limit_severity']})")
        report.append(f"  Profit Before Limits: ${viability['expected_profit_before_limits']:,.0f}")
        report.append("")
        report.append("⚠️  CRITICAL WARNINGS:")
        for warning in viability['warnings']:
            report.append(f"  • {warning}")
        report.append("")
        report.append("MARKET EFFICIENCY ASSESSMENT:")
        report.append("  NBA betting markets are HIGHLY EFFICIENT (85-95/100)")
        report.append("  True sustainable edges are typically <3%")
        report.append("  Sample sizes <1000 bets are heavily influenced by luck")
        report.append("")
        report.append("WHAT THIS MEANS:")
        if roi > 0.10:
            report.append("  🚨 ROI >10% is UNREALISTIC for NBA long-term")
            report.append("     You are likely experiencing variance/luck")
            report.append("     Or your model has significant errors")
            report.append("     FanDuel will limit you very quickly")
        elif roi > 0.05:
            report.append("  ⚠️  ROI >5% is VERY DIFFICULT to sustain")
            report.append("     Requires elite modeling and execution")
            report.append("     Expect limits within 2-4 months")
        elif roi > 0.03:
            report.append("  ✅ ROI 3-5% is the realistic ceiling for NBA")
            report.append("     This is world-class performance")
            report.append("     Still expect eventual limits")
        elif roi > 0:
            report.append("  📊 ROI 0-3% is marginal")
            report.append("     May not overcome variance and limits")
            report.append("     Break-even is more likely")
        else:
            report.append("  ❌ Negative ROI indicates:")
            report.append("     Model errors, bad execution, or bad luck")
            report.append("     Reassess strategy before continuing")
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


if __name__ == "__main__":
    """Example usage."""

    analyzer = MarketEfficiencyAnalyzer()

    # Example: Claimed +86% EV bet (Memphis ML)
    reality_check = analyzer.reality_check_ev_opportunity(
        model_prob=0.685,
        market_prob=0.354,
        odds=+172,
        ev_percentage=0.8634
    )

    print("REALITY CHECK: Memphis Grizzlies ML (+172)")
    print("=" * 60)
    print(f"Recommendation: {reality_check['recommendation']}")
    print(f"Confidence Multiplier: {reality_check['confidence_multiplier']:.2f}")
    print(f"Adjusted EV: {reality_check['adjusted_ev']*100:+.1f}% (was {reality_check['original_ev']*100:+.1f}%)")
    print()
    print("Warnings:")
    for warning in reality_check['warnings']:
        print(f"  [{warning['level']}] {warning['message']}")
        print(f"    → {warning['explanation']}")
        print(f"    → {warning['action']}")
        print()
