"""
Backtesting Engine for NBA Betting Strategies

Processes games chronologically, places bets, and tracks performance.
Prevents data leakage and enforces FanDuel-realistic constraints.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import BaseModel
from strategy import find_ev_opportunities, calculate_stake, BetSizingMethod
from simulator.bankroll import Bankroll, BetResult


@dataclass
class BacktestConfig:
    """
    Configuration for backtesting.

    All parameters that control the backtest behavior.
    """
    # Model
    model: BaseModel

    # Bankroll
    initial_bankroll: float = 10000.0
    max_bet_percentage: float = 0.05
    max_daily_bets: int = 10
    max_game_exposure: float = 0.10

    # Strategy
    min_ev: float = 0.02  # 2% minimum EV
    min_edge: float = 0.01  # 1% minimum edge
    bet_sizing_method: BetSizingMethod = "fractional_kelly"
    kelly_fraction: float = 0.25
    flat_percentage: float = 0.01

    # FanDuel constraints
    min_bet_amount: float = 10.0
    max_bet_amount: Optional[float] = None
    vig_method: str = "proportional"

    # Execution
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None
    seasons: Optional[List[int]] = None

    def __repr__(self) -> str:
        return (
            f"BacktestConfig(model={self.model.name}, "
            f"bankroll=${self.initial_bankroll}, "
            f"method={self.bet_sizing_method})"
        )


class Backtester:
    """
    Main backtesting engine.

    Processes games chronologically, identifies +EV opportunities,
    sizes bets, and tracks performance.
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize backtester.

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.model = config.model

        # Initialize bankroll
        self.bankroll = Bankroll(
            initial_bankroll=config.initial_bankroll,
            max_bet_percentage=config.max_bet_percentage,
            max_daily_bets=config.max_daily_bets,
            max_game_exposure=config.max_game_exposure
        )

        # Results tracking
        self.games_processed = 0
        self.bets_attempted = 0
        self.bets_placed = 0
        self.bets_rejected = 0

    def run(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run backtest on historical games.

        This is the main entry point for backtesting.

        Args:
            games: List of games (chronologically sorted) with outcomes and odds

        Returns:
            Dictionary with backtest results and performance metrics
        """
        # Reset state
        self.bankroll.reset()
        self.games_processed = 0
        self.bets_attempted = 0
        self.bets_placed = 0
        self.bets_rejected = 0

        # Filter games by date/season if specified
        games = self._filter_games(games)

        if not games:
            raise ValueError("No games to backtest after filtering")

        # Fit model on initial training data
        print(f"Fitting model on {len(games)} games...")
        self.model.fit(games)

        # Process each game chronologically
        print(f"Running backtest...")
        for i, game in enumerate(games):
            self._process_game(game)
            self.games_processed += 1

            # Progress update
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(games)} games...")

        # Generate results
        results = self._generate_results()

        print(f"\nBacktest complete!")
        print(f"Games processed: {self.games_processed}")
        print(f"Bets placed: {self.bets_placed}")
        print(f"Final bankroll: ${self.bankroll.current_bankroll:.2f}")

        return results

    def _process_game(self, game: Dict[str, Any]) -> None:
        """
        Process a single game: predict, find +EV, place bets, settle.

        Args:
            game: Game data with outcome and FanDuel odds
        """
        # 1. Get model prediction (before game outcome is known)
        try:
            home_win_prob = self.model.predict_proba(game)
        except Exception as e:
            print(f"Warning: Model prediction failed for game {game['game_id']}: {e}")
            return

        # 2. Find +EV opportunities
        opportunities = find_ev_opportunities(
            game=game,
            home_win_prob=home_win_prob,
            min_ev=self.config.min_ev,
            min_edge=self.config.min_edge,
            vig_method=self.config.vig_method
        )

        # 3. Place bets for each opportunity
        for opp in opportunities:
            self._place_bet_for_opportunity(game, opp)

        # 4. Update model with game outcome
        self.model.update(game)

    def _place_bet_for_opportunity(
        self,
        game: Dict[str, Any],
        opp: Any  # BetOpportunity
    ) -> None:
        """
        Attempt to place a bet for an opportunity.

        Args:
            game: Game data
            opp: BetOpportunity object
        """
        self.bets_attempted += 1

        # Calculate stake size
        stake = calculate_stake(
            probability=opp.model_prob,
            american_odds=opp.odds,
            bankroll=self.bankroll.current_bankroll,
            method=self.config.bet_sizing_method,
            kelly_fraction=self.config.kelly_fraction,
            flat_percentage=self.config.flat_percentage,
            max_bet_percentage=self.config.max_bet_percentage,
            min_bet_amount=self.config.min_bet_amount,
            max_bet_amount=self.config.max_bet_amount
        )

        # Skip if stake is 0 (below minimum)
        if stake == 0:
            self.bets_rejected += 1
            return

        # Attempt to place bet
        bet = self.bankroll.place_bet(
            game_id=game['game_id'],
            date=game['date'],
            bet_type=opp.bet_type,
            team=opp.team,
            stake=stake,
            odds=opp.odds,
            model_prob=opp.model_prob,
            ev=opp.ev
        )

        if bet is None:
            # Bet rejected by bankroll constraints
            self.bets_rejected += 1
            return

        # Bet placed successfully
        self.bets_placed += 1

        # Settle bet based on game outcome
        won = self._determine_bet_outcome(game, opp.bet_type)
        self.bankroll.settle_bet(bet, won)

    def _determine_bet_outcome(
        self,
        game: Dict[str, Any],
        bet_type: str
    ) -> bool:
        """
        Determine if a bet won based on game outcome.

        Args:
            game: Game data with final score
            bet_type: Type of bet placed

        Returns:
            True if bet won, False otherwise
        """
        if bet_type == "moneyline_home":
            return game['home_won']
        elif bet_type == "moneyline_away":
            return not game['home_won']
        elif bet_type == "spread_home":
            # Home covers if: (home_score + spread) > away_score
            # Which is: home_score - away_score > -spread
            # Which is: margin > -spread
            return game['margin'] > -game['spread']
        elif bet_type == "spread_away":
            # Away covers if: away_score + (-spread) > home_score
            # Which is: away_score - home_score > spread
            # Which is: -margin > spread
            return -game['margin'] > game['spread']
        else:
            raise ValueError(f"Unknown bet type: {bet_type}")

    def _filter_games(
        self,
        games: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter games by date range or seasons.

        Args:
            games: All games

        Returns:
            Filtered games
        """
        filtered = games

        # Filter by date
        if self.config.start_date:
            start = pd.to_datetime(self.config.start_date)
            filtered = [g for g in filtered if g['date'] >= start]

        if self.config.end_date:
            end = pd.to_datetime(self.config.end_date)
            filtered = [g for g in filtered if g['date'] <= end]

        # Filter by seasons
        if self.config.seasons:
            filtered = [g for g in filtered if g['season'] in self.config.seasons]

        return filtered

    def _generate_results(self) -> Dict[str, Any]:
        """
        Generate comprehensive backtest results.

        Returns:
            Dictionary with all performance metrics
        """
        bankroll_stats = self.bankroll.get_stats()

        results = {
            # Backtest metadata
            'config': {
                'model': self.model.name,
                'initial_bankroll': self.config.initial_bankroll,
                'bet_sizing_method': self.config.bet_sizing_method,
                'min_ev': self.config.min_ev,
                'kelly_fraction': self.config.kelly_fraction,
            },

            # Game stats
            'games_processed': self.games_processed,

            # Bet stats
            'bets_attempted': self.bets_attempted,
            'bets_placed': self.bets_placed,
            'bets_rejected': self.bets_rejected,
            'bet_rate': self.bets_placed / self.games_processed if self.games_processed > 0 else 0,

            # Bankroll stats
            'bankroll': bankroll_stats,

            # Bet history
            'bet_history': [b.to_dict() for b in self.bankroll.bet_history],
        }

        return results

    def save_results(
        self,
        results: Dict[str, Any],
        output_path: Path
    ) -> None:
        """
        Save backtest results to files.

        Args:
            results: Backtest results dictionary
            output_path: Directory to save results
        """
        output_path.mkdir(parents=True, exist_ok=True)

        # Save bet history as CSV
        if results['bet_history']:
            bet_df = pd.DataFrame(results['bet_history'])
            bet_df.to_csv(output_path / 'bet_history.csv', index=False)

        # Save summary stats as JSON
        import json

        summary = {k: v for k, v in results.items() if k != 'bet_history'}

        # Convert non-serializable types
        summary_json = json.dumps(summary, indent=2, default=str)

        with open(output_path / 'summary.json', 'w') as f:
            f.write(summary_json)

        print(f"Results saved to {output_path}/")

    def get_bankroll_curve(self) -> pd.DataFrame:
        """
        Get bankroll over time as DataFrame.

        Returns:
            DataFrame with columns: bet_id, date, bankroll
        """
        settled_bets = [b for b in self.bankroll.bet_history if b.won is not None]

        data = [{
            'bet_id': b.bet_id,
            'date': b.date,
            'bankroll': b.bankroll_after
        } for b in settled_bets]

        return pd.DataFrame(data)

    def __repr__(self) -> str:
        return (
            f"Backtester(model={self.model.name}, "
            f"bankroll=${self.bankroll.current_bankroll:.2f})"
        )
