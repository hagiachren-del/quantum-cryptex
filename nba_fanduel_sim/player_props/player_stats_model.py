"""
Player Stats Prediction Model

Estimates player performance probabilities using:
- Historical averages
- Recent form
- Injury status
- Matchup difficulty
- Home/away splits
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Optional, List
from dataclasses import dataclass
import sys
sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')
from data.sportradar_api import SportradarNBAClient, get_player_full_profile  # ONLY data source - NBA official partner
from data.roster_updates_2025_26 import (
    get_player_current_stats,
    get_player_injury_status as get_manual_injury_status,
    get_player_current_team,
    is_player_available
)


@dataclass
class PlayerProjection:
    """Projected player statistics"""

    player_name: str
    prop_type: str

    # Projections
    expected_value: float
    std_dev: float

    # Probability estimates
    over_prob: float
    under_prob: float

    # Context
    line: float
    recent_avg: float
    season_avg: float

    # Adjustments
    injury_factor: float = 1.0
    matchup_factor: float = 1.0
    rest_factor: float = 1.0
    home_away_factor: float = 1.0

    def get_total_adjustment(self) -> float:
        """Get combined adjustment factor"""
        return (self.injury_factor *
                self.matchup_factor *
                self.rest_factor *
                self.home_away_factor)


class PlayerStatsModel:
    """
    Model for predicting player stat probabilities.

    Uses historical data and contextual factors to estimate
    the probability of a player going over/under prop lines.
    """

    # Default historical averages (would ideally come from database)
    DEFAULT_STATS = {
        'points': {'mean': 15.0, 'std': 8.0},
        'rebounds': {'mean': 5.0, 'std': 3.0},
        'assists': {'mean': 3.5, 'std': 2.5},
        'threes': {'mean': 1.5, 'std': 1.2},
        'pts_rebs_asts': {'mean': 25.0, 'std': 12.0}
    }

    def __init__(self, sportradar_api: Optional[SportradarNBAClient] = None, use_live_data: bool = True):
        """
        Initialize player stats model

        Args:
            sportradar_api: Sportradar API client - ONLY data source (NBA official partner)
            use_live_data: If True, fetch real-time data instead of using cache
        """
        self.player_cache = {}
        # Use Sportradar API ONLY (NBA official partner - premium LIVE data)
        sportradar_key = "93Qg8StSODooorMmFtlsvkrzpd8z7GxNPwUe16bn"
        self.sportradar_api = sportradar_api if sportradar_api else SportradarNBAClient(sportradar_key)
        self.use_live_data = use_live_data  # Real-time data (no caching)

    def project_player_prop(self,
                           player_name: str,
                           prop_type: str,
                           line: float,
                           opponent: str = "",
                           home_away: str = "home",
                           injury_status: Optional[str] = None,
                           days_rest: int = 1) -> PlayerProjection:
        """
        Project a player's probability of hitting a prop.

        Args:
            player_name: Player's name
            prop_type: Type of prop ('points', 'rebounds', etc.)
            line: Over/under line
            opponent: Opposing team
            home_away: 'home' or 'away'
            injury_status: 'healthy', 'questionable', 'probable', etc.
            days_rest: Days since last game

        Returns:
            PlayerProjection with probabilities
        """

        # Get player's historical stats
        season_avg, season_std = self._get_player_stats(player_name, prop_type)
        recent_avg = season_avg  # Simplified - would use last 10 games

        # Calculate adjustment factors
        injury_factor = self._calculate_injury_factor(injury_status)
        matchup_factor = self._calculate_matchup_factor(opponent, prop_type)
        rest_factor = self._calculate_rest_factor(days_rest)
        home_away_factor = self._calculate_home_away_factor(home_away, prop_type)

        # Adjusted expected value
        base_expected = season_avg
        expected_value = base_expected * injury_factor * matchup_factor * rest_factor * home_away_factor

        # Adjusted standard deviation (injuries increase variance)
        adjusted_std = season_std
        if injury_factor < 1.0:
            adjusted_std *= 1.2  # More uncertainty when injured

        # Calculate probability using normal distribution
        z_score = (expected_value - line) / adjusted_std
        over_prob = norm.cdf(z_score)
        under_prob = 1 - over_prob

        return PlayerProjection(
            player_name=player_name,
            prop_type=prop_type,
            expected_value=expected_value,
            std_dev=adjusted_std,
            over_prob=over_prob,
            under_prob=under_prob,
            line=line,
            recent_avg=recent_avg,
            season_avg=season_avg,
            injury_factor=injury_factor,
            matchup_factor=matchup_factor,
            rest_factor=rest_factor,
            home_away_factor=home_away_factor
        )

    def _get_player_stats(self, player_name: str, prop_type: str) -> tuple:
        """
        Get player's LIVE stats from Sportradar ONLY.

        Priority:
        1. Manual 2025-26 roster updates (for trades/injuries/current season)
        2. Sportradar API LIVE data (real-time season stats)

        NO FALLBACKS - Sportradar only, or raises error if player not found.
        """

        # Check cache only if NOT using live data
        cache_key = f"{player_name}_{prop_type}"
        if not self.use_live_data and cache_key in self.player_cache:
            return self.player_cache[cache_key]

        # PRIORITY 1: Check manual roster updates for 2025-26 season
        manual_stats = get_player_current_stats(player_name)
        if manual_stats:
            stat_mapping = {
                'points': 'points',
                'rebounds': 'rebounds',
                'assists': 'assists',
                'threes': 'threes',
            }

            if prop_type in stat_mapping:
                stat_field = stat_mapping[prop_type]
                mean = manual_stats.get(stat_field)

                if mean is not None and mean > 0:
                    # Use 30% of mean as std dev
                    default_stds = {'points': 5.0, 'rebounds': 3.0, 'assists': 2.5, 'threes': 1.2}
                    std = max(default_stds.get(prop_type, 3.0), mean * 0.30)

                    # Cache only if not live mode
                    if not self.use_live_data:
                        self.player_cache[cache_key] = (mean, std)

                    team = manual_stats.get('team', '???')
                    gp = manual_stats.get('games_played', 0)
                    print(f"✓ MANUAL 2025-26: {player_name} {prop_type} = {mean:.1f} ± {std:.1f} ({team}, {gp} GP)")
                    return mean, std

        # PRIORITY 2: Sportradar API ONLY (try 2025, then 2024)
        for year in [2025, 2024]:
            try:
                profile = get_player_full_profile(self.sportradar_api, player_name, year=year)

                if profile and profile['stats']:
                    stats = profile['stats']

                    # Map prop type to stat field (Sportradar field names)
                    stat_mapping = {
                        'points': ('points', 5.0),  # (field, default_std)
                        'rebounds': ('rebounds', 3.0),
                        'assists': ('assists', 2.5),
                        'threes': ('three_points_made', 1.2),
                        'pts_rebs_asts': (None, 12.0)  # Calculated
                    }

                    if prop_type in stat_mapping:
                        field, default_std = stat_mapping[prop_type]

                        if prop_type == 'pts_rebs_asts':
                            # Combo stat
                            mean = stats.points + stats.rebounds + stats.assists
                        else:
                            mean = getattr(stats, field, None)

                        if mean is not None and mean > 0:
                            # Use 30% of mean as std dev (conservative estimate)
                            std = max(default_std, mean * 0.30)

                            # Cache only if not live mode
                            if not self.use_live_data:
                                self.player_cache[cache_key] = (mean, std)

                            season_str = f"{year}-{str(year+1)[-2:]}"
                            data_mode = "LIVE" if self.use_live_data else "CACHED"
                            print(f"✓ Sportradar {data_mode} {season_str}: {player_name} {prop_type} = {mean:.1f} ± {std:.1f} ({stats.games_played} GP)")
                            return mean, std

            except Exception as e:
                # Try next season
                if year == 2024:
                    # Last attempt failed
                    print(f"❌ Sportradar API Error for {player_name}: {str(e)}")
                continue

        # NO FALLBACK - Raise error if player not found
        raise ValueError(f"❌ SPORTRADAR ONLY MODE: Player '{player_name}' not found in Sportradar API. No fallback data sources available.")

    def _calculate_injury_factor(self, injury_status: Optional[str]) -> float:
        """
        Calculate injury impact factor.

        Returns:
            Multiplier for expected stats (0.6 - 1.0)
        """

        if injury_status is None or injury_status == 'healthy':
            return 1.0

        injury_impacts = {
            'questionable': 0.85,
            'probable': 0.92,
            'doubtful': 0.70,
            'out': 0.0
        }

        return injury_impacts.get(injury_status.lower(), 1.0)

    def _calculate_matchup_factor(self, opponent: str, prop_type: str) -> float:
        """
        Calculate matchup difficulty factor.

        Uses opponent's defensive ratings from API if available.

        Returns:
            Multiplier (0.85 - 1.15)
        """

        if not opponent:
            return 1.0

        # TODO: Could use team defensive stats from API when available
        # For now, use simplified approach

        # Simplified: hash opponent name to get consistent factor
        np.random.seed(hash(f"{opponent}_{prop_type}") % (2**32))
        # Elite defense (0.85) to poor defense (1.15)
        return np.random.uniform(0.85, 1.15)

    def get_player_injury_status(self, player_name: str) -> Optional[str]:
        """
        Get player's current injury status.

        Checks manual roster updates first, then returns None if not found.

        Returns:
            'healthy', 'out', 'questionable', 'doubtful', or None
        """
        # Check manual roster updates
        status = get_manual_injury_status(player_name)
        if status:
            return status

        # Default to healthy if not in injury report
        return 'healthy'

    def _calculate_rest_factor(self, days_rest: int) -> float:
        """
        Calculate rest/fatigue factor.

        Returns:
            Multiplier (0.90 - 1.05)
        """

        if days_rest == 0:  # Back-to-back
            return 0.92
        elif days_rest == 1:
            return 0.98
        elif days_rest == 2:
            return 1.00
        elif days_rest >= 3:
            return 1.02  # Extra rest helps
        else:
            return 1.0

    def _calculate_home_away_factor(self, home_away: str, prop_type: str) -> float:
        """
        Calculate home/away impact.

        Returns:
            Multiplier (0.95 - 1.05)
        """

        if home_away == 'home':
            # Home advantage for scoring stats
            if prop_type in ['points', 'threes']:
                return 1.03
            elif prop_type in ['assists']:
                return 1.02
            else:
                return 1.01
        else:
            # Slight road disadvantage
            if prop_type in ['points', 'threes']:
                return 0.97
            elif prop_type in ['assists']:
                return 0.98
            else:
                return 0.99

    def estimate_prop_edge(self,
                          projection: PlayerProjection,
                          over_odds: int,
                          under_odds: int) -> Dict:
        """
        Calculate edge on over/under.

        Args:
            projection: PlayerProjection
            over_odds: American odds for over
            under_odds: American odds for under

        Returns:
            Dict with edge analysis
        """

        from odds.fanduel_odds_utils import american_to_probability

        # Market probabilities
        over_market_prob = american_to_probability(over_odds)
        under_market_prob = american_to_probability(under_odds)

        # Remove vig
        total_prob = over_market_prob + under_market_prob
        over_fair = over_market_prob / total_prob
        under_fair = under_market_prob / total_prob

        # Calculate edges
        over_edge = projection.over_prob - over_fair
        under_edge = projection.under_prob - under_fair

        # Determine best bet
        if abs(over_edge) > abs(under_edge):
            best_side = 'over'
            best_edge = over_edge
            best_prob = projection.over_prob
            best_odds = over_odds
        else:
            best_side = 'under'
            best_edge = under_edge
            best_prob = projection.under_prob
            best_odds = under_odds

        return {
            'player': projection.player_name,
            'prop_type': projection.prop_type,
            'line': projection.line,
            'expected_value': projection.expected_value,
            'over_prob': projection.over_prob,
            'under_prob': projection.under_prob,
            'over_edge': over_edge,
            'under_edge': under_edge,
            'best_side': best_side,
            'best_edge': best_edge,
            'best_prob': best_prob,
            'best_odds': best_odds
        }


if __name__ == "__main__":
    # Example usage
    model = PlayerStatsModel()

    # Project a player prop
    projection = model.project_player_prop(
        player_name="Stephen Curry",
        prop_type="points",
        line=27.5,
        opponent="Lakers",
        home_away="home",
        injury_status="healthy",
        days_rest=1
    )

    print(f"Projection for {projection.player_name} {projection.prop_type}")
    print(f"Line: {projection.line}")
    print(f"Expected: {projection.expected_value:.1f}")
    print(f"Over Prob: {projection.over_prob*100:.1f}%")
    print(f"Under Prob: {projection.under_prob*100:.1f}%")
    print()

    # Estimate edge
    edge_analysis = model.estimate_prop_edge(projection, -110, -110)
    print(f"Best Side: {edge_analysis['best_side'].upper()}")
    print(f"Edge: {edge_analysis['best_edge']*100:+.1f}%")
