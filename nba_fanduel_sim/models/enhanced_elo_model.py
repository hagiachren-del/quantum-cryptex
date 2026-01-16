"""
Enhanced Elo Model with Injury Adjustments and Recent Form

Addresses Model Limitations:
- Incorporates injury impact (star player out, role player out)
- Recent form adjustments (hot/cold streaks)
- Home court advantage variations
- Rest/fatigue factors
- Back-to-back game penalties
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class InjuryImpact:
    """Represents impact of injured player."""
    player_name: str
    position: str
    impact_level: str  # 'star', 'starter', 'rotation', 'bench'
    elo_adjustment: float  # Points to subtract from team Elo


@dataclass
class TeamForm:
    """Recent team performance metrics."""
    last_5_record: Tuple[int, int]  # (wins, losses)
    last_10_record: Tuple[int, int]
    point_diff_l5: float  # Average point differential last 5
    point_diff_l10: float
    streak: int  # Positive for win streak, negative for loss streak


class EnhancedEloModel:
    """
    Advanced Elo model with multiple adjustment factors.

    Improvements over basic Elo:
    1. Injury adjustments based on player impact
    2. Recent form (hot/cold streak adjustments)
    3. Rest/fatigue factors (back-to-backs, travel)
    4. Home court advantage variations
    5. Playoff mode adjustments
    """

    def __init__(
        self,
        k_factor: float = 20.0,
        home_advantage: float = 100.0,
        regression_factor: float = 0.25,
        form_weight: float = 0.15,
        injury_weight: float = 1.0
    ):
        """
        Initialize enhanced Elo model.

        Args:
            k_factor: Elo update rate
            home_advantage: Base home court advantage (Elo points)
            regression_factor: Off-season mean reversion
            form_weight: Weight for recent form adjustments (0-1)
            injury_weight: Weight for injury adjustments (0-1)
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.regression_factor = regression_factor
        self.form_weight = form_weight
        self.injury_weight = injury_weight

        # Team ratings
        self.ratings: Dict[str, float] = {}
        self.default_rating = 1500.0

        # Team form tracking
        self.team_form: Dict[str, TeamForm] = {}

        # Recent games for form calculation
        self.recent_games: Dict[str, List[Dict]] = {}

        # Injury data
        self.injuries: Dict[str, List[InjuryImpact]] = {}

    def get_rating(self, team: str) -> float:
        """Get current Elo rating for team."""
        return self.ratings.get(team, self.default_rating)

    def set_rating(self, team: str, rating: float) -> None:
        """Set Elo rating for team."""
        self.ratings[team] = rating

    def calculate_injury_adjustment(self, team: str) -> float:
        """
        Calculate Elo adjustment for team injuries.

        Star player: -50 to -80 Elo
        Starter: -20 to -40 Elo
        Rotation: -5 to -15 Elo
        Bench: -0 to -5 Elo

        Returns:
            Total Elo points to subtract
        """
        if team not in self.injuries:
            return 0.0

        total_adjustment = 0.0

        for injury in self.injuries[team]:
            total_adjustment += injury.elo_adjustment

        return total_adjustment * self.injury_weight

    def calculate_form_adjustment(self, team: str) -> float:
        """
        Calculate Elo adjustment based on recent form.

        Hot streak (4+ wins): +20 to +40 Elo
        Cold streak (4+ losses): -20 to -40 Elo
        Moderate: -10 to +10 Elo

        Returns:
            Elo adjustment based on form
        """
        if team not in self.team_form:
            return 0.0

        form = self.team_form[team]

        # Streak-based adjustment
        streak_adj = 0.0
        if abs(form.streak) >= 4:
            # Strong streak
            streak_adj = min(40, abs(form.streak) * 8) * (1 if form.streak > 0 else -1)
        elif abs(form.streak) >= 2:
            # Moderate streak
            streak_adj = min(20, abs(form.streak) * 5) * (1 if form.streak > 0 else -1)

        # Point differential adjustment
        diff_adj = 0.0
        if abs(form.point_diff_l5) > 10:
            diff_adj = min(30, form.point_diff_l5 * 2)

        # Combine (weighted average)
        total_adj = (streak_adj * 0.6 + diff_adj * 0.4) * self.form_weight

        return total_adj

    def calculate_rest_adjustment(
        self,
        team: str,
        days_rest: int,
        is_back_to_back: bool = False,
        travel_distance: float = 0.0
    ) -> float:
        """
        Calculate Elo adjustment for rest and fatigue.

        Back-to-back: -30 to -50 Elo
        1 day rest: -10 to -20 Elo
        2 days rest: 0 Elo (normal)
        3+ days rest: +5 to +10 Elo (but can get rusty)
        Long travel (>2000 miles): -5 to -15 Elo

        Returns:
            Elo adjustment for rest/fatigue
        """
        adjustment = 0.0

        # Back-to-back penalty
        if is_back_to_back:
            adjustment -= 40

        # Rest days
        if days_rest == 0:
            adjustment -= 30
        elif days_rest == 1:
            adjustment -= 15
        elif days_rest >= 3:
            adjustment += 7

        # Travel fatigue
        if travel_distance > 2000:
            adjustment -= 10
        elif travel_distance > 1000:
            adjustment -= 5

        return adjustment

    def calculate_home_advantage(
        self,
        home_team: str,
        is_playoff: bool = False
    ) -> float:
        """
        Calculate context-specific home court advantage.

        Regular season: 100 Elo (baseline)
        Playoffs: 120 Elo (more intense)
        Elite home teams: +10 to +20 Elo bonus
        Poor home teams: -10 to -20 Elo penalty

        Returns:
            Home court advantage in Elo points
        """
        base_advantage = self.home_advantage

        # Playoff boost
        if is_playoff:
            base_advantage *= 1.2

        # Team-specific home court (would need historical data)
        # For now, use simplified version
        # Elite home teams: GSW, BOS, DEN, etc.
        elite_home = ['Golden State Warriors', 'Boston Celtics', 'Denver Nuggets',
                      'Miami Heat', 'Milwaukee Bucks']
        if home_team in elite_home:
            base_advantage += 15

        return base_advantage

    def predict_win_probability(
        self,
        home_team: str,
        away_team: str,
        home_injuries: List[InjuryImpact] = None,
        away_injuries: List[InjuryImpact] = None,
        home_rest_days: int = 2,
        away_rest_days: int = 2,
        home_back_to_back: bool = False,
        away_back_to_back: bool = False,
        is_playoff: bool = False
    ) -> float:
        """
        Predict home team win probability with all adjustments.

        Args:
            home_team: Home team name
            away_team: Away team name
            home_injuries: List of home team injuries
            away_injuries: List of away team injuries
            home_rest_days: Days of rest for home team
            away_rest_days: Days of rest for away team
            home_back_to_back: Is home team on back-to-back?
            away_back_to_back: Is away team on back-to-back?
            is_playoff: Is this a playoff game?

        Returns:
            Probability home team wins (0 to 1)
        """
        # Get base ratings
        home_elo = self.get_rating(home_team)
        away_elo = self.get_rating(away_team)

        # Apply injury adjustments
        if home_injuries:
            self.injuries[home_team] = home_injuries
            home_elo -= self.calculate_injury_adjustment(home_team)

        if away_injuries:
            self.injuries[away_team] = away_injuries
            away_elo -= self.calculate_injury_adjustment(away_team)

        # Apply form adjustments
        home_elo += self.calculate_form_adjustment(home_team)
        away_elo += self.calculate_form_adjustment(away_team)

        # Apply rest adjustments
        home_elo += self.calculate_rest_adjustment(home_team, home_rest_days, home_back_to_back)
        away_elo += self.calculate_rest_adjustment(away_team, away_rest_days, away_back_to_back)

        # Home court advantage
        home_advantage = self.calculate_home_advantage(home_team, is_playoff)

        # Calculate win probability
        elo_diff = (home_elo + home_advantage) - away_elo
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))

        return win_prob

    def update_team_form(
        self,
        team: str,
        recent_games: List[Dict]
    ) -> None:
        """
        Update team form metrics based on recent games.

        Args:
            team: Team name
            recent_games: List of recent game results (last 10)
        """
        if not recent_games:
            return

        # Calculate last 5 and last 10 records
        last_5 = recent_games[-5:] if len(recent_games) >= 5 else recent_games
        last_10 = recent_games[-10:] if len(recent_games) >= 10 else recent_games

        l5_wins = sum(1 for g in last_5 if g.get('won', False))
        l5_losses = len(last_5) - l5_wins

        l10_wins = sum(1 for g in last_10 if g.get('won', False))
        l10_losses = len(last_10) - l10_wins

        # Point differentials
        l5_diff = np.mean([g.get('point_diff', 0) for g in last_5])
        l10_diff = np.mean([g.get('point_diff', 0) for g in last_10])

        # Calculate streak
        streak = 0
        for game in reversed(recent_games):
            if game.get('won'):
                if streak >= 0:
                    streak += 1
                else:
                    break
            else:
                if streak <= 0:
                    streak -= 1
                else:
                    break

        # Store form
        self.team_form[team] = TeamForm(
            last_5_record=(l5_wins, l5_losses),
            last_10_record=(l10_wins, l10_losses),
            point_diff_l5=l5_diff,
            point_diff_l10=l10_diff,
            streak=streak
        )

    def get_adjustment_breakdown(
        self,
        home_team: str,
        away_team: str,
        **kwargs
    ) -> Dict[str, float]:
        """
        Get detailed breakdown of all Elo adjustments.

        Useful for debugging and understanding model decisions.

        Returns:
            Dictionary with all adjustment components
        """
        # Get base ratings
        home_base = self.get_rating(home_team)
        away_base = self.get_rating(away_team)

        # Calculate all adjustments
        home_injury = -self.calculate_injury_adjustment(home_team)
        away_injury = -self.calculate_injury_adjustment(away_team)

        home_form = self.calculate_form_adjustment(home_team)
        away_form = self.calculate_form_adjustment(away_team)

        home_rest = self.calculate_rest_adjustment(
            home_team,
            kwargs.get('home_rest_days', 2),
            kwargs.get('home_back_to_back', False)
        )
        away_rest = self.calculate_rest_adjustment(
            away_team,
            kwargs.get('away_rest_days', 2),
            kwargs.get('away_back_to_back', False)
        )

        home_adv = self.calculate_home_advantage(
            home_team,
            kwargs.get('is_playoff', False)
        )

        return {
            'home_base_elo': home_base,
            'away_base_elo': away_base,
            'home_injury_adj': home_injury,
            'away_injury_adj': away_injury,
            'home_form_adj': home_form,
            'away_form_adj': away_form,
            'home_rest_adj': home_rest,
            'away_rest_adj': away_rest,
            'home_court_adv': home_adv,
            'home_final_elo': home_base + home_injury + home_form + home_rest + home_adv,
            'away_final_elo': away_base + away_injury + away_form + away_rest,
            'elo_difference': (home_base + home_injury + home_form + home_rest + home_adv) -
                            (away_base + away_injury + away_form + away_rest)
        }


# Injury impact templates
STAR_PLAYER_INJURY = lambda name, pos: InjuryImpact(
    player_name=name,
    position=pos,
    impact_level='star',
    elo_adjustment=65.0  # Major impact
)

STARTER_INJURY = lambda name, pos: InjuryImpact(
    player_name=name,
    position=pos,
    impact_level='starter',
    elo_adjustment=30.0  # Moderate impact
)

ROTATION_INJURY = lambda name, pos: InjuryImpact(
    player_name=name,
    position=pos,
    impact_level='rotation',
    elo_adjustment=10.0  # Minor impact
)

BENCH_INJURY = lambda name, pos: InjuryImpact(
    player_name=name,
    position=pos,
    impact_level='bench',
    elo_adjustment=2.0  # Minimal impact
)


if __name__ == "__main__":
    """Example usage of enhanced Elo model."""

    model = EnhancedEloModel()

    # Set team ratings
    model.set_rating("Cleveland Cavaliers", 1650)
    model.set_rating("Philadelphia 76ers", 1470)

    # Simulate 76ers injuries (Joel Embiid out, Tyrese Maxey questionable)
    sixers_injuries = [
        STAR_PLAYER_INJURY("Joel Embiid", "C"),
        STARTER_INJURY("Tyrese Maxey", "PG")
    ]

    # Simulate Cavs hot streak
    cavs_recent_games = [
        {'won': True, 'point_diff': 15},
        {'won': True, 'point_diff': 8},
        {'won': True, 'point_diff': 12},
        {'won': True, 'point_diff': 5},
        {'won': True, 'point_diff': 10},
    ]
    model.update_team_form("Cleveland Cavaliers", cavs_recent_games)

    # Predict game
    win_prob = model.predict_win_probability(
        home_team="Philadelphia 76ers",
        away_team="Cleveland Cavaliers",
        home_injuries=sixers_injuries,
        away_injuries=[],
        home_rest_days=2,
        away_rest_days=1,
        home_back_to_back=False,
        away_back_to_back=False
    )

    # Get breakdown
    breakdown = model.get_adjustment_breakdown(
        "Philadelphia 76ers",
        "Cleveland Cavaliers",
        home_rest_days=2,
        away_rest_days=1
    )

    print("Enhanced Elo Model Prediction")
    print("=" * 60)
    print(f"Game: Cleveland Cavaliers @ Philadelphia 76ers")
    print()
    print("Adjustments:")
    print(f"  Home Base Elo: {breakdown['home_base_elo']:.0f}")
    print(f"  Home Injuries: {breakdown['home_injury_adj']:+.0f}")
    print(f"  Home Form: {breakdown['home_form_adj']:+.0f}")
    print(f"  Home Rest: {breakdown['home_rest_adj']:+.0f}")
    print(f"  Home Court: +{breakdown['home_court_adv']:.0f}")
    print(f"  Home Final: {breakdown['home_final_elo']:.0f}")
    print()
    print(f"  Away Base Elo: {breakdown['away_base_elo']:.0f}")
    print(f"  Away Injuries: {breakdown['away_injury_adj']:+.0f}")
    print(f"  Away Form: {breakdown['away_form_adj']:+.0f}")
    print(f"  Away Rest: {breakdown['away_rest_adj']:+.0f}")
    print(f"  Away Final: {breakdown['away_final_elo']:.0f}")
    print()
    print(f"Elo Difference: {breakdown['elo_difference']:+.0f}")
    print(f"Cleveland Win Probability: {(1-win_prob)*100:.1f}%")
    print(f"Philadelphia Win Probability: {win_prob*100:.1f}%")
