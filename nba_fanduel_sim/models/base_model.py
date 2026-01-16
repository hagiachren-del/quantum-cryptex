"""
Base Model Interface

All probability models must implement this interface
to ensure compatibility with the backtesting system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd


class BaseModel(ABC):
    """
    Abstract base class for NBA win probability models.

    All models must implement:
    - fit(data): Train the model on historical data
    - predict_proba(game_row): Predict win probability for a single game

    Models must be designed for sequential backtesting:
    - No lookahead bias (only use data available before game time)
    - Support incremental updates
    """

    def __init__(self, name: str):
        """
        Initialize the model.

        Args:
            name: Human-readable name for the model
        """
        self.name = name
        self.is_fitted = False

    @abstractmethod
    def fit(self, data: List[Dict[str, Any]]) -> None:
        """
        Train the model on historical game data.

        This method should be called with chronologically sorted data.
        The model should learn patterns but avoid lookahead bias.

        Args:
            data: List of game dictionaries (merged games + odds)
                  Each dict should contain game outcomes and features

        Raises:
            ValueError: If data is invalid or insufficient
        """
        pass

    @abstractmethod
    def predict_proba(self, game_row: Dict[str, Any]) -> float:
        """
        Predict home team win probability for a single game.

        This should be called BEFORE the game outcome is known.
        Only use information available at game time.

        Args:
            game_row: Dictionary containing game features
                      Must include: home_team, away_team, date, etc.

        Returns:
            Probability that home team wins (between 0 and 1)

        Raises:
            ValueError: If model is not fitted
            KeyError: If required features are missing
        """
        pass

    def update(self, game_row: Dict[str, Any]) -> None:
        """
        Update the model after a game completes (optional).

        Some models (like Elo) update after each game.
        Others (like logistic regression) may only update periodically.

        Args:
            game_row: Completed game with outcome
        """
        pass

    def get_model_params(self) -> Dict[str, Any]:
        """
        Get model parameters for logging/debugging.

        Returns:
            Dictionary of model parameters and state
        """
        return {
            'name': self.name,
            'is_fitted': self.is_fitted,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class EnsembleModel(BaseModel):
    """
    Ensemble model that combines multiple base models.

    Averages predictions from multiple models, optionally weighted.

    Example:
        >>> elo = EloModel()
        >>> logreg = LogisticModel()
        >>> ensemble = EnsembleModel([elo, logreg], weights=[0.6, 0.4])
    """

    def __init__(
        self,
        models: List[BaseModel],
        weights: List[float] = None,
        name: str = "Ensemble"
    ):
        """
        Initialize ensemble model.

        Args:
            models: List of base models to combine
            weights: Optional weights for each model (default: equal weights)
            name: Name for this ensemble
        """
        super().__init__(name)
        self.models = models
        self.weights = weights or [1.0 / len(models)] * len(models)

        if len(self.weights) != len(self.models):
            raise ValueError("Number of weights must match number of models")

        if not abs(sum(self.weights) - 1.0) < 1e-6:
            raise ValueError("Weights must sum to 1.0")

    def fit(self, data: List[Dict[str, Any]]) -> None:
        """Fit all models in the ensemble."""
        for model in self.models:
            model.fit(data)
        self.is_fitted = True

    def predict_proba(self, game_row: Dict[str, Any]) -> float:
        """Predict using weighted average of all models."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        predictions = [model.predict_proba(game_row) for model in self.models]
        weighted_pred = sum(p * w for p, w in zip(predictions, self.weights))

        return weighted_pred

    def update(self, game_row: Dict[str, Any]) -> None:
        """Update all models in the ensemble."""
        for model in self.models:
            model.update(game_row)

    def get_model_params(self) -> Dict[str, Any]:
        """Get parameters for all models in ensemble."""
        return {
            'name': self.name,
            'is_fitted': self.is_fitted,
            'models': [m.get_model_params() for m in self.models],
            'weights': self.weights,
        }
