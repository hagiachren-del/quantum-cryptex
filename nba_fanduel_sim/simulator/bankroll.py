"""
Bankroll Management and Bet Tracking

Tracks betting history, bankroll changes, and enforces limits.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds import calculate_payout


@dataclass
class BetResult:
    """
    Represents the result of a placed bet.

    Attributes:
        bet_id: Unique identifier
        game_id: Game this bet is on
        date: Game date
        bet_type: Type of bet (moneyline_home, spread_away, etc.)
        team: Team bet on
        stake: Amount wagered
        odds: American odds
        won: Whether bet won (None if not yet settled)
        payout: Total payout if won (None if not settled)
        profit: Profit/loss (None if not settled)
        bankroll_before: Bankroll before bet was placed
        bankroll_after: Bankroll after bet settles (None if not settled)
    """
    bet_id: int
    game_id: str
    date: datetime
    bet_type: str
    team: str
    stake: float
    odds: float
    won: Optional[bool] = None
    payout: Optional[float] = None
    profit: Optional[float] = None
    bankroll_before: float = 0.0
    bankroll_after: Optional[float] = None
    model_prob: float = 0.0
    ev: float = 0.0

    def settle(self, won: bool) -> None:
        """
        Settle the bet with the outcome.

        Args:
            won: Whether the bet won
        """
        self.won = won

        if won:
            self.payout = calculate_payout(self.stake, self.odds)
            self.profit = self.payout - self.stake
            self.bankroll_after = self.bankroll_before + self.profit
        else:
            self.payout = 0.0
            self.profit = -self.stake
            self.bankroll_after = self.bankroll_before + self.profit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'bet_id': self.bet_id,
            'game_id': self.game_id,
            'date': self.date,
            'bet_type': self.bet_type,
            'team': self.team,
            'stake': self.stake,
            'odds': self.odds,
            'won': self.won,
            'payout': self.payout,
            'profit': self.profit,
            'bankroll_before': self.bankroll_before,
            'bankroll_after': self.bankroll_after,
            'model_prob': self.model_prob,
            'ev': self.ev,
        }


class Bankroll:
    """
    Manages betting bankroll with safety constraints.

    Tracks:
    - Current bankroll
    - Bet history
    - Peak bankroll
    - Drawdown
    - Daily/game exposure limits
    """

    def __init__(
        self,
        initial_bankroll: float,
        max_bet_percentage: float = 0.05,
        max_daily_bets: int = 10,
        max_game_exposure: float = 0.10,
        min_bankroll: float = 0.0
    ):
        """
        Initialize bankroll.

        Args:
            initial_bankroll: Starting bankroll in dollars
            max_bet_percentage: Max bet as % of bankroll (per bet)
            max_daily_bets: Max number of bets per day
            max_game_exposure: Max total exposure per game (as % of bankroll)
            min_bankroll: Minimum bankroll before stopping (default 0 = no limit)
        """
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.max_bet_percentage = max_bet_percentage
        self.max_daily_bets = max_daily_bets
        self.max_game_exposure = max_game_exposure
        self.min_bankroll = min_bankroll

        # Tracking
        self.bet_history: List[BetResult] = []
        self.peak_bankroll = initial_bankroll
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0

        # Daily tracking
        self.bets_today: Dict[str, int] = {}  # date -> count
        self.exposure_per_game: Dict[str, float] = {}  # game_id -> total stake

        self.next_bet_id = 1

    def can_place_bet(
        self,
        stake: float,
        game_id: str,
        date: datetime
    ) -> tuple[bool, str]:
        """
        Check if a bet is allowed given current constraints.

        Args:
            stake: Proposed bet size
            game_id: Game to bet on
            date: Game date

        Returns:
            (allowed, reason) - reason is empty string if allowed
        """
        # Check minimum bankroll
        if self.current_bankroll <= self.min_bankroll:
            return False, "Bankroll below minimum threshold"

        # Check if stake exceeds current bankroll
        if stake > self.current_bankroll:
            return False, f"Stake (${stake:.2f}) exceeds bankroll (${self.current_bankroll:.2f})"

        # Check bet percentage limit
        max_stake = self.current_bankroll * self.max_bet_percentage
        if stake > max_stake:
            return False, f"Stake (${stake:.2f}) exceeds max bet size (${max_stake:.2f})"

        # Check daily bet limit
        date_str = date.strftime('%Y-%m-%d')
        bets_today = self.bets_today.get(date_str, 0)
        if bets_today >= self.max_daily_bets:
            return False, f"Daily bet limit ({self.max_daily_bets}) reached"

        # Check per-game exposure
        current_exposure = self.exposure_per_game.get(game_id, 0.0)
        new_exposure = current_exposure + stake
        max_exposure = self.current_bankroll * self.max_game_exposure

        if new_exposure > max_exposure:
            return False, f"Game exposure (${new_exposure:.2f}) exceeds limit (${max_exposure:.2f})"

        return True, ""

    def place_bet(
        self,
        game_id: str,
        date: datetime,
        bet_type: str,
        team: str,
        stake: float,
        odds: float,
        model_prob: float = 0.0,
        ev: float = 0.0
    ) -> Optional[BetResult]:
        """
        Place a bet (reserve stake from bankroll).

        Args:
            game_id: Game identifier
            date: Game date
            bet_type: Type of bet
            team: Team being bet on
            stake: Amount to wager
            odds: American odds
            model_prob: Model's probability
            ev: Expected value

        Returns:
            BetResult object if bet placed, None if rejected
        """
        # Check if bet is allowed
        allowed, reason = self.can_place_bet(stake, game_id, date)

        if not allowed:
            # Bet rejected
            return None

        # Create bet result
        bet = BetResult(
            bet_id=self.next_bet_id,
            game_id=game_id,
            date=date,
            bet_type=bet_type,
            team=team,
            stake=stake,
            odds=odds,
            bankroll_before=self.current_bankroll,
            model_prob=model_prob,
            ev=ev
        )

        self.next_bet_id += 1

        # Update tracking
        date_str = date.strftime('%Y-%m-%d')
        self.bets_today[date_str] = self.bets_today.get(date_str, 0) + 1
        self.exposure_per_game[game_id] = self.exposure_per_game.get(game_id, 0.0) + stake

        # Add to history (unsettled)
        self.bet_history.append(bet)

        return bet

    def settle_bet(self, bet: BetResult, won: bool) -> None:
        """
        Settle a bet and update bankroll.

        Args:
            bet: The bet to settle
            won: Whether the bet won
        """
        # Settle the bet
        bet.settle(won)

        # Update current bankroll
        self.current_bankroll = bet.bankroll_after

        # Update peak and drawdown
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current bankroll statistics.

        Returns:
            Dictionary with performance metrics
        """
        settled_bets = [b for b in self.bet_history if b.won is not None]

        if not settled_bets:
            return {
                'initial_bankroll': self.initial_bankroll,
                'current_bankroll': self.current_bankroll,
                'total_bets': 0,
                'total_profit': 0.0,
                'roi': 0.0,
            }

        total_staked = sum(b.stake for b in settled_bets)
        total_profit = sum(b.profit for b in settled_bets)
        wins = sum(1 for b in settled_bets if b.won)

        return {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'peak_bankroll': self.peak_bankroll,
            'total_bets': len(settled_bets),
            'wins': wins,
            'losses': len(settled_bets) - wins,
            'win_rate': wins / len(settled_bets) if settled_bets else 0.0,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': total_profit / total_staked if total_staked > 0 else 0.0,
            'roi_percentage': (total_profit / total_staked * 100) if total_staked > 0 else 0.0,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'profit_factor': self._calculate_profit_factor(settled_bets),
        }

    def _calculate_profit_factor(self, bets: List[BetResult]) -> float:
        """
        Calculate profit factor (total wins / total losses).

        Args:
            bets: List of settled bets

        Returns:
            Profit factor (> 1.0 = profitable)
        """
        winning_bets = [b for b in bets if b.won]
        losing_bets = [b for b in bets if not b.won]

        total_wins = sum(b.profit for b in winning_bets)
        total_losses = abs(sum(b.profit for b in losing_bets))

        if total_losses == 0:
            return float('inf') if total_wins > 0 else 0.0

        return total_wins / total_losses

    def reset(self) -> None:
        """Reset bankroll to initial state."""
        self.current_bankroll = self.initial_bankroll
        self.bet_history = []
        self.peak_bankroll = self.initial_bankroll
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.bets_today = {}
        self.exposure_per_game = {}
        self.next_bet_id = 1

    def __repr__(self) -> str:
        return f"Bankroll(current=${self.current_bankroll:.2f}, bets={len(self.bet_history)})"
