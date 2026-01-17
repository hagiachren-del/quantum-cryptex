#!/usr/bin/env python3
"""
View Performance Statistics

Quick script to view betting performance statistics.
"""

import sys

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from tracking.bet_tracker import BetTracker
from tracking.performance_analytics import PerformanceAnalytics


def main():
    """Display performance report"""

    print()
    tracker = BetTracker("bet_history.json")

    if not tracker.bets:
        print("=" * 80)
        print("No bet history found.")
        print("=" * 80)
        print()
        print("To get started, log your first bets:")
        print("  python3 log_bet_results.py --init")
        print()
        print("Or add bets interactively:")
        print("  python3 log_bet_results.py")
        print()
        return

    analytics = PerformanceAnalytics(tracker)
    report = analytics.generate_performance_report()

    print(report)

    # Show ROI timeline if we have enough bets
    roi_timeline = analytics.calculate_roi_over_time()

    if len(roi_timeline) > 1:
        print()
        print("📈 ROI OVER TIME")
        print("-" * 80)
        print(f"{'Date':<12} {'Bet':<20} {'Profit':<12} {'Cumulative ROI':<15}")
        print("-" * 80)

        for entry in roi_timeline:
            print(
                f"{entry['date']:<12} "
                f"{entry['bet_id']:<20} "
                f"${entry['cumulative_profit']:>10,.2f} "
                f"{entry['cumulative_roi']:>+13.2f}%"
            )
        print()


if __name__ == '__main__':
    main()
