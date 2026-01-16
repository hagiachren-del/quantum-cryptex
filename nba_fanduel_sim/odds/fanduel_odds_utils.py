"""
FanDuel Odds Utilities

Handles conversion between American odds and probabilities,
with explicit handling of FanDuel-style market structures.
"""

from typing import Tuple
import numpy as np


def american_to_probability(american_odds: float) -> float:
    """
    Convert American odds to implied probability.

    FanDuel uses American odds format:
    - Negative odds (e.g., -110): Favorite, bet $110 to win $100
    - Positive odds (e.g., +150): Underdog, bet $100 to win $150

    Args:
        american_odds: American odds (e.g., -110, +150)

    Returns:
        Implied probability between 0 and 1

    Examples:
        >>> american_to_probability(-110)
        0.5238095238095238
        >>> american_to_probability(+150)
        0.4
    """
    if american_odds < 0:
        # Favorite: probability = |odds| / (|odds| + 100)
        return abs(american_odds) / (abs(american_odds) + 100)
    else:
        # Underdog: probability = 100 / (odds + 100)
        return 100 / (american_odds + 100)


def probability_to_american(probability: float) -> float:
    """
    Convert probability to American odds.

    Args:
        probability: Probability between 0 and 1

    Returns:
        American odds

    Examples:
        >>> probability_to_american(0.5238095238095238)
        -110.0
        >>> probability_to_american(0.4)
        150.0
    """
    if probability >= 0.5:
        # Favorite: odds = -100 * p / (1 - p)
        return -100 * probability / (1 - probability)
    else:
        # Underdog: odds = 100 * (1 - p) / p
        return 100 * (1 - probability) / probability


def american_to_decimal(american_odds: float) -> float:
    """
    Convert American odds to decimal odds.

    Decimal odds represent total payout per $1 bet (including stake).

    Args:
        american_odds: American odds

    Returns:
        Decimal odds

    Examples:
        >>> american_to_decimal(-110)
        1.909090909090909
        >>> american_to_decimal(+150)
        2.5
    """
    if american_odds < 0:
        return 1 + (100 / abs(american_odds))
    else:
        return 1 + (american_odds / 100)


def calculate_payout(stake: float, american_odds: float) -> float:
    """
    Calculate total payout for a winning bet on FanDuel.

    Args:
        stake: Amount wagered
        american_odds: American odds

    Returns:
        Total payout (stake + profit)

    Examples:
        >>> calculate_payout(100, -110)
        190.90909090909093
        >>> calculate_payout(100, +150)
        250.0
    """
    decimal_odds = american_to_decimal(american_odds)
    return stake * decimal_odds


def calculate_profit(stake: float, american_odds: float) -> float:
    """
    Calculate profit (excluding stake) for a winning bet.

    Args:
        stake: Amount wagered
        american_odds: American odds

    Returns:
        Profit (payout - stake)
    """
    return calculate_payout(stake, american_odds) - stake


def normalize_two_way_market(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """
    Normalize two probabilities to sum to 1.0.

    Used after vig removal or for ensuring valid probability distributions.

    Args:
        prob_a: Probability of outcome A
        prob_b: Probability of outcome B

    Returns:
        Tuple of normalized probabilities (prob_a, prob_b)

    Examples:
        >>> normalize_two_way_market(0.55, 0.55)
        (0.5, 0.5)
    """
    total = prob_a + prob_b
    if total == 0:
        return 0.5, 0.5
    return prob_a / total, prob_b / total


def validate_fanduel_odds(american_odds: float) -> bool:
    """
    Check if odds fall within realistic FanDuel ranges.

    FanDuel typically doesn't offer:
    - Extreme favorites < -10000
    - Extreme underdogs > +10000
    - Odds exactly at 0 or 100

    Args:
        american_odds: American odds to validate

    Returns:
        True if odds are realistic, False otherwise
    """
    return -10000 <= american_odds <= 10000 and american_odds != 0


def get_market_vig(prob_a: float, prob_b: float) -> float:
    """
    Calculate the vig (juice/overround) in a two-way market.

    The vig represents the sportsbook's built-in edge.
    For fair odds, probabilities sum to 1.0.
    For FanDuel odds, they typically sum to ~1.04-1.05 (4-5% vig).

    Args:
        prob_a: Implied probability of outcome A
        prob_b: Implied probability of outcome B

    Returns:
        Vig percentage (e.g., 0.0476 for 4.76% vig)

    Examples:
        >>> get_market_vig(0.5238, 0.5238)  # Both sides at -110
        0.0476
    """
    return (prob_a + prob_b) - 1.0


def is_typical_fanduel_pricing(home_odds: float, away_odds: float) -> bool:
    """
    Check if odds match typical FanDuel pricing patterns.

    FanDuel commonly uses:
    - Standard spread pricing: -110/-110
    - Slight adjustments: -108/-112, -105/-115
    - Moneyline: wide variety

    Args:
        home_odds: Home team American odds
        away_odds: Away team American odds

    Returns:
        True if pricing looks like typical FanDuel format
    """
    # Both odds should be valid
    if not (validate_fanduel_odds(home_odds) and validate_fanduel_odds(away_odds)):
        return False

    # Check reasonable vig (2% to 10%)
    prob_home = american_to_probability(home_odds)
    prob_away = american_to_probability(away_odds)
    vig = get_market_vig(prob_home, prob_away)

    return 0.02 <= vig <= 0.10


def format_american_odds(odds: float) -> str:
    """
    Format American odds for display.

    Args:
        odds: American odds

    Returns:
        Formatted string with + for positive odds

    Examples:
        >>> format_american_odds(-110)
        '-110'
        >>> format_american_odds(150)
        '+150'
    """
    if odds > 0:
        return f"+{int(odds)}"
    else:
        return str(int(odds))
