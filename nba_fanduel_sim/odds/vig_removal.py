"""
Vig Removal Methods

Removes sportsbook vig (juice) from implied probabilities
to estimate true market probabilities.

FanDuel builds vig into all markets. These methods attempt to
extract the "fair" odds the market implies.
"""

from typing import Tuple, Literal
import numpy as np
from .fanduel_odds_utils import get_market_vig


VigMethod = Literal["proportional", "additive", "power", "shin"]


def remove_vig_proportional(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """
    Remove vig using proportional (multiplicative) method.

    This is the default method. It scales both probabilities
    proportionally so they sum to 1.0.

    Formula:
        fair_prob_a = prob_a / (prob_a + prob_b)
        fair_prob_b = prob_b / (prob_a + prob_b)

    Args:
        prob_a: Implied probability of outcome A (with vig)
        prob_b: Implied probability of outcome B (with vig)

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) summing to 1.0

    Examples:
        >>> remove_vig_proportional(0.5238, 0.5238)  # -110 / -110
        (0.5, 0.5)
        >>> remove_vig_proportional(0.60, 0.45)
        (0.5714285714285714, 0.42857142857142855)
    """
    total = prob_a + prob_b
    if total == 0:
        return 0.5, 0.5

    return prob_a / total, prob_b / total


def remove_vig_additive(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """
    Remove vig using additive (margin) method.

    Subtracts half the vig from each probability.

    Formula:
        vig = (prob_a + prob_b) - 1
        fair_prob_a = prob_a - (vig / 2)
        fair_prob_b = prob_b - (vig / 2)

    Args:
        prob_a: Implied probability of outcome A (with vig)
        prob_b: Implied probability of outcome B (with vig)

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) summing to 1.0

    Examples:
        >>> remove_vig_additive(0.5238, 0.5238)
        (0.5, 0.5)
    """
    vig = get_market_vig(prob_a, prob_b)
    fair_a = prob_a - (vig / 2)
    fair_b = prob_b - (vig / 2)

    # Ensure probabilities are valid
    fair_a = max(0.01, min(0.99, fair_a))
    fair_b = max(0.01, min(0.99, fair_b))

    # Normalize to ensure they sum to 1.0
    total = fair_a + fair_b
    return fair_a / total, fair_b / total


def remove_vig_power(
    prob_a: float, prob_b: float, power: float = 1.5
) -> Tuple[float, float]:
    """
    Remove vig using power method.

    Applies a power transformation before normalizing.
    This method assumes longshots are more overpriced.

    Formula:
        fair_prob_a = prob_a^k / (prob_a^k + prob_b^k)
        where k is the power parameter (typically 1.5-2.0)

    Args:
        prob_a: Implied probability of outcome A (with vig)
        prob_b: Implied probability of outcome B (with vig)
        power: Power parameter (default 1.5)

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) summing to 1.0
    """
    prob_a_powered = prob_a ** power
    prob_b_powered = prob_b ** power
    total = prob_a_powered + prob_b_powered

    if total == 0:
        return 0.5, 0.5

    return prob_a_powered / total, prob_b_powered / total


def remove_vig_shin(prob_a: float, prob_b: float, max_iterations: int = 100) -> Tuple[float, float]:
    """
    Remove vig using Shin's method (simplified).

    This method accounts for informed betting and attempts
    to find the true probabilities that, when adjusted for vig,
    produce the observed market prices.

    Note: This is a simplified implementation. Full Shin method
    requires iterative solving of a polynomial equation.

    Args:
        prob_a: Implied probability of outcome A (with vig)
        prob_b: Implied probability of outcome B (with vig)
        max_iterations: Maximum iterations for convergence

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) summing to 1.0
    """
    # For simplicity, use proportional method with adjustment
    # A full Shin implementation would solve for the insider trading parameter
    vig = get_market_vig(prob_a, prob_b)

    # Adjust for vig with bias toward favorites
    if prob_a > prob_b:
        # prob_a is the favorite
        adjustment_a = vig * 0.45  # Favorite gets less vig removed
        adjustment_b = vig * 0.55  # Underdog gets more vig removed
    else:
        adjustment_a = vig * 0.55
        adjustment_b = vig * 0.45

    fair_a = prob_a - adjustment_a
    fair_b = prob_b - adjustment_b

    # Normalize
    total = fair_a + fair_b
    return fair_a / total, fair_b / total


def remove_vig(
    prob_a: float,
    prob_b: float,
    method: VigMethod = "proportional"
) -> Tuple[float, float]:
    """
    Remove vig from two-way market using specified method.

    This is the main entry point for vig removal.
    Default is proportional method, which is most common.

    Args:
        prob_a: Implied probability of outcome A (with vig)
        prob_b: Implied probability of outcome B (with vig)
        method: Vig removal method to use

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) summing to 1.0

    Raises:
        ValueError: If method is not recognized
    """
    if method == "proportional":
        return remove_vig_proportional(prob_a, prob_b)
    elif method == "additive":
        return remove_vig_additive(prob_a, prob_b)
    elif method == "power":
        return remove_vig_power(prob_a, prob_b)
    elif method == "shin":
        return remove_vig_shin(prob_a, prob_b)
    else:
        raise ValueError(f"Unknown vig removal method: {method}")


def calculate_fair_odds_from_american(
    american_odds_a: float,
    american_odds_b: float,
    method: VigMethod = "proportional"
) -> Tuple[float, float]:
    """
    Convert FanDuel American odds to fair probabilities.

    This is a convenience function that:
    1. Converts American odds to implied probabilities
    2. Removes vig using specified method
    3. Returns fair probabilities

    Args:
        american_odds_a: American odds for outcome A
        american_odds_b: American odds for outcome B
        method: Vig removal method

    Returns:
        Tuple of (fair_prob_a, fair_prob_b)
    """
    from .fanduel_odds_utils import american_to_probability

    prob_a = american_to_probability(american_odds_a)
    prob_b = american_to_probability(american_odds_b)

    return remove_vig(prob_a, prob_b, method)


def get_vig_adjusted_edge(
    model_prob: float,
    american_odds: float,
    opponent_odds: float,
    method: VigMethod = "proportional"
) -> float:
    """
    Calculate the edge between model probability and fair market probability.

    Args:
        model_prob: Model's estimated probability
        american_odds: FanDuel odds for this outcome
        opponent_odds: FanDuel odds for the opposing outcome
        method: Vig removal method

    Returns:
        Edge (model_prob - fair_market_prob)
        Positive edge means model sees value.
    """
    from .fanduel_odds_utils import american_to_probability

    # Get implied probabilities
    implied_prob = american_to_probability(american_odds)
    opponent_prob = american_to_probability(opponent_odds)

    # Remove vig to get fair market probability
    if american_odds < opponent_odds:  # This is the favorite
        fair_prob, _ = remove_vig(implied_prob, opponent_prob, method)
    else:  # This is the underdog
        _, fair_prob = remove_vig(opponent_prob, implied_prob, method)

    return model_prob - fair_prob
