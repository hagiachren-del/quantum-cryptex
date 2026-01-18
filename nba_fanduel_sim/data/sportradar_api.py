"""
Sportradar NBA API Client - Premium Real-Time NBA Data

Official Sportradar API integration for:
- Real-time player statistics (2025-26 season)
- Team rosters and profiles
- Live game data and scores
- Season statistics and averages
- Player game logs
- Injury reports

API Key: 93Qg8StSODooorMmFtlsvkrzpd8z7GxNPwUe16bn
Docs: https://developer.sportradar.com/basketball/reference/nba-overview
"""

import time
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class PlayerProfile:
    """Sportradar player profile"""
    player_id: str
    full_name: str
    first_name: str
    last_name: str
    position: str
    primary_position: str
    jersey_number: str
    height: int  # inches
    weight: int  # pounds
    birthdate: str
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    team_market: Optional[str] = None
    rookie_year: Optional[int] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_pick: Optional[int] = None


@dataclass
class PlayerSeasonStats:
    """Player season statistics"""
    player_id: str
    player_name: str
    team: str
    season_year: int
    games_played: int
    games_started: int
    minutes: float
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    field_goals_made: float
    field_goals_att: float
    field_goal_pct: float
    three_points_made: float
    three_points_att: float
    three_point_pct: float
    free_throws_made: float
    free_throws_att: float
    free_throw_pct: float
    offensive_rebounds: float
    defensive_rebounds: float
    personal_fouls: float
    plus_minus: float


@dataclass
class TeamInfo:
    """Team information"""
    team_id: str
    name: str
    market: str
    alias: str  # Team abbreviation
    conference: str
    division: str
    founded: Optional[int] = None


@dataclass
class GameInfo:
    """Game information"""
    game_id: str
    scheduled: str
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = "scheduled"
    quarter: Optional[int] = None
    clock: Optional[str] = None


class SportradarNBAClient:
    """
    Client for Sportradar NBA API.

    Provides access to real-time NBA data including:
    - Player profiles and statistics
    - Team rosters and information
    - Game schedules and live scores
    - Season statistics
    - Player game logs
    """

    BASE_URL = "https://api.sportradar.us/nba/trial/v8/en"

    def __init__(self, api_key: str, rate_limit_delay: float = 1.0, use_live_data: bool = True):
        """
        Initialize Sportradar NBA API client.

        Args:
            api_key: Sportradar API key
            rate_limit_delay: Seconds between requests (trial: 1/sec, paid: varies)
            use_live_data: If True, disable caching for real-time data
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.use_live_data = use_live_data

        # Caching system (disabled in LIVE mode)
        self._teams_cache = None
        self._players_cache = {}
        self._stats_cache = {}  # Cache player stats {player_id_year: (stats, timestamp)}
        self._cache_ttl = 0 if use_live_data else 3600  # 0 = no cache for LIVE, 1 hour for historical

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request with rate limiting"""
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        params = {'api_key': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Sportradar API Error: {e}")
            return None

    def get_league_hierarchy(self) -> Optional[Dict]:
        """
        Get complete league hierarchy (teams, divisions, conferences).

        Returns:
            Dict with all teams and structure
        """
        endpoint = "/league/hierarchy.json"
        return self._make_request(endpoint)

    def get_all_teams(self) -> List[TeamInfo]:
        """Get all NBA teams"""
        if self._teams_cache:
            return self._teams_cache

        hierarchy = self.get_league_hierarchy()
        if not hierarchy:
            return []

        teams = []
        for conference in hierarchy.get('conferences', []):
            for division in conference.get('divisions', []):
                for team in division.get('teams', []):
                    teams.append(TeamInfo(
                        team_id=team['id'],
                        name=team['name'],
                        market=team['market'],
                        alias=team['alias'],
                        conference=conference['name'],
                        division=division['name']
                    ))

        self._teams_cache = teams
        return teams

    def find_team(self, name: str) -> Optional[TeamInfo]:
        """Find team by name, market, or alias"""
        teams = self.get_all_teams()
        name_lower = name.lower()

        for team in teams:
            if (name_lower in team.name.lower() or
                name_lower in team.market.lower() or
                name_lower in team.alias.lower()):
                return team

        return None

    def get_team_profile(self, team_id: str) -> Optional[Dict]:
        """
        Get team profile including roster.

        Args:
            team_id: Sportradar team ID

        Returns:
            Team profile with roster
        """
        endpoint = f"/teams/{team_id}/profile.json"
        return self._make_request(endpoint)

    def get_team_roster(self, team_id: str) -> List[Dict]:
        """Get current team roster"""
        profile = self.get_team_profile(team_id)

        if not profile:
            return []

        return profile.get('players', [])

    def get_player_profile(self, player_id: str) -> Optional[PlayerProfile]:
        """
        Get player profile.

        Args:
            player_id: Sportradar player ID

        Returns:
            PlayerProfile or None
        """
        endpoint = f"/players/{player_id}/profile.json"
        data = self._make_request(endpoint)

        if not data:
            return None

        return PlayerProfile(
            player_id=data['id'],
            full_name=data['full_name'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            position=data.get('position', ''),
            primary_position=data.get('primary_position', ''),
            jersey_number=data.get('jersey_number', ''),
            height=data.get('height', 0),
            weight=data.get('weight', 0),
            birthdate=data.get('birthdate', ''),
            rookie_year=data.get('rookie_year'),
            draft_year=data.get('draft', {}).get('year'),
            draft_round=data.get('draft', {}).get('round'),
            draft_pick=data.get('draft', {}).get('pick')
        )

    def get_season_schedule(self, year: int, season_type: str = "REG") -> Optional[Dict]:
        """
        Get season schedule.

        Args:
            year: Season year (e.g., 2025 for 2025-26 season)
            season_type: "REG" (regular) or "PST" (playoffs)

        Returns:
            Schedule data
        """
        endpoint = f"/games/{year}/{season_type}/schedule.json"
        return self._make_request(endpoint)

    def get_daily_schedule(self, date: datetime) -> Optional[Dict]:
        """
        Get games for specific date.

        Args:
            date: Date to get games for

        Returns:
            Daily schedule
        """
        date_str = date.strftime("%Y/%m/%d")
        endpoint = f"/games/{date_str}/schedule.json"
        return self._make_request(endpoint)

    def get_todays_games(self) -> List[GameInfo]:
        """Get today's games"""
        schedule = self.get_daily_schedule(datetime.now())

        if not schedule or 'games' not in schedule:
            return []

        games = []
        for game in schedule['games']:
            games.append(GameInfo(
                game_id=game['id'],
                scheduled=game['scheduled'],
                home_team=game['home']['alias'],
                away_team=game['away']['alias'],
                home_score=game.get('home_points'),
                away_score=game.get('away_points'),
                status=game.get('status', 'scheduled')
            ))

        return games

    def get_game_summary(self, game_id: str) -> Optional[Dict]:
        """
        Get live game summary with current score.

        Args:
            game_id: Sportradar game ID

        Returns:
            Game summary with live data
        """
        endpoint = f"/games/{game_id}/summary.json"
        return self._make_request(endpoint)

    def get_player_season_stats(self, player_id: str, year: int = 2025,
                                season_type: str = "REG") -> Optional[PlayerSeasonStats]:
        """
        Get player season statistics with caching.

        Args:
            player_id: Sportradar player ID
            year: Season year (2025 for 2025-26)
            season_type: "REG" or "PST"

        Returns:
            PlayerSeasonStats or None
        """
        # Check cache first
        cache_key = f"{player_id}_{year}_{season_type}"
        if cache_key in self._stats_cache:
            stats, timestamp = self._stats_cache[cache_key]
            # Check if cache is still valid (within TTL)
            if time.time() - timestamp < self._cache_ttl:
                return stats

        endpoint = f"/seasons/{year}/{season_type}/players/{player_id}/statistics.json"
        data = self._make_request(endpoint)

        if not data or 'seasons' not in data:
            return None

        # Get most recent season
        season = data['seasons'][0] if data['seasons'] else None
        if not season:
            return None

        totals = season.get('total', {})
        games = totals.get('games_played', 1)

        if games == 0:
            games = 1

        stats = PlayerSeasonStats(
            player_id=player_id,
            player_name=data.get('full_name', ''),
            team=season.get('teams', [{}])[0].get('alias', '') if season.get('teams') else '',
            season_year=year,
            games_played=totals.get('games_played', 0),
            games_started=totals.get('games_started', 0),
            minutes=totals.get('minutes', 0) / games,
            points=totals.get('points', 0) / games,
            rebounds=totals.get('rebounds', 0) / games,
            assists=totals.get('assists', 0) / games,
            steals=totals.get('steals', 0) / games,
            blocks=totals.get('blocks', 0) / games,
            turnovers=totals.get('turnovers', 0) / games,
            field_goals_made=totals.get('field_goals_made', 0) / games,
            field_goals_att=totals.get('field_goals_att', 0) / games,
            field_goal_pct=totals.get('field_goals_pct', 0),
            three_points_made=totals.get('three_points_made', 0) / games,
            three_points_att=totals.get('three_points_att', 0) / games,
            three_point_pct=totals.get('three_points_pct', 0),
            free_throws_made=totals.get('free_throws_made', 0) / games,
            free_throws_att=totals.get('free_throws_att', 0) / games,
            free_throw_pct=totals.get('free_throws_pct', 0),
            offensive_rebounds=totals.get('offensive_rebounds', 0) / games,
            defensive_rebounds=totals.get('defensive_rebounds', 0) / games,
            personal_fouls=totals.get('personal_fouls', 0) / games,
            plus_minus=totals.get('plus_minus', 0) / games
        )

        # Cache the stats with current timestamp
        cache_key = f"{player_id}_{year}_{season_type}"
        self._stats_cache[cache_key] = (stats, time.time())

        return stats

    def find_player_by_name(self, name: str) -> Optional[str]:
        """
        Find player ID by name.

        Note: Requires iterating through teams to find player.
        Consider caching results.

        Args:
            name: Player name

        Returns:
            Player ID or None
        """
        name_lower = name.lower()

        # Check cache
        if name_lower in self._players_cache:
            return self._players_cache[name_lower]

        # Search through all teams
        teams = self.get_all_teams()

        for team in teams:
            roster = self.get_team_roster(team.team_id)

            for player in roster:
                player_full = player.get('full_name', '').lower()

                if name_lower in player_full or player_full in name_lower:
                    player_id = player['id']
                    self._players_cache[name_lower] = player_id
                    return player_id

        return None

    def get_injuries(self) -> Optional[Dict]:
        """
        Get league-wide injury report.

        Returns:
            Injury data
        """
        endpoint = "/league/injuries.json"
        return self._make_request(endpoint)


def get_player_full_profile(client: SportradarNBAClient,
                           player_name: str,
                           year: int = 2025) -> Optional[Dict]:
    """
    Get complete player profile with stats.

    Args:
        client: SportradarNBAClient instance
        player_name: Player name
        year: Season year

    Returns:
        Dict with profile and stats
    """
    # Find player ID
    player_id = client.find_player_by_name(player_name)

    if not player_id:
        return None

    # Get profile
    profile = client.get_player_profile(player_id)

    # Get stats
    stats = client.get_player_season_stats(player_id, year=year)

    return {
        'player_id': player_id,
        'profile': profile,
        'stats': stats
    }


if __name__ == "__main__":
    # Test the API
    print("Testing Sportradar NBA API...")
    print()

    api_key = "93Qg8StSODooorMmFtlsvkrzpd8z7GxNPwUe16bn"
    client = SportradarNBAClient(api_key)

    # Test 1: Get teams
    print("Test 1: Getting all teams")
    teams = client.get_all_teams()
    print(f"  ✓ Found {len(teams)} teams")
    print()

    # Test 2: Find Lakers
    print("Test 2: Finding Lakers")
    lakers = client.find_team("Lakers")
    if lakers:
        print(f"  ✓ Found: {lakers.market} {lakers.name} ({lakers.alias})")
    print()

    # Test 3: Get today's games
    print("Test 3: Getting today's games")
    games = client.get_todays_games()
    print(f"  ✓ Found {len(games)} games")
    for game in games[:3]:
        print(f"    - {game.away_team} @ {game.home_team}")
    print()

    print("✅ Sportradar API tests complete!")
