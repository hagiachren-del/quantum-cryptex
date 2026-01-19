"""
Performance Analytics

Analyzes historical bet performance and generates detailed reports.
"""

from typing import List, Dict, Tuple
import numpy as np
from collections import defaultdict
from .bet_tracker import BetTracker, BetRecord, BetOutcome


class PerformanceAnalytics:
    """
    Analyzes historical betting performance.

    Provides detailed breakdowns by bet type, time period, edge size, etc.
    """

    def __init__(self, tracker: BetTracker):
        """
        Initialize analytics with a BetTracker.

        Args:
            tracker: BetTracker instance with bet history
        """
        self.tracker = tracker

    def calculate_win_rate_by_bet_type(self) -> Dict[str, Dict]:
        """
        Calculate win rate broken down by bet type.

        Returns:
            Dictionary with stats for each bet type
        """
        settled = self.tracker.get_settled_bets()

        stats_by_type = defaultdict(lambda: {
            'bets': 0,
            'wins': 0,
            'losses': 0,
            'pushes': 0,
            'total_staked': 0.0,
            'total_profit': 0.0
        })

        for bet in settled:
            bet_type = bet.bet_type
            stats = stats_by_type[bet_type]

            stats['bets'] += 1
            stats['total_staked'] += bet.stake
            stats['total_profit'] += bet.profit

            if bet.outcome == BetOutcome.WIN.value:
                stats['wins'] += 1
            elif bet.outcome == BetOutcome.LOSS.value:
                stats['losses'] += 1
            elif bet.outcome == BetOutcome.PUSH.value:
                stats['pushes'] += 1

        # Calculate rates
        for bet_type, stats in stats_by_type.items():
            if stats['bets'] > 0:
                stats['win_rate'] = stats['wins'] / stats['bets']
                stats['roi'] = (stats['total_profit'] / stats['total_staked'] * 100) if stats['total_staked'] > 0 else 0
            else:
                stats['win_rate'] = 0.0
                stats['roi'] = 0.0

        return dict(stats_by_type)

    def calculate_win_rate_by_edge_bucket(self) -> Dict[str, Dict]:
        """
        Calculate win rate broken down by edge size.

        Buckets:
        - Small edge: 0-5%
        - Medium edge: 5-10%
        - Large edge: 10-15%
        - Very large edge: 15%+

        Returns:
            Dictionary with stats for each edge bucket
        """
        settled = self.tracker.get_settled_bets()

        buckets = {
            '0-5% edge': {'min': 0, 'max': 5, 'bets': 0, 'wins': 0, 'total_profit': 0, 'total_staked': 0},
            '5-10% edge': {'min': 5, 'max': 10, 'bets': 0, 'wins': 0, 'total_profit': 0, 'total_staked': 0},
            '10-15% edge': {'min': 10, 'max': 15, 'bets': 0, 'wins': 0, 'total_profit': 0, 'total_staked': 0},
            '15%+ edge': {'min': 15, 'max': 100, 'bets': 0, 'wins': 0, 'total_profit': 0, 'total_staked': 0},
        }

        for bet in settled:
            edge_pct = bet.edge * 100

            # Find appropriate bucket
            for bucket_name, bucket in buckets.items():
                if bucket['min'] <= edge_pct < bucket['max']:
                    bucket['bets'] += 1
                    bucket['total_staked'] += bet.stake
                    bucket['total_profit'] += bet.profit
                    if bet.outcome == BetOutcome.WIN.value:
                        bucket['wins'] += 1
                    break

        # Calculate rates
        for bucket in buckets.values():
            if bucket['bets'] > 0:
                bucket['win_rate'] = bucket['wins'] / bucket['bets']
                bucket['roi'] = (bucket['total_profit'] / bucket['total_staked'] * 100) if bucket['total_staked'] > 0 else 0
            else:
                bucket['win_rate'] = 0.0
                bucket['roi'] = 0.0

        return buckets

    def calculate_actual_vs_expected(self) -> Dict:
        """
        Compare actual win rate to model-predicted win rate.

        This is a key metric for model calibration.
        """
        settled = self.tracker.get_settled_bets()

        if not settled:
            return {
                'actual_win_rate': 0.0,
                'expected_win_rate': 0.0,
                'calibration_error': 0.0,
                'num_bets': 0
            }

        wins = sum(1 for bet in settled if bet.outcome == BetOutcome.WIN.value)
        actual_win_rate = wins / len(settled)

        # Expected win rate is average of model probabilities
        expected_win_rate = np.mean([bet.model_prob for bet in settled])

        calibration_error = abs(actual_win_rate - expected_win_rate)

        return {
            'actual_win_rate': actual_win_rate,
            'expected_win_rate': expected_win_rate,
            'calibration_error': calibration_error,
            'num_bets': len(settled),
            'total_wins': wins,
            'total_losses': sum(1 for bet in settled if bet.outcome == BetOutcome.LOSS.value)
        }

    def calculate_roi_over_time(self) -> List[Dict]:
        """
        Calculate cumulative ROI over time.

        Returns:
            List of {date, cumulative_profit, cumulative_roi} dicts
        """
        settled = sorted(self.tracker.get_settled_bets(),
                        key=lambda x: x.game_date)

        cumulative_profit = 0
        cumulative_staked = 0
        roi_timeline = []

        for bet in settled:
            cumulative_profit += bet.profit
            cumulative_staked += bet.stake
            roi = (cumulative_profit / cumulative_staked * 100) if cumulative_staked > 0 else 0

            roi_timeline.append({
                'date': bet.game_date,
                'bet_id': bet.bet_id,
                'cumulative_profit': cumulative_profit,
                'cumulative_staked': cumulative_staked,
                'cumulative_roi': roi
            })

        return roi_timeline

    def calculate_longest_streaks(self) -> Dict:
        """
        Calculate longest winning and losing streaks.

        Returns:
            Dictionary with longest win/loss streaks
        """
        settled = sorted(self.tracker.get_settled_bets(),
                        key=lambda x: x.timestamp)

        if not settled:
            return {
                'longest_win_streak': 0,
                'longest_loss_streak': 0,
                'current_streak': 0,
                'current_streak_type': None
            }

        longest_win = 0
        longest_loss = 0
        current_win = 0
        current_loss = 0

        for bet in settled:
            if bet.outcome == BetOutcome.WIN.value:
                current_win += 1
                current_loss = 0
                longest_win = max(longest_win, current_win)
            elif bet.outcome == BetOutcome.LOSS.value:
                current_loss += 1
                current_win = 0
                longest_loss = max(longest_loss, current_loss)
            else:  # Push
                current_win = 0
                current_loss = 0

        # Current streak
        current_streak = current_win if current_win > 0 else -current_loss
        current_streak_type = 'WIN' if current_win > 0 else 'LOSS' if current_loss > 0 else 'NONE'

        return {
            'longest_win_streak': longest_win,
            'longest_loss_streak': longest_loss,
            'current_streak': abs(current_streak),
            'current_streak_type': current_streak_type
        }

    def calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio of betting returns.

        Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns
        Assumes 0% risk-free rate for simplicity.

        Higher Sharpe = better risk-adjusted returns
        """
        settled = self.tracker.get_settled_bets()

        if not settled:
            return 0.0

        # Calculate return on each bet
        returns = [bet.profit / bet.stake for bet in settled]

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        sharpe = mean_return / std_return

        return sharpe

    def generate_performance_report(self) -> str:
        """
        Generate comprehensive performance report.

        Returns:
            Formatted string report
        """
        overall_stats = self.tracker.get_summary_stats()
        by_type = self.calculate_win_rate_by_bet_type()
        by_edge = self.calculate_win_rate_by_edge_bucket()
        calibration = self.calculate_actual_vs_expected()
        streaks = self.calculate_longest_streaks()
        sharpe = self.calculate_sharpe_ratio()

        lines = []
        lines.append("=" * 80)
        lines.append("🏀 NBA BETTING SIMULATOR - HISTORICAL PERFORMANCE REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Overall Performance
        lines.append("📊 OVERALL PERFORMANCE")
        lines.append("-" * 80)
        lines.append(f"Total Bets Placed:     {overall_stats['total_bets']}")
        lines.append(f"Wins:                  {overall_stats['wins']}")
        lines.append(f"Losses:                {overall_stats['losses']}")
        lines.append(f"Pushes:                {overall_stats['pushes']}")
        lines.append(f"Win Rate:              {overall_stats['win_rate']*100:.1f}%")
        lines.append("")
        lines.append(f"Total Staked:          ${overall_stats['total_staked']:,.2f}")
        lines.append(f"Total Profit/Loss:     ${overall_stats['total_profit']:,.2f}")
        lines.append(f"ROI:                   {overall_stats['roi']:+.2f}%")
        lines.append(f"Average Odds:          {overall_stats['average_odds']:+.0f}")
        lines.append(f"Average Edge:          {overall_stats['average_edge']*100:+.1f}%")
        lines.append(f"Sharpe Ratio:          {sharpe:.3f}")
        lines.append("")
        lines.append(f"Pending Bets:          {overall_stats['pending_bets']}")
        lines.append("")

        # Model Calibration
        lines.append("🎯 MODEL CALIBRATION")
        lines.append("-" * 80)
        lines.append(f"Expected Win Rate:     {calibration['expected_win_rate']*100:.1f}% (based on model probs)")
        lines.append(f"Actual Win Rate:       {calibration['actual_win_rate']*100:.1f}%")
        lines.append(f"Calibration Error:     {calibration['calibration_error']*100:.1f}%")
        lines.append("")

        if calibration['calibration_error'] < 0.05:
            lines.append("✅ Model is well-calibrated (error < 5%)")
        elif calibration['calibration_error'] < 0.10:
            lines.append("⚠️  Model calibration is acceptable (error 5-10%)")
        else:
            lines.append("🔴 Model needs recalibration (error > 10%)")

        lines.append("")

        # Performance by Bet Type
        if by_type:
            lines.append("📈 PERFORMANCE BY BET TYPE")
            lines.append("-" * 80)
            lines.append(f"{'Type':<15} {'Bets':<6} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
            lines.append("-" * 80)

            for bet_type, stats in sorted(by_type.items()):
                lines.append(
                    f"{bet_type:<15} "
                    f"{stats['bets']:<6} "
                    f"{stats['win_rate']*100:<7.1f}% "
                    f"{stats['roi']:>+8.1f}% "
                    f"${stats['total_profit']:>10,.2f}"
                )
            lines.append("")

        # Performance by Edge Size
        if by_edge:
            lines.append("💎 PERFORMANCE BY EDGE SIZE")
            lines.append("-" * 80)
            lines.append(f"{'Edge Range':<15} {'Bets':<6} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
            lines.append("-" * 80)

            for edge_range, stats in by_edge.items():
                if stats['bets'] > 0:
                    lines.append(
                        f"{edge_range:<15} "
                        f"{stats['bets']:<6} "
                        f"{stats['win_rate']*100:<7.1f}% "
                        f"{stats['roi']:>+8.1f}% "
                        f"${stats['total_profit']:>10,.2f}"
                    )
            lines.append("")

        # Streaks
        lines.append("🔥 STREAKS")
        lines.append("-" * 80)
        lines.append(f"Longest Win Streak:    {streaks['longest_win_streak']} bets")
        lines.append(f"Longest Loss Streak:   {streaks['longest_loss_streak']} bets")
        lines.append(f"Current Streak:        {streaks['current_streak']} {streaks['current_streak_type']}")
        lines.append("")

        # Key Insights
        lines.append("💡 KEY INSIGHTS")
        lines.append("-" * 80)

        # Insight 1: Win rate vs break-even
        avg_odds = overall_stats['average_odds']
        if avg_odds < 0:
            breakeven_wr = abs(avg_odds) / (abs(avg_odds) + 100)
        else:
            breakeven_wr = 100 / (avg_odds + 100)

        lines.append(f"• Average odds of {avg_odds:+.0f} requires {breakeven_wr*100:.1f}% win rate to break even")
        lines.append(f"  Your win rate: {overall_stats['win_rate']*100:.1f}%")

        if overall_stats['win_rate'] > breakeven_wr:
            lines.append(f"  ✅ Beating break-even by {(overall_stats['win_rate'] - breakeven_wr)*100:.1f}%")
        else:
            lines.append(f"  🔴 Below break-even by {(breakeven_wr - overall_stats['win_rate'])*100:.1f}%")

        lines.append("")

        # Insight 2: Sample size
        if overall_stats['total_bets'] < 50:
            lines.append(f"• Sample size ({overall_stats['total_bets']} bets) is small - results heavily influenced by variance")
        elif overall_stats['total_bets'] < 200:
            lines.append(f"• Sample size ({overall_stats['total_bets']} bets) is moderate - still significant variance")
        else:
            lines.append(f"• Sample size ({overall_stats['total_bets']} bets) is good - results becoming more reliable")

        lines.append("")

        # Insight 3: Sharpe ratio
        if sharpe > 0.5:
            lines.append(f"• Sharpe ratio of {sharpe:.2f} indicates strong risk-adjusted returns")
        elif sharpe > 0:
            lines.append(f"• Sharpe ratio of {sharpe:.2f} indicates moderate risk-adjusted returns")
        else:
            lines.append(f"• Sharpe ratio of {sharpe:.2f} indicates poor risk-adjusted returns")

        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    from bet_tracker import BetTracker, BetRecord, BetOutcome
    from datetime import datetime, timedelta

    tracker = BetTracker("example_history.json")

    # Add some example bets
    teams = [
        ("Kings", "Wizards"),
        ("Rockets", "Timberwolves"),
        ("Pacers", "Bulls"),
        ("Cavaliers", "76ers")
    ]

    for i, (home, away) in enumerate(teams):
        bet = BetRecord(
            bet_id=f"BET_{i}",
            timestamp=datetime.now().isoformat(),
            home_team=home,
            away_team=away,
            game_date=(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            bet_type="spread",
            team=home,
            odds=-110,
            line=-7.0,
            model_prob=0.60,
            market_prob=0.52,
            edge=0.08,
            ev_percentage=10.0,
            adjusted_ev=8.0,
            stake=100
        )
        tracker.add_bet(bet)

        # All won
        tracker.update_bet_outcome(bet.bet_id, BetOutcome.WIN, f"{home} won")

    # Generate report
    analytics = PerformanceAnalytics(tracker)
    report = analytics.generate_performance_report()
    print(report)
