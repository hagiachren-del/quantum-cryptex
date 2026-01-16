"""
Bet Sizing and Bankroll Management

Implements various bet sizing methods including Kelly Criterion
and flat staking, with FanDuel-realistic constraints.
"""

from typing import Literal
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds import american_to_decimal


BetSizingMethod = Literal["flat", "kelly", "fractional_kelly"]


def calculate_kelly_stake(
    probability: float,
    american_odds: float,
    bankroll: float
) -> float:
    """
    Calculate optimal Kelly Criterion stake size.

    Kelly Formula:
        f* = (bp - q) / b

    Where:
        b = odds (decimal odds - 1)
        p = probability of winning
        q = probability of losing (1 - p)
        f* = fraction of bankroll to bet

    Args:
        probability: Estimated win probability (0 to 1)
        american_odds: FanDuel American odds
        bankroll: Current bankroll

    Returns:
        Stake size in dollars

    Note:
        Full Kelly can be very aggressive. Most bettors use fractional Kelly.

    Examples:
        >>> calculate_kelly_stake(0.55, -110, 1000)
        91.74  # Bet ~9.2% of bankroll
    """
    # Convert to decimal odds
    decimal_odds = american_to_decimal(american_odds)
    b = decimal_odds - 1  # Net odds

    # Kelly formula
    p = probability
    q = 1 - probability

    kelly_fraction = (b * p - q) / b

    # Ensure non-negative (no bet if negative EV)
    kelly_fraction = max(0, kelly_fraction)

    # Calculate stake
    stake = bankroll * kelly_fraction

    return stake


def calculate_fractional_kelly(
    probability: float,
    american_odds: float,
    bankroll: float,
    kelly_fraction: float = 0.25
) -> float:
    """
    Calculate fractional Kelly stake (safer than full Kelly).

    Most professional bettors use 1/4 Kelly to 1/2 Kelly
    to reduce variance while maintaining long-term growth.

    Args:
        probability: Estimated win probability
        american_odds: FanDuel odds
        bankroll: Current bankroll
        kelly_fraction: Fraction of Kelly to use (default 0.25 = quarter Kelly)

    Returns:
        Stake size in dollars

    Examples:
        >>> calculate_fractional_kelly(0.55, -110, 1000, kelly_fraction=0.25)
        22.94  # 1/4 of full Kelly
    """
    full_kelly = calculate_kelly_stake(probability, american_odds, bankroll)
    return full_kelly * kelly_fraction


def calculate_flat_stake(
    bankroll: float,
    flat_percentage: float = 0.01
) -> float:
    """
    Calculate flat stake as percentage of bankroll.

    Simplest method: bet fixed percentage of current bankroll.

    Args:
        bankroll: Current bankroll
        flat_percentage: Percentage of bankroll to bet (default 1%)

    Returns:
        Stake size in dollars

    Examples:
        >>> calculate_flat_stake(1000, 0.02)
        20.0  # 2% of bankroll
    """
    return bankroll * flat_percentage


def calculate_stake(
    probability: float,
    american_odds: float,
    bankroll: float,
    method: BetSizingMethod = "fractional_kelly",
    kelly_fraction: float = 0.25,
    flat_percentage: float = 0.01,
    max_bet_percentage: float = 0.05,
    min_bet_amount: float = 10.0,
    max_bet_amount: float = None
) -> float:
    """
    Calculate bet size using specified method with safety constraints.

    This is the main entry point for bet sizing.

    Args:
        probability: Model's win probability
        american_odds: FanDuel odds
        bankroll: Current bankroll
        method: Sizing method ("flat", "kelly", "fractional_kelly")
        kelly_fraction: Fraction for fractional Kelly (default 0.25)
        flat_percentage: Percentage for flat staking (default 0.01)
        max_bet_percentage: Maximum bet as % of bankroll (default 5%)
        min_bet_amount: Minimum bet in dollars (default $10)
        max_bet_amount: Maximum bet in dollars (optional)

    Returns:
        Stake size in dollars, constrained by limits

    Raises:
        ValueError: If method is not recognized
    """
    # Calculate raw stake based on method
    if method == "flat":
        stake = calculate_flat_stake(bankroll, flat_percentage)
    elif method == "kelly":
        stake = calculate_kelly_stake(probability, american_odds, bankroll)
    elif method == "fractional_kelly":
        stake = calculate_fractional_kelly(
            probability, american_odds, bankroll, kelly_fraction
        )
    else:
        raise ValueError(f"Unknown bet sizing method: {method}")

    # Apply max bet percentage constraint
    max_stake = bankroll * max_bet_percentage
    stake = min(stake, max_stake)

    # Apply max bet amount constraint (if specified)
    if max_bet_amount is not None:
        stake = min(stake, max_bet_amount)

    # Apply minimum bet constraint
    # If stake is below minimum, don't bet at all
    if stake < min_bet_amount:
        return 0.0

    return stake


def simulate_kelly_growth(
    initial_bankroll: float,
    win_rate: float,
    average_odds: float,
    num_bets: int = 100,
    kelly_fraction: float = 0.25,
    random_seed: int = 42
) -> np.ndarray:
    """
    Simulate bankroll growth using Kelly Criterion.

    Useful for understanding variance and drawdown risk.

    Args:
        initial_bankroll: Starting bankroll
        win_rate: Expected win rate (0 to 1)
        average_odds: Average American odds
        num_bets: Number of bets to simulate
        kelly_fraction: Kelly fraction to use
        random_seed: Random seed for reproducibility

    Returns:
        Array of bankroll values over time

    Example:
        >>> growth = simulate_kelly_growth(1000, 0.55, -110, 100)
        >>> final_bankroll = growth[-1]
    """
    np.random.seed(random_seed)

    bankrolls = [initial_bankroll]
    current_bankroll = initial_bankroll

    for _ in range(num_bets):
        # Calculate stake
        stake = calculate_fractional_kelly(
            win_rate,
            average_odds,
            current_bankroll,
            kelly_fraction
        )

        # Simulate outcome
        won = np.random.random() < win_rate

        if won:
            from odds import calculate_profit
            profit = calculate_profit(stake, average_odds)
            current_bankroll += profit
        else:
            current_bankroll -= stake

        # Stop if bankrupt
        if current_bankroll <= 0:
            current_bankroll = 0
            bankrolls.append(0)
            break

        bankrolls.append(current_bankroll)

    return np.array(bankrolls)


def estimate_optimal_kelly_fraction(
    win_rate: float,
    average_odds: float,
    max_drawdown_tolerance: float = 0.30,
    num_simulations: int = 1000
) -> float:
    """
    Estimate optimal Kelly fraction based on drawdown tolerance.

    Runs simulations to find the Kelly fraction that keeps
    drawdowns within acceptable limits.

    Args:
        win_rate: Expected win rate
        average_odds: Average odds
        max_drawdown_tolerance: Maximum acceptable drawdown (default 30%)
        num_simulations: Number of simulations to run

    Returns:
        Recommended Kelly fraction

    Note:
        This is computationally expensive. Use sparingly.
    """
    kelly_fractions = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
    drawdowns = []

    for fraction in kelly_fractions:
        max_drawdowns = []

        for seed in range(num_simulations):
            bankrolls = simulate_kelly_growth(
                1000, win_rate, average_odds,
                num_bets=200,
                kelly_fraction=fraction,
                random_seed=seed
            )

            # Calculate max drawdown
            peak = bankrolls[0]
            max_dd = 0

            for br in bankrolls:
                if br > peak:
                    peak = br
                dd = (peak - br) / peak
                max_dd = max(max_dd, dd)

            max_drawdowns.append(max_dd)

        # Average max drawdown for this fraction
        avg_max_dd = np.mean(max_drawdowns)
        drawdowns.append(avg_max_dd)

    # Find largest fraction that keeps drawdown acceptable
    for i, dd in enumerate(drawdowns):
        if dd > max_drawdown_tolerance:
            # Return previous fraction (or 0.1 if first one is too high)
            return kelly_fractions[max(0, i - 1)]

    # If all fractions are acceptable, return largest
    return kelly_fractions[-1]


def get_fanduel_stake_limits(bet_type: str = "moneyline") -> dict:
    """
    Get realistic FanDuel stake limits.

    FanDuel has bet limits that vary by market and user.
    Sharp bettors often get limited to lower stakes.

    Args:
        bet_type: Type of bet (moneyline, spread, etc.)

    Returns:
        Dictionary with min_stake and max_stake

    Note:
        These are approximate. Actual limits vary by:
        - Sport and market
        - User betting history
        - Line movement
        - Account status (sharp vs recreational)
    """
    # Approximate FanDuel limits (can vary widely)
    limits = {
        "moneyline": {
            "min_stake": 1.0,      # $1 minimum
            "max_stake": 10000.0,  # $10k for recreational accounts
            "max_stake_sharp": 500.0,  # Sharps often limited to $500 or less
        },
        "spread": {
            "min_stake": 1.0,
            "max_stake": 5000.0,
            "max_stake_sharp": 300.0,
        },
        "total": {
            "min_stake": 1.0,
            "max_stake": 5000.0,
            "max_stake_sharp": 300.0,
        },
    }

    return limits.get(bet_type, limits["moneyline"])
