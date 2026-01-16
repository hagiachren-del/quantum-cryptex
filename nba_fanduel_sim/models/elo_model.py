"""
Elo Rating Model for NBA

Implements team-level Elo ratings with home court advantage.
This is the primary model for the simulator.

Elo ratings are updated sequentially after each game,
making them ideal for chronological backtesting.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from .base_model import BaseModel


class EloModel(BaseModel):
    """
    Elo rating system for NBA teams.

    Features:
    - Team-specific Elo ratings (updated after each game)
    - Explicit home court advantage parameter
    - Configurable K-factor for update speed
    - Mean reversion between seasons

    The Elo formula:
        Expected Win Prob = 1 / (1 + 10^(-(rating_diff + home_advantage) / 400))

    References:
        - FiveThirtyEight NBA Elo: https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/
        - Standard Elo: https://en.wikipedia.org/wiki/Elo_rating_system
    """

    def __init__(
        self,
        k_factor: float = 20.0,
        home_advantage: float = 100.0,
        initial_rating: float = 1500.0,
        mean_reversion: float = 0.75,
        name: str = "Elo"
    ):
        """
        Initialize Elo model.

        Args:
            k_factor: How quickly ratings update (higher = more reactive)
                     Typical values: 16-32 for NBA
            home_advantage: Elo points added for home court
                          Typical value: 100 (equivalent to ~3 point spread)
            initial_rating: Starting Elo for all teams
            mean_reversion: How much ratings revert to mean between seasons
                          0.0 = no reversion, 1.0 = full reversion to initial
            name: Model name
        """
        super().__init__(name)
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.initial_rating = initial_rating
        self.mean_reversion = mean_reversion

        # Current ratings for each team
        self.ratings: Dict[str, float] = {}

        # Track rating history for analysis
        self.rating_history: List[Dict[str, Any]] = []

        # Track current season
        self.current_season: Optional[int] = None

    def fit(self, data: List[Dict[str, Any]]) -> None:
        """
        Initialize Elo ratings from historical data.

        This processes all historical games chronologically,
        updating ratings after each game.

        Args:
            data: Chronologically sorted list of games
        """
        if not data:
            raise ValueError("Cannot fit model with empty data")

        # Reset ratings
        self.ratings = {}
        self.rating_history = []
        self.current_season = None

        # Process all games chronologically
        for game in data:
            # Check for season change (apply mean reversion)
            if self.current_season is not None and game['season'] != self.current_season:
                self._apply_season_reversion()

            self.current_season = game['season']

            # Ensure both teams have ratings
            self._ensure_team_rating(game['home_team'])
            self._ensure_team_rating(game['away_team'])

            # Update ratings based on game outcome
            self.update(game)

        self.is_fitted = True

    def predict_proba(self, game_row: Dict[str, Any]) -> float:
        """
        Predict home team win probability using Elo ratings.

        Formula:
            win_prob = 1 / (1 + 10^(-(home_elo - away_elo + home_adv) / 400))

        Args:
            game_row: Game features including home_team, away_team

        Returns:
            Probability home team wins (0 to 1)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        home_team = game_row['home_team']
        away_team = game_row['away_team']

        # Ensure both teams have ratings (use initial if not)
        self._ensure_team_rating(home_team)
        self._ensure_team_rating(away_team)

        home_elo = self.ratings[home_team]
        away_elo = self.ratings[away_team]

        # Calculate expected win probability
        elo_diff = home_elo - away_elo + self.home_advantage
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))

        return win_prob

    def update(self, game_row: Dict[str, Any]) -> None:
        """
        Update Elo ratings after a game completes.

        New Elo = Old Elo + K * (Actual - Expected)

        Args:
            game_row: Completed game with outcome
        """
        home_team = game_row['home_team']
        away_team = game_row['away_team']

        # Get current ratings
        home_elo = self.ratings.get(home_team, self.initial_rating)
        away_elo = self.ratings.get(away_team, self.initial_rating)

        # Calculate expected win probability (before game)
        elo_diff = home_elo - away_elo + self.home_advantage
        expected_home_win = 1 / (1 + 10 ** (-elo_diff / 400))

        # Actual outcome (1 if home won, 0 if away won)
        actual_home_win = 1.0 if game_row['home_won'] else 0.0

        # Margin of victory multiplier (optional enhancement)
        mov_multiplier = self._get_mov_multiplier(game_row['margin'], elo_diff)

        # Update ratings
        rating_change = self.k_factor * mov_multiplier * (actual_home_win - expected_home_win)
        self.ratings[home_team] = home_elo + rating_change
        self.ratings[away_team] = away_elo - rating_change

        # Record rating change
        self.rating_history.append({
            'date': game_row['date'],
            'game_id': game_row['game_id'],
            'home_team': home_team,
            'away_team': away_team,
            'home_elo_before': home_elo,
            'away_elo_before': away_elo,
            'home_elo_after': self.ratings[home_team],
            'away_elo_after': self.ratings[away_team],
            'expected_home_win': expected_home_win,
            'actual_home_win': actual_home_win,
            'margin': game_row['margin'],
        })

    def _ensure_team_rating(self, team: str) -> None:
        """Ensure a team has an Elo rating (initialize if not)."""
        if team not in self.ratings:
            self.ratings[team] = self.initial_rating

    def _get_mov_multiplier(self, margin: int, elo_diff: float) -> float:
        """
        Calculate margin of victory multiplier.

        Larger blowouts count for more, but less so if the favorite wins big.
        This follows the FiveThirtyEight approach.

        Args:
            margin: Home team margin (positive if home won)
            elo_diff: Home Elo - Away Elo (before home advantage added)

        Returns:
            Multiplier between 0.5 and ~3.0
        """
        # Base multiplier from margin
        mov_mult = np.log(max(1, abs(margin)) + 1)

        # Reduce multiplier if the favorite won by a lot
        # (this prevents ratings from exploding when good teams crush bad teams)
        if (margin > 0 and elo_diff > 0) or (margin < 0 and elo_diff < 0):
            # Favorite won
            mov_mult *= 0.8

        return mov_mult

    def _apply_season_reversion(self) -> None:
        """
        Apply mean reversion between seasons.

        All ratings move toward the mean (initial_rating).
        This accounts for roster changes, coaching changes, etc.
        """
        for team in self.ratings:
            current = self.ratings[team]
            self.ratings[team] = (
                self.mean_reversion * self.initial_rating +
                (1 - self.mean_reversion) * current
            )

    def get_current_ratings(self) -> Dict[str, float]:
        """
        Get current Elo ratings for all teams.

        Returns:
            Dictionary mapping team -> current Elo rating
        """
        return self.ratings.copy()

    def get_team_rating(self, team: str) -> float:
        """
        Get current Elo rating for a specific team.

        Args:
            team: Team abbreviation

        Returns:
            Current Elo rating (or initial rating if team not found)
        """
        return self.ratings.get(team, self.initial_rating)

    def elo_to_spread(self, elo_diff: float) -> float:
        """
        Convert Elo difference to approximate point spread.

        Rule of thumb: 25 Elo points ≈ 1 point spread

        Args:
            elo_diff: Home Elo - Away Elo + Home Advantage

        Returns:
            Approximate point spread (home team perspective)
        """
        return elo_diff / 25.0

    def spread_to_elo(self, spread: float) -> float:
        """
        Convert point spread to approximate Elo difference.

        Args:
            spread: Point spread (home team perspective)

        Returns:
            Approximate Elo difference
        """
        return spread * 25.0

    def get_model_params(self) -> Dict[str, Any]:
        """Get model parameters and current state."""
        params = super().get_model_params()
        params.update({
            'k_factor': self.k_factor,
            'home_advantage': self.home_advantage,
            'initial_rating': self.initial_rating,
            'mean_reversion': self.mean_reversion,
            'num_teams': len(self.ratings),
            'current_season': self.current_season,
        })
        return params

    def __repr__(self) -> str:
        return (
            f"EloModel(k={self.k_factor}, home_adv={self.home_advantage}, "
            f"teams={len(self.ratings)})"
        )
