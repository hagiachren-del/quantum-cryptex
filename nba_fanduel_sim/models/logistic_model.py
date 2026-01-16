"""
Logistic Regression Model for NBA

Uses team features and Elo ratings to predict game outcomes.
Trained only on past data during backtests to prevent lookahead bias.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from .base_model import BaseModel


class LogisticModel(BaseModel):
    """
    Logistic regression model for NBA game prediction.

    Features:
    - Elo difference
    - Rest differential
    - Home indicator
    - Optional: Season, playoff flag, etc.

    The model is retrained periodically during backtesting
    to avoid lookahead bias.
    """

    def __init__(
        self,
        retrain_frequency: int = 100,
        min_training_games: int = 200,
        name: str = "Logistic"
    ):
        """
        Initialize logistic regression model.

        Args:
            retrain_frequency: Retrain every N games during backtesting
            min_training_games: Minimum games needed before first training
            name: Model name
        """
        super().__init__(name)
        self.retrain_frequency = retrain_frequency
        self.min_training_games = min_training_games

        # Sklearn models
        self.model: Optional[LogisticRegression] = None
        self.scaler: Optional[StandardScaler] = None

        # Training data buffer
        self.training_data: List[Dict[str, Any]] = []
        self.games_since_retrain = 0

        # Track which features to use
        self.feature_names = [
            'elo_diff',
            'rest_diff',
            'is_home',
            'is_playoff',
        ]

    def fit(self, data: List[Dict[str, Any]]) -> None:
        """
        Initial fit on historical data.

        For backtesting, this trains on the first min_training_games,
        then retrains periodically.

        Args:
            data: List of historical games (chronologically sorted)
        """
        if len(data) < self.min_training_games:
            raise ValueError(
                f"Need at least {self.min_training_games} games for training, "
                f"got {len(data)}"
            )

        # Store all data for potential retraining
        self.training_data = data[:self.min_training_games]

        # Train initial model
        self._train_model()

        self.is_fitted = True

    def predict_proba(self, game_row: Dict[str, Any]) -> float:
        """
        Predict home team win probability.

        Args:
            game_row: Game features

        Returns:
            Probability home team wins
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Model must be fitted before prediction")

        # Extract features
        features = self._extract_features(game_row)

        # Scale features
        features_scaled = self.scaler.transform([features])

        # Predict probability
        prob = self.model.predict_proba(features_scaled)[0][1]

        return prob

    def update(self, game_row: Dict[str, Any]) -> None:
        """
        Add game to training buffer and retrain if needed.

        Args:
            game_row: Completed game
        """
        # Add to training data
        self.training_data.append(game_row)
        self.games_since_retrain += 1

        # Retrain if frequency threshold reached
        if self.games_since_retrain >= self.retrain_frequency:
            self._train_model()
            self.games_since_retrain = 0

    def _extract_features(self, game_row: Dict[str, Any]) -> List[float]:
        """
        Extract feature vector from game data.

        Features:
        - elo_diff: Home Elo - Away Elo (requires Elo ratings in game_row)
        - rest_diff: Home rest days - Away rest days
        - is_home: Always 1 (home team perspective)
        - is_playoff: 1 if playoff game, 0 otherwise

        Args:
            game_row: Game data

        Returns:
            List of feature values
        """
        features = []

        # Elo difference (if available, otherwise use 0)
        if 'home_elo' in game_row and 'away_elo' in game_row:
            elo_diff = game_row['home_elo'] - game_row['away_elo']
        else:
            elo_diff = 0.0

        features.append(elo_diff)

        # Rest differential
        rest_diff = game_row.get('home_rest_days', 0) - game_row.get('away_rest_days', 0)
        features.append(rest_diff)

        # Is home (always 1 from home team perspective)
        features.append(1.0)

        # Is playoff
        features.append(1.0 if game_row.get('is_playoff', False) else 0.0)

        return features

    def _train_model(self) -> None:
        """
        Train logistic regression on current training data.
        """
        # Extract features and labels
        X = []
        y = []

        for game in self.training_data:
            features = self._extract_features(game)
            label = 1 if game['home_won'] else 0

            X.append(features)
            y.append(label)

        X = np.array(X)
        y = np.array(y)

        # Fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train logistic regression
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            solver='lbfgs'
        )
        self.model.fit(X_scaled, y)

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance (coefficients).

        Returns:
            Dictionary mapping feature name -> coefficient
        """
        if self.model is None:
            return {}

        coefficients = self.model.coef_[0]
        return dict(zip(self.feature_names, coefficients))

    def get_model_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        params = super().get_model_params()
        params.update({
            'retrain_frequency': self.retrain_frequency,
            'min_training_games': self.min_training_games,
            'training_games': len(self.training_data),
            'games_since_retrain': self.games_since_retrain,
            'feature_importance': self.get_feature_importance(),
        })
        return params


class LogisticWithEloModel(BaseModel):
    """
    Hybrid model that combines Elo model with logistic regression.

    The Elo model provides base ratings, and logistic regression
    learns adjustments based on additional features.

    This is a convenience class that maintains an Elo model internally
    and uses its ratings as features for logistic regression.
    """

    def __init__(
        self,
        elo_k_factor: float = 20.0,
        elo_home_advantage: float = 100.0,
        retrain_frequency: int = 100,
        name: str = "LogisticWithElo"
    ):
        """
        Initialize hybrid model.

        Args:
            elo_k_factor: K-factor for internal Elo model
            elo_home_advantage: Home advantage for Elo model
            retrain_frequency: How often to retrain logistic model
            name: Model name
        """
        super().__init__(name)

        # Import here to avoid circular dependency
        from .elo_model import EloModel

        self.elo_model = EloModel(
            k_factor=elo_k_factor,
            home_advantage=elo_home_advantage,
            name="Internal-Elo"
        )
        self.logistic_model = LogisticModel(
            retrain_frequency=retrain_frequency,
            name="Internal-Logistic"
        )

    def fit(self, data: List[Dict[str, Any]]) -> None:
        """
        Fit both Elo and logistic models.

        First fits Elo on all data, then enriches data with Elo ratings
        and trains logistic regression.
        """
        # Fit Elo model
        self.elo_model.fit(data)

        # Enrich data with Elo ratings
        enriched_data = []
        for game in data:
            game_copy = game.copy()

            # Add Elo ratings at time of game
            # (Look them up from Elo model's history or recompute)
            home_elo = self.elo_model.get_team_rating(game['home_team'])
            away_elo = self.elo_model.get_team_rating(game['away_team'])

            game_copy['home_elo'] = home_elo
            game_copy['away_elo'] = away_elo

            enriched_data.append(game_copy)

        # Fit logistic model
        self.logistic_model.fit(enriched_data)

        self.is_fitted = True

    def predict_proba(self, game_row: Dict[str, Any]) -> float:
        """
        Predict using logistic model with Elo features.
        """
        # Enrich game row with current Elo ratings
        game_copy = game_row.copy()
        game_copy['home_elo'] = self.elo_model.get_team_rating(game_row['home_team'])
        game_copy['away_elo'] = self.elo_model.get_team_rating(game_row['away_team'])

        return self.logistic_model.predict_proba(game_copy)

    def update(self, game_row: Dict[str, Any]) -> None:
        """Update both models."""
        # Enrich with Elo before updating logistic
        game_copy = game_row.copy()
        game_copy['home_elo'] = self.elo_model.get_team_rating(game_row['home_team'])
        game_copy['away_elo'] = self.elo_model.get_team_rating(game_row['away_team'])

        self.logistic_model.update(game_copy)

        # Update Elo AFTER logistic (so next game has updated ratings)
        self.elo_model.update(game_row)

    def get_model_params(self) -> Dict[str, Any]:
        """Get parameters from both models."""
        params = super().get_model_params()
        params.update({
            'elo_params': self.elo_model.get_model_params(),
            'logistic_params': self.logistic_model.get_model_params(),
        })
        return params
