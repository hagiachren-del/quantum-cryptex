"""
Report Generation for Backtest Results

Generates human-readable summaries and visualizations of backtest performance.
"""

from typing import Dict, Any
import pandas as pd


def generate_summary_report(backtest_results: Dict[str, Any]) -> str:
    """
    Generate a text summary report of backtest results.

    Args:
        backtest_results: Results from backtester

    Returns:
        Formatted string report
    """
    report_lines = []

    report_lines.append("=" * 70)
    report_lines.append("NBA FANDUEL BETTING SIMULATOR - BACKTEST RESULTS")
    report_lines.append("=" * 70)
    report_lines.append("")

    # Configuration
    report_lines.append("CONFIGURATION")
    report_lines.append("-" * 70)
    config = backtest_results['config']
    report_lines.append(f"Model:              {config['model']}")
    report_lines.append(f"Initial Bankroll:   ${config['initial_bankroll']:,.2f}")
    report_lines.append(f"Bet Sizing:         {config['bet_sizing_method']}")
    if config['bet_sizing_method'] == 'fractional_kelly':
        report_lines.append(f"Kelly Fraction:     {config['kelly_fraction']}")
    report_lines.append(f"Min EV Threshold:   {config['min_ev'] * 100:.1f}%")
    report_lines.append("")

    # Game Statistics
    report_lines.append("GAME STATISTICS")
    report_lines.append("-" * 70)
    report_lines.append(f"Games Processed:    {backtest_results['games_processed']:,}")
    report_lines.append(f"Bets Attempted:     {backtest_results['bets_attempted']:,}")
    report_lines.append(f"Bets Placed:        {backtest_results['bets_placed']:,}")
    report_lines.append(f"Bets Rejected:      {backtest_results['bets_rejected']:,}")
    report_lines.append(f"Bet Rate:           {backtest_results['bet_rate'] * 100:.1f}% (bets per game)")
    report_lines.append("")

    # Bankroll Performance
    report_lines.append("BANKROLL PERFORMANCE")
    report_lines.append("-" * 70)
    br = backtest_results['bankroll']
    report_lines.append(f"Initial Bankroll:   ${br['initial_bankroll']:,.2f}")
    report_lines.append(f"Final Bankroll:     ${br['current_bankroll']:,.2f}")
    report_lines.append(f"Peak Bankroll:      ${br['peak_bankroll']:,.2f}")
    report_lines.append(f"Total Profit:       ${br['total_profit']:,.2f}")

    profit_pct = (br['current_bankroll'] - br['initial_bankroll']) / br['initial_bankroll'] * 100
    report_lines.append(f"Profit %:           {profit_pct:+.2f}%")
    report_lines.append("")

    # Betting Statistics
    report_lines.append("BETTING STATISTICS")
    report_lines.append("-" * 70)
    report_lines.append(f"Total Bets:         {br['total_bets']:,}")
    report_lines.append(f"Wins:               {br['wins']:,}")
    report_lines.append(f"Losses:             {br['losses']:,}")
    report_lines.append(f"Win Rate:           {br['win_rate'] * 100:.2f}%")
    report_lines.append(f"Total Staked:       ${br['total_staked']:,.2f}")
    report_lines.append(f"ROI:                {br['roi_percentage']:+.2f}%")
    report_lines.append(f"Profit Factor:      {br['profit_factor']:.3f}")
    report_lines.append("")

    # Risk Metrics
    report_lines.append("RISK METRICS")
    report_lines.append("-" * 70)
    report_lines.append(f"Current Drawdown:   {br['current_drawdown'] * 100:.2f}%")
    report_lines.append(f"Max Drawdown:       {br['max_drawdown'] * 100:.2f}%")
    report_lines.append("")

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def print_backtest_summary(backtest_results: Dict[str, Any]) -> None:
    """
    Print a summary of backtest results to console.

    Args:
        backtest_results: Results from backtester
    """
    print(generate_summary_report(backtest_results))


def generate_bet_type_report(metrics: Dict[str, Any]) -> str:
    """
    Generate report broken down by bet type.

    Args:
        metrics: Metrics dictionary with bet_type_breakdown

    Returns:
        Formatted report string
    """
    if 'bet_type_breakdown' not in metrics:
        return "No bet type breakdown available"

    report_lines = []
    report_lines.append("\nPERFORMANCE BY BET TYPE")
    report_lines.append("-" * 70)

    breakdown = metrics['bet_type_breakdown']

    for bet_type, stats in breakdown.items():
        report_lines.append(f"\n{bet_type.upper().replace('_', ' ')}")
        report_lines.append(f"  Bets:       {stats['count']:,}")
        report_lines.append(f"  Wins:       {stats['wins']:,}")
        report_lines.append(f"  Win Rate:   {stats['win_rate'] * 100:.2f}%")
        report_lines.append(f"  Total Staked: ${stats['total_staked']:,.2f}")
        report_lines.append(f"  Profit:     ${stats['total_profit']:+,.2f}")
        report_lines.append(f"  ROI:        {stats['roi'] * 100:+.2f}%")

    return "\n".join(report_lines)


def generate_calibration_report(metrics: Dict[str, Any]) -> str:
    """
    Generate model calibration report.

    Args:
        metrics: Metrics with calibration data

    Returns:
        Formatted report string
    """
    if 'calibration' not in metrics:
        return "No calibration data available"

    report_lines = []
    report_lines.append("\nMODEL CALIBRATION")
    report_lines.append("-" * 70)

    calib = metrics['calibration']

    if calib['calibration_error'] is not None:
        report_lines.append(f"Mean Calibration Error: {calib['calibration_error'] * 100:.2f}%")
        report_lines.append("\nProbability Bins:")
        report_lines.append(f"{'Range':<15} {'Count':<10} {'Predicted':<12} {'Actual':<12} {'Error':<10}")
        report_lines.append("-" * 70)

        for bin_data in calib['bins']:
            range_str = f"{bin_data['bin_min']:.2f}-{bin_data['bin_max']:.2f}"
            report_lines.append(
                f"{range_str:<15} {bin_data['count']:<10} "
                f"{bin_data['predicted_prob'] * 100:>10.1f}% "
                f"{bin_data['actual_win_rate'] * 100:>10.1f}% "
                f"{bin_data['error'] * 100:>8.1f}%"
            )

    return "\n".join(report_lines)


def generate_full_report(
    backtest_results: Dict[str, Any],
    metrics: Dict[str, Any]
) -> str:
    """
    Generate comprehensive report with all metrics.

    Args:
        backtest_results: Backtest results
        metrics: Calculated metrics

    Returns:
        Full formatted report
    """
    report_parts = []

    # Main summary
    report_parts.append(generate_summary_report(backtest_results))

    # Risk-adjusted metrics
    report_parts.append("\nRISK-ADJUSTED RETURNS")
    report_parts.append("-" * 70)
    report_parts.append(f"Sharpe Ratio:       {metrics.get('sharpe_ratio', 0):.3f}")
    report_parts.append(f"Sortino Ratio:      {metrics.get('sortino_ratio', 0):.3f}")
    report_parts.append(f"Calmar Ratio:       {metrics.get('calmar_ratio', 0):.3f}")
    report_parts.append(f"Max Consecutive Losses: {metrics.get('max_consecutive_losses', 0)}")

    # Bet type breakdown
    report_parts.append(generate_bet_type_report(metrics))

    # Calibration
    report_parts.append(generate_calibration_report(metrics))

    return "\n".join(report_parts)


def save_report_to_file(report: str, filepath: str) -> None:
    """
    Save report to text file.

    Args:
        report: Report string
        filepath: Output file path
    """
    with open(filepath, 'w') as f:
        f.write(report)

    print(f"Report saved to {filepath}")
