"""
Performance Metrics for Betting Backtests

Calculates various performance metrics including risk-adjusted returns,
calibration, and variance measures.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd


def calculate_sharpe_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Sharpe ratio (risk-adjusted return).

    Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns

    Args:
        returns: Array of bet returns
        risk_free_rate: Risk-free rate (default 0)

    Returns:
        Sharpe ratio (higher is better, > 1.0 is good)
    """
    if len(returns) == 0:
        return 0.0

    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)

    if std_return == 0:
        return 0.0

    sharpe = (mean_return - risk_free_rate) / std_return

    # Annualize (assuming ~250 bets per year)
    sharpe_annual = sharpe * np.sqrt(250)

    return sharpe_annual


def calculate_sortino_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Sortino ratio (downside deviation only).

    Like Sharpe but only penalizes downside volatility.

    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate

    Returns:
        Sortino ratio
    """
    if len(returns) == 0:
        return 0.0

    mean_return = np.mean(returns)

    # Downside deviation (only negative returns)
    downside_returns = returns[returns < 0]

    if len(downside_returns) == 0:
        return float('inf')

    downside_std = np.std(downside_returns, ddof=1)

    if downside_std == 0:
        return 0.0

    sortino = (mean_return - risk_free_rate) / downside_std

    # Annualize
    sortino_annual = sortino * np.sqrt(250)

    return sortino_annual


def calculate_calmar_ratio(
    total_return: float,
    max_drawdown: float,
    years: float = 1.0
) -> float:
    """
    Calculate Calmar ratio (return / max drawdown).

    Measures return per unit of worst drawdown.

    Args:
        total_return: Total return (as decimal, e.g., 0.15 = 15%)
        max_drawdown: Maximum drawdown (as decimal, e.g., 0.20 = 20%)
        years: Number of years (for annualization)

    Returns:
        Calmar ratio (higher is better)
    """
    if max_drawdown == 0:
        return float('inf') if total_return > 0 else 0.0

    annual_return = (1 + total_return) ** (1 / years) - 1

    return annual_return / max_drawdown


def calculate_max_consecutive_losses(bets: List[Dict[str, Any]]) -> int:
    """
    Calculate maximum consecutive losing bets.

    Args:
        bets: List of bet dictionaries

    Returns:
        Maximum consecutive losses
    """
    if not bets:
        return 0

    max_consecutive = 0
    current_consecutive = 0

    for bet in bets:
        if bet['won'] is False:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0

    return max_consecutive


def calculate_bet_type_breakdown(
    bets: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate performance by bet type.

    Args:
        bets: List of bet dictionaries

    Returns:
        Dictionary with stats per bet type
    """
    bet_types = {}

    for bet in bets:
        if bet['won'] is None:
            continue

        bet_type = bet['bet_type']

        if bet_type not in bet_types:
            bet_types[bet_type] = {
                'count': 0,
                'wins': 0,
                'total_staked': 0.0,
                'total_profit': 0.0,
            }

        bet_types[bet_type]['count'] += 1
        if bet['won']:
            bet_types[bet_type]['wins'] += 1
        bet_types[bet_type]['total_staked'] += bet['stake']
        bet_types[bet_type]['total_profit'] += bet['profit']

    # Calculate derived metrics
    for bet_type, stats in bet_types.items():
        stats['win_rate'] = stats['wins'] / stats['count'] if stats['count'] > 0 else 0
        stats['roi'] = stats['total_profit'] / stats['total_staked'] if stats['total_staked'] > 0 else 0

    return bet_types


def calculate_calibration_metrics(
    bets: List[Dict[str, Any]],
    num_bins: int = 10
) -> Dict[str, Any]:
    """
    Calculate model calibration (are probabilities accurate?).

    Bins bets by predicted probability and checks if actual win rate
    matches predicted probability.

    Args:
        bets: List of bet dictionaries with 'model_prob' and 'won'
        num_bins: Number of probability bins

    Returns:
        Dictionary with calibration metrics
    """
    settled_bets = [b for b in bets if b['won'] is not None and 'model_prob' in b]

    if not settled_bets:
        return {'calibration_error': None, 'bins': []}

    # Create bins
    bins = np.linspace(0, 1, num_bins + 1)
    bin_stats = []

    for i in range(num_bins):
        bin_min = bins[i]
        bin_max = bins[i + 1]

        # Filter bets in this bin
        bin_bets = [
            b for b in settled_bets
            if bin_min <= b['model_prob'] < bin_max
        ]

        if not bin_bets:
            continue

        predicted_prob = np.mean([b['model_prob'] for b in bin_bets])
        actual_win_rate = np.mean([1 if b['won'] else 0 for b in bin_bets])

        bin_stats.append({
            'bin_min': bin_min,
            'bin_max': bin_max,
            'count': len(bin_bets),
            'predicted_prob': predicted_prob,
            'actual_win_rate': actual_win_rate,
            'error': abs(predicted_prob - actual_win_rate)
        })

    # Mean calibration error
    if bin_stats:
        mean_error = np.mean([b['error'] for b in bin_stats])
    else:
        mean_error = None

    return {
        'calibration_error': mean_error,
        'bins': bin_stats
    }


def calculate_metrics(backtest_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics.

    Args:
        backtest_results: Results from backtester

    Returns:
        Dictionary with all calculated metrics
    """
    bets = backtest_results['bet_history']
    settled_bets = [b for b in bets if b['won'] is not None]

    if not settled_bets:
        return {'error': 'No settled bets to analyze'}

    # Extract returns
    returns = np.array([b['profit'] / b['stake'] for b in settled_bets])

    # Calculate metrics
    metrics = {
        # Risk-adjusted returns
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'sortino_ratio': calculate_sortino_ratio(returns),

        # Drawdown metrics
        'calmar_ratio': calculate_calmar_ratio(
            backtest_results['bankroll']['total_profit'] / backtest_results['bankroll']['initial_bankroll'],
            backtest_results['bankroll']['max_drawdown']
        ),

        # Streak metrics
        'max_consecutive_losses': calculate_max_consecutive_losses(settled_bets),

        # Bet type breakdown
        'bet_type_breakdown': calculate_bet_type_breakdown(settled_bets),

        # Calibration
        'calibration': calculate_calibration_metrics(settled_bets),

        # Basic stats (from bankroll)
        'win_rate': backtest_results['bankroll']['win_rate'],
        'roi': backtest_results['bankroll']['roi'],
        'total_profit': backtest_results['bankroll']['total_profit'],
        'max_drawdown': backtest_results['bankroll']['max_drawdown'],
    }

    return metrics


def calculate_variance_analysis(bets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze variance in betting results.

    Compares expected vs actual variance.

    Args:
        bets: List of bet dictionaries

    Returns:
        Variance analysis metrics
    """
    settled_bets = [b for b in bets if b['won'] is not None]

    if not settled_bets:
        return {}

    # Actual variance
    profits = [b['profit'] for b in settled_bets]
    actual_variance = np.var(profits)

    # Expected variance (based on EV and probabilities)
    expected_variances = []
    for bet in settled_bets:
        if 'model_prob' not in bet or 'ev' not in bet:
            continue

        # Variance = p * (win_amount - EV)^2 + (1-p) * (loss_amount - EV)^2
        p = bet['model_prob']
        win_profit = bet['profit'] if bet['won'] else 0  # Approximate
        loss_profit = -bet['stake']
        ev = bet['ev'] * bet['stake']

        var = p * (win_profit - ev) ** 2 + (1 - p) * (loss_profit - ev) ** 2
        expected_variances.append(var)

    expected_variance = np.mean(expected_variances) if expected_variances else 0

    return {
        'actual_variance': actual_variance,
        'expected_variance': expected_variance,
        'variance_ratio': actual_variance / expected_variance if expected_variance > 0 else None,
    }
