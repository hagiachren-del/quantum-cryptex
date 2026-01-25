"""
Bet Tracking System

Logs all bet recommendations and their outcomes for performance analysis.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class BetOutcome(Enum):
    """Possible bet outcomes"""
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class BetRecord:
    """Single bet record with all relevant information"""

    # Identification
    bet_id: str
    timestamp: str

    # Game information
    home_team: str
    away_team: str
    game_date: str

    # Bet details
    bet_type: str  # 'moneyline', 'spread', 'total_over', 'total_under'
    team: str  # Team bet on (or 'over'/'under' for totals)
    odds: int  # American odds

    # Optional fields with defaults
    quarter: Optional[int] = None  # None for full game, 1-4 for quarters
    line: float = 0.0  # Spread or total line

    # Model predictions
    model_prob: float = 0.0  # Model's probability
    market_prob: float = 0.0  # Market implied probability
    edge: float = 0.0  # Model edge over market
    ev_percentage: float = 0.0  # Expected value percentage
    adjusted_ev: float = 0.0  # EV after reality checks

    # Bet sizing
    stake: float = 100.0
    recommended_stake: float = 0.0  # Kelly-based recommendation

    # Outcome
    outcome: str = BetOutcome.PENDING.value
    actual_result: Optional[str] = None  # Actual game result
    profit: float = 0.0

    # Metadata
    notes: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'BetRecord':
        """Create BetRecord from dictionary"""
        return cls(**data)


class BetTracker:
    """
    Tracks all bet recommendations and outcomes.

    Stores data in JSON file for persistence.
    """

    def __init__(self, data_file: str = "bet_history.json"):
        """
        Initialize bet tracker.

        Args:
            data_file: Path to JSON file for storing bet history
        """
        self.data_file = data_file
        self.bets: List[BetRecord] = []
        self._load_history()

    def _load_history(self):
        """Load bet history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.bets = [BetRecord.from_dict(bet) for bet in data]
                print(f"Loaded {len(self.bets)} historical bets from {self.data_file}")
            except Exception as e:
                print(f"Warning: Could not load bet history: {e}")
                self.bets = []
        else:
            print(f"No existing bet history found. Starting fresh.")
            self.bets = []

    def _save_history(self):
        """Save bet history to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([bet.to_dict() for bet in self.bets], f, indent=2)
        except Exception as e:
            print(f"Error saving bet history: {e}")

    def add_bet(self, bet: BetRecord) -> str:
        """
        Add a new bet to tracking.

        Args:
            bet: BetRecord to add

        Returns:
            bet_id of the added bet
        """
        # Generate bet_id if not provided
        if not bet.bet_id:
            bet.bet_id = f"BET_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.bets)}"

        self.bets.append(bet)
        self._save_history()

        return bet.bet_id

    def update_bet_outcome(self, bet_id: str, outcome: BetOutcome,
                          actual_result: Optional[str] = None,
                          profit: Optional[float] = None) -> bool:
        """
        Update a bet's outcome.

        Args:
            bet_id: ID of bet to update
            outcome: BetOutcome (WIN, LOSS, PUSH, etc.)
            actual_result: Description of actual game result
            profit: Actual profit/loss (calculated if not provided)

        Returns:
            True if bet was found and updated, False otherwise
        """
        for bet in self.bets:
            if bet.bet_id == bet_id:
                bet.outcome = outcome.value
                bet.actual_result = actual_result

                # Calculate profit if not provided
                if profit is not None:
                    bet.profit = profit
                elif outcome == BetOutcome.WIN:
                    # Calculate based on odds
                    if bet.odds > 0:
                        bet.profit = bet.stake * (bet.odds / 100)
                    else:
                        bet.profit = bet.stake * (100 / abs(bet.odds))
                elif outcome == BetOutcome.LOSS:
                    bet.profit = -bet.stake
                else:  # PUSH or CANCELLED
                    bet.profit = 0.0

                self._save_history()
                return True

        return False

    def get_bet(self, bet_id: str) -> Optional[BetRecord]:
        """Get a specific bet by ID"""
        for bet in self.bets:
            if bet.bet_id == bet_id:
                return bet
        return None

    def get_pending_bets(self) -> List[BetRecord]:
        """Get all pending bets"""
        return [bet for bet in self.bets if bet.outcome == BetOutcome.PENDING.value]

    def get_settled_bets(self) -> List[BetRecord]:
        """Get all settled bets (win/loss/push)"""
        return [bet for bet in self.bets
                if bet.outcome in [BetOutcome.WIN.value, BetOutcome.LOSS.value, BetOutcome.PUSH.value]]

    def get_bets_by_date(self, start_date: str, end_date: Optional[str] = None) -> List[BetRecord]:
        """
        Get bets within a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to start_date)

        Returns:
            List of bets in date range
        """
        if end_date is None:
            end_date = start_date

        return [bet for bet in self.bets
                if start_date <= bet.game_date <= end_date]

    def get_bets_by_type(self, bet_type: str) -> List[BetRecord]:
        """Get all bets of a specific type"""
        return [bet for bet in self.bets if bet.bet_type == bet_type]

    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics of all tracked bets.

        Returns:
            Dictionary with win rate, ROI, etc.
        """
        settled = self.get_settled_bets()

        if not settled:
            return {
                'total_bets': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'roi': 0.0
            }

        wins = sum(1 for bet in settled if bet.outcome == BetOutcome.WIN.value)
        losses = sum(1 for bet in settled if bet.outcome == BetOutcome.LOSS.value)
        pushes = sum(1 for bet in settled if bet.outcome == BetOutcome.PUSH.value)

        total_profit = sum(bet.profit for bet in settled)
        total_staked = sum(bet.stake for bet in settled)

        win_rate = wins / len(settled) if settled else 0.0
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0.0

        return {
            'total_bets': len(settled),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': roi,
            'average_odds': sum(bet.odds for bet in settled) / len(settled) if settled else 0,
            'average_edge': sum(bet.edge for bet in settled) / len(settled) if settled else 0,
            'pending_bets': len(self.get_pending_bets())
        }

    def export_to_csv(self, filename: str = "bet_history.csv"):
        """Export bet history to CSV file"""
        import csv

        if not self.bets:
            print("No bets to export")
            return

        with open(filename, 'w', newline='') as f:
            # Get all field names from first bet
            fieldnames = list(self.bets[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for bet in self.bets:
                writer.writerow(bet.to_dict())

        print(f"Exported {len(self.bets)} bets to {filename}")


if __name__ == "__main__":
    # Example usage
    tracker = BetTracker()

    # Add a bet
    bet = BetRecord(
        bet_id="",
        timestamp=datetime.now().isoformat(),
        home_team="Kings",
        away_team="Wizards",
        game_date="2026-01-17",
        bet_type="spread",
        team="Kings",
        odds=-110,
        line=-7.0,
        model_prob=0.65,
        market_prob=0.52,
        edge=0.13,
        ev_percentage=15.2,
        adjusted_ev=10.5,
        stake=100
    )

    bet_id = tracker.add_bet(bet)
    print(f"Added bet: {bet_id}")

    # Update outcome
    tracker.update_bet_outcome(bet_id, BetOutcome.WIN, "Kings won 115-102")

    # Get stats
    stats = tracker.get_summary_stats()
    print(f"Win rate: {stats['win_rate']*100:.1f}%")
    print(f"ROI: {stats['roi']:.1f}%")
