"""
Performance evaluation and metrics for backtesting.
"""

from .metrics import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    calculate_max_consecutive_losses,
    calculate_metrics,
)

from .reports import (
    generate_summary_report,
    print_backtest_summary,
)

__all__ = [
    # metrics
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_calmar_ratio",
    "calculate_max_consecutive_losses",
    "calculate_metrics",
    # reports
    "generate_summary_report",
    "print_backtest_summary",
]
