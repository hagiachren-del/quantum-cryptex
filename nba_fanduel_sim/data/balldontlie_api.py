"""
BallDontLie API Integration

Fetches real NBA data including:
- Current team rosters
- Player season averages
- Injury reports
- Player props
- Game statistics
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
import time


@dataclass
class PlayerInfo:
    """Player information with current team"""
    player_id: int
    first_name: str
    last_name: str
    position: str
    team: str
    team_id: int
    height: str
    weight: str
    jersey_number: str

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@dataclass
class PlayerStats:
    """Player season statistics"""
    player_id: int
    player_name: str
    games_played: int

    # Scoring
    points: float
    field_goal_pct: float
    three_point_pct: float
    free_throw_pct: float

    # Rebounds
    rebounds: float
    offensive_rebounds: float
    defensive_rebounds: float

    # Other stats
    assists: float
    steals: float
    blocks: float
    turnovers: float
    minutes: float


@dataclass
class InjuryReport:
    """Player injury information"""
    player_id: int
    player_name: str
    team: str
    status: str  # 'Out', 'Questionable', 'Probable', 'Day-to-Day'
    injury: str
    return_date: Optional[str]


class BallDontLieAPI:
    """
    Interface to BallDontLie API for NBA data.

    Free tier available, paid tier for more requests.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize API client.

        Args:
            api_key: Optional API key for authentication
        """
        self.base_url = "https://api.balldontlie.io"
        self.api_key = api_key
        self.headers = {}

        if api_key:
            self.headers['Authorization'] = api_key

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return {}

    def get_player_by_name(self, name: str) -> Optional[PlayerInfo]:
        """
        Get player information by name.

        Args:
            name: Player name (first or last)

        Returns:
            PlayerInfo object or None
        """

        endpoint = "/v1/players"
        params = {'search': name}

        data = self._make_request(endpoint, params)

        if not data or 'data' not in data or not data['data']:
            return None

        # Get first matching player
        player = data['data'][0]

        return PlayerInfo(
            player_id=player.get('id'),
            first_name=player.get('first_name', ''),
            last_name=player.get('last_name', ''),
            position=player.get('position', ''),
            team=player.get('team', {}).get('full_name', 'Free Agent'),
            team_id=player.get('team', {}).get('id', 0),
            height=player.get('height', ''),
            weight=player.get('weight', ''),
            jersey_number=player.get('jersey_number', '')
        )

    def get_player_season_averages(self, player_id: int, season: int = 2024) -> Optional[PlayerStats]:
        """
        Get player's season averages.

        Args:
            player_id: Player ID from BallDontLie
            season: Season year (e.g., 2024 for 2024-25 season)

        Returns:
            PlayerStats object or None
        """

        endpoint = f"/v1/season_averages"
        params = {
            'season': season,
            'player_ids[]': player_id
        }

        data = self._make_request(endpoint, params)

        if not data or 'data' not in data or not data['data']:
            return None

        stats = data['data'][0]

        return PlayerStats(
            player_id=player_id,
            player_name="",  # Will be filled by caller
            games_played=stats.get('games_played', 0),
            points=stats.get('pts', 0.0),
            field_goal_pct=stats.get('fg_pct', 0.0),
            three_point_pct=stats.get('fg3_pct', 0.0),
            free_throw_pct=stats.get('ft_pct', 0.0),
            rebounds=stats.get('reb', 0.0),
            offensive_rebounds=stats.get('oreb', 0.0),
            defensive_rebounds=stats.get('dreb', 0.0),
            assists=stats.get('ast', 0.0),
            steals=stats.get('stl', 0.0),
            blocks=stats.get('blk', 0.0),
            turnovers=stats.get('turnover', 0.0),
            minutes=stats.get('min', 0.0)
        )

    def get_team_roster(self, team_id: int) -> List[PlayerInfo]:
        """
        Get current roster for a team.

        Args:
            team_id: Team ID from BallDontLie

        Returns:
            List of PlayerInfo objects
        """

        endpoint = f"/v1/teams/{team_id}/roster"

        data = self._make_request(endpoint)

        if not data or 'data' not in data:
            return []

        roster = []
        for player in data['data']:
            roster.append(PlayerInfo(
                player_id=player.get('id'),
                first_name=player.get('first_name', ''),
                last_name=player.get('last_name', ''),
                position=player.get('position', ''),
                team=player.get('team', {}).get('full_name', ''),
                team_id=team_id,
                height=player.get('height', ''),
                weight=player.get('weight', ''),
                jersey_number=player.get('jersey_number', '')
            ))

        return roster

    def get_injuries(self) -> List[InjuryReport]:
        """
        Get current NBA injury reports.

        Returns:
            List of InjuryReport objects
        """

        endpoint = "/v1/injuries"

        data = self._make_request(endpoint)

        if not data or 'data' not in data:
            return []

        injuries = []
        for injury in data['data']:
            player = injury.get('player', {})

            injuries.append(InjuryReport(
                player_id=player.get('id', 0),
                player_name=f"{player.get('first_name', '')} {player.get('last_name', '')}",
                team=player.get('team', {}).get('full_name', ''),
                status=injury.get('status', 'Unknown'),
                injury=injury.get('description', 'Not specified'),
                return_date=injury.get('return_date')
            ))

        return injuries

    def get_all_teams(self) -> List[Dict]:
        """Get list of all NBA teams"""

        endpoint = "/v1/teams"

        data = self._make_request(endpoint)

        if not data or 'data' not in data:
            return []

        return data['data']

    def search_players(self, query: str) -> List[PlayerInfo]:
        """
        Search for players by name.

        Args:
            query: Search query

        Returns:
            List of matching PlayerInfo objects
        """

        endpoint = "/v1/players"
        params = {'search': query}

        data = self._make_request(endpoint, params)

        if not data or 'data' not in data:
            return []

        results = []
        for player in data['data']:
            results.append(PlayerInfo(
                player_id=player.get('id'),
                first_name=player.get('first_name', ''),
                last_name=player.get('last_name', ''),
                position=player.get('position', ''),
                team=player.get('team', {}).get('full_name', 'Free Agent'),
                team_id=player.get('team', {}).get('id', 0),
                height=player.get('height', ''),
                weight=player.get('weight', ''),
                jersey_number=player.get('jersey_number', '')
            ))

        return results


def get_player_full_profile(api: BallDontLieAPI, player_name: str, season: int = 2024) -> Dict:
    """
    Get complete player profile including stats and injury status.

    Args:
        api: BallDontLieAPI instance
        player_name: Player name to search
        season: Season year

    Returns:
        Dictionary with player info, stats, and injury status
    """

    # Search for player
    player = api.get_player_by_name(player_name)

    if not player:
        return {'error': f'Player {player_name} not found'}

    # Get season stats
    stats = api.get_player_season_averages(player.player_id, season)

    # Get injury status
    injuries = api.get_injuries()
    player_injury = next(
        (inj for inj in injuries if inj.player_id == player.player_id),
        None
    )

    return {
        'player': player,
        'stats': stats,
        'injury': player_injury,
        'current_team': player.team,
        'position': player.position
    }


if __name__ == "__main__":
    # Example usage
    api = BallDontLieAPI()  # Can add API key if you have one

    # Test with Anthony Davis to see current team
    print("Testing with Anthony Davis...")
    profile = get_player_full_profile(api, "Anthony Davis")

    if 'error' not in profile:
        print(f"\nPlayer: {profile['player'].full_name}")
        print(f"Current Team: {profile['current_team']}")
        print(f"Position: {profile['position']}")

        if profile['stats']:
            print(f"\n2024-25 Season Averages:")
            print(f"  Points: {profile['stats'].points:.1f}")
            print(f"  Rebounds: {profile['stats'].rebounds:.1f}")
            print(f"  Assists: {profile['stats'].assists:.1f}")

        if profile['injury']:
            print(f"\nInjury Status: {profile['injury'].status}")
            print(f"  Details: {profile['injury'].injury}")
    else:
        print(profile['error'])

    # Test getting current injuries
    print("\n" + "="*50)
    print("Current NBA Injuries:")
    print("="*50)

    injuries = api.get_injuries()
    for injury in injuries[:5]:  # Show first 5
        print(f"{injury.player_name} ({injury.team}): {injury.status} - {injury.injury}")
