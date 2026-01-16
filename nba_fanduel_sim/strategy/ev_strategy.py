"""
Expected Value (EV) Strategy for FanDuel NBA Markets

Identifies positive EV betting opportunities by comparing
model probabilities to FanDuel odds.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds import (
    calculate_profit,
    american_to_probability,
    get_vig_adjusted_edge,
    validate_fanduel_odds,
)


BetType = Literal["moneyline_home", "moneyline_away", "spread_home", "spread_away"]


@dataclass
class BetOpportunity:
    """
    Represents a positive EV betting opportunity.

    Attributes:
        game_id: Game identifier
        bet_type: Type of bet (moneyline_home, spread_home, etc.)
        team: Team being bet on
        odds: FanDuel American odds
        model_prob: Model's estimated probability
        fair_prob: Fair probability after vig removal
        implied_prob: Implied probability from odds (with vig)
        ev: Expected value as decimal (e.g., 0.05 = 5% EV)
        ev_percent: Expected value as percentage
        edge: Model probability - fair probability
    """
    game_id: str
    bet_type: BetType
    team: str
    odds: float
    model_prob: float
    fair_prob: float
    implied_prob: float
    ev: float
    ev_percent: float
    edge: float

    def __repr__(self) -> str:
        return (
            f"BetOpportunity({self.bet_type}, {self.team}, "
            f"odds={self.odds:+.0f}, EV={self.ev_percent:.2f}%)"
        )


def calculate_ev(
    model_prob: float,
    american_odds: float,
    stake: float = 100.0
) -> float:
    """
    Calculate expected value of a bet.

    EV = (Probability of Win × Profit) - (Probability of Loss × Stake)

    Args:
        model_prob: Model's estimated win probability (0 to 1)
        american_odds: FanDuel American odds
        stake: Bet size (default 100)

    Returns:
        Expected value in same units as stake
        Positive EV = profitable bet
        Negative EV = losing bet

    Examples:
        >>> calculate_ev(0.55, -110, 100)  # Model thinks 55% likely, FanDuel has -110
        4.09  # Expected to make $4.09 per $100 bet
        >>> calculate_ev(0.45, +150, 100)  # Model thinks 45% likely, FanDuel has +150
        12.5  # Expected to make $12.50 per $100 bet
    """
    # Calculate profit if bet wins
    profit = calculate_profit(stake, american_odds)

    # Expected value
    ev = (model_prob * profit) - ((1 - model_prob) * stake)

    return ev


def calculate_ev_percentage(
    model_prob: float,
    american_odds: float
) -> float:
    """
    Calculate EV as a percentage of stake.

    This is the standard way to express betting EV.

    Args:
        model_prob: Model's probability
        american_odds: FanDuel odds

    Returns:
        EV percentage (e.g., 0.05 = 5% EV)
    """
    ev = calculate_ev(model_prob, american_odds, stake=100.0)
    return ev / 100.0


def find_moneyline_opportunities(
    game: Dict[str, Any],
    home_prob: float,
    away_prob: float,
    min_ev: float = 0.02,
    min_edge: float = 0.01,
    vig_method: str = "proportional"
) -> List[BetOpportunity]:
    """
    Find positive EV moneyline opportunities for a game.

    Args:
        game: Game data including FanDuel moneyline odds
        home_prob: Model's home win probability
        away_prob: Model's away win probability (should be 1 - home_prob)
        min_ev: Minimum EV percentage to bet (default 2%)
        min_edge: Minimum edge vs fair odds (default 1%)
        vig_method: Vig removal method

    Returns:
        List of positive EV bet opportunities
    """
    opportunities = []

    # Validate odds
    if not validate_fanduel_odds(game['moneyline_home']):
        return opportunities
    if not validate_fanduel_odds(game['moneyline_away']):
        return opportunities

    # Home moneyline
    home_edge = get_vig_adjusted_edge(
        home_prob,
        game['moneyline_home'],
        game['moneyline_away'],
        vig_method
    )

    home_implied = american_to_probability(game['moneyline_home'])
    home_fair = home_prob - home_edge  # Fair prob = model - edge
    home_ev = calculate_ev_percentage(home_prob, game['moneyline_home'])

    if home_ev >= min_ev and home_edge >= min_edge:
        opportunities.append(BetOpportunity(
            game_id=game['game_id'],
            bet_type="moneyline_home",
            team=game['home_team'],
            odds=game['moneyline_home'],
            model_prob=home_prob,
            fair_prob=home_fair,
            implied_prob=home_implied,
            ev=home_ev,
            ev_percent=home_ev * 100,
            edge=home_edge
        ))

    # Away moneyline
    away_edge = get_vig_adjusted_edge(
        away_prob,
        game['moneyline_away'],
        game['moneyline_home'],
        vig_method
    )

    away_implied = american_to_probability(game['moneyline_away'])
    away_fair = away_prob - away_edge
    away_ev = calculate_ev_percentage(away_prob, game['moneyline_away'])

    if away_ev >= min_ev and away_edge >= min_edge:
        opportunities.append(BetOpportunity(
            game_id=game['game_id'],
            bet_type="moneyline_away",
            team=game['away_team'],
            odds=game['moneyline_away'],
            model_prob=away_prob,
            fair_prob=away_fair,
            implied_prob=away_implied,
            ev=away_ev,
            ev_percent=away_ev * 100,
            edge=away_edge
        ))

    return opportunities


def find_spread_opportunities(
    game: Dict[str, Any],
    home_cover_prob: float,
    away_cover_prob: float,
    min_ev: float = 0.02,
    min_edge: float = 0.01,
    vig_method: str = "proportional"
) -> List[BetOpportunity]:
    """
    Find positive EV spread betting opportunities.

    Args:
        game: Game data including FanDuel spread and odds
        home_cover_prob: Probability home team covers the spread
        away_cover_prob: Probability away team covers (should be 1 - home_cover_prob)
        min_ev: Minimum EV percentage
        min_edge: Minimum edge vs fair odds
        vig_method: Vig removal method

    Returns:
        List of positive EV spread bet opportunities
    """
    opportunities = []

    # Validate spread odds
    if not validate_fanduel_odds(game['spread_odds_home']):
        return opportunities
    if not validate_fanduel_odds(game['spread_odds_away']):
        return opportunities

    # Home spread
    home_edge = get_vig_adjusted_edge(
        home_cover_prob,
        game['spread_odds_home'],
        game['spread_odds_away'],
        vig_method
    )

    home_implied = american_to_probability(game['spread_odds_home'])
    home_fair = home_cover_prob - home_edge
    home_ev = calculate_ev_percentage(home_cover_prob, game['spread_odds_home'])

    if home_ev >= min_ev and home_edge >= min_edge:
        opportunities.append(BetOpportunity(
            game_id=game['game_id'],
            bet_type="spread_home",
            team=f"{game['home_team']} {game['spread']:+.1f}",
            odds=game['spread_odds_home'],
            model_prob=home_cover_prob,
            fair_prob=home_fair,
            implied_prob=home_implied,
            ev=home_ev,
            ev_percent=home_ev * 100,
            edge=home_edge
        ))

    # Away spread
    away_edge = get_vig_adjusted_edge(
        away_cover_prob,
        game['spread_odds_away'],
        game['spread_odds_home'],
        vig_method
    )

    away_implied = american_to_probability(game['spread_odds_away'])
    away_fair = away_cover_prob - away_edge
    away_ev = calculate_ev_percentage(away_cover_prob, game['spread_odds_away'])

    if away_ev >= min_ev and away_edge >= min_edge:
        opportunities.append(BetOpportunity(
            game_id=game['game_id'],
            bet_type="spread_away",
            team=f"{game['away_team']} {-game['spread']:+.1f}",
            odds=game['spread_odds_away'],
            model_prob=away_cover_prob,
            fair_prob=away_fair,
            implied_prob=away_implied,
            ev=away_ev,
            ev_percent=away_ev * 100,
            edge=away_edge
        ))

    return opportunities


def find_ev_opportunities(
    game: Dict[str, Any],
    home_win_prob: float,
    home_cover_prob: Optional[float] = None,
    min_ev: float = 0.02,
    min_edge: float = 0.01,
    bet_types: List[BetType] = None,
    vig_method: str = "proportional"
) -> List[BetOpportunity]:
    """
    Find all positive EV opportunities for a game.

    This is the main entry point for EV detection.

    Args:
        game: Game data with FanDuel odds
        home_win_prob: Model's home win probability
        home_cover_prob: Model's home cover probability (optional)
        min_ev: Minimum EV percentage threshold (e.g., 0.02 = 2%)
        min_edge: Minimum probability edge threshold
        bet_types: List of bet types to check (default: all)
        vig_method: Vig removal method

    Returns:
        List of all positive EV betting opportunities,
        sorted by EV (highest first)
    """
    if bet_types is None:
        bet_types = ["moneyline_home", "moneyline_away"]
        if home_cover_prob is not None:
            bet_types.extend(["spread_home", "spread_away"])

    opportunities = []

    # Check moneylines
    if any(bt.startswith("moneyline") for bt in bet_types):
        away_win_prob = 1 - home_win_prob
        ml_opps = find_moneyline_opportunities(
            game, home_win_prob, away_win_prob,
            min_ev, min_edge, vig_method
        )
        opportunities.extend(ml_opps)

    # Check spreads
    if home_cover_prob is not None and any(bt.startswith("spread") for bt in bet_types):
        away_cover_prob = 1 - home_cover_prob
        spread_opps = find_spread_opportunities(
            game, home_cover_prob, away_cover_prob,
            min_ev, min_edge, vig_method
        )
        opportunities.extend(spread_opps)

    # Sort by EV (highest first)
    opportunities.sort(key=lambda x: x.ev, reverse=True)

    return opportunities


def estimate_spread_cover_prob(
    home_win_prob: float,
    spread: float,
    std_dev: float = 12.0
) -> float:
    """
    Estimate probability of covering spread given win probability.

    Uses a simple normal distribution model.
    Assumes margin of victory ~ Normal(expected_margin, std_dev)

    Args:
        home_win_prob: Probability home team wins
        spread: Point spread (home team perspective)
        std_dev: Standard deviation of point margins (default 12)

    Returns:
        Probability home team covers the spread

    Note:
        This is a rough approximation. More sophisticated models
        would use historical margin distributions or simulation.
    """
    from scipy import stats

    # Convert win probability to expected margin
    # (Very rough approximation)
    if home_win_prob > 0.5:
        expected_margin = (home_win_prob - 0.5) * 20  # Scale to ~10 point range
    else:
        expected_margin = (home_win_prob - 0.5) * 20

    # Probability of covering spread
    # P(actual_margin > spread) = P(Z > (spread - expected_margin) / std_dev)
    z_score = (spread - expected_margin) / std_dev
    cover_prob = 1 - stats.norm.cdf(z_score)

    return cover_prob
