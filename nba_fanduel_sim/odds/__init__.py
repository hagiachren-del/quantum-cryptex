"""
Odds processing and vig removal for FanDuel markets.
"""

from .fanduel_odds_utils import (
    american_to_probability,
    probability_to_american,
    american_to_decimal,
    calculate_payout,
    calculate_profit,
    normalize_two_way_market,
    validate_fanduel_odds,
    get_market_vig,
    is_typical_fanduel_pricing,
    format_american_odds,
)

from .vig_removal import (
    remove_vig,
    remove_vig_proportional,
    remove_vig_additive,
    remove_vig_power,
    remove_vig_shin,
    calculate_fair_odds_from_american,
    get_vig_adjusted_edge,
    VigMethod,
)

__all__ = [
    # fanduel_odds_utils
    "american_to_probability",
    "probability_to_american",
    "american_to_decimal",
    "calculate_payout",
    "calculate_profit",
    "normalize_two_way_market",
    "validate_fanduel_odds",
    "get_market_vig",
    "is_typical_fanduel_pricing",
    "format_american_odds",
    # vig_removal
    "remove_vig",
    "remove_vig_proportional",
    "remove_vig_additive",
    "remove_vig_power",
    "remove_vig_shin",
    "calculate_fair_odds_from_american",
    "get_vig_adjusted_edge",
    "VigMethod",
]
