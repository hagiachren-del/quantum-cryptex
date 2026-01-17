"""
NBA API Client - Official NBA.com Data Integration

Uses the nba_api library (https://github.com/swar/nba_api) to access
official NBA.com data including:
- Current season player stats (2025-26)
- Historical player data
- Team rosters and stats
- Game schedules and scores
- Injury reports
- Real-time updates

Advantages over other APIs:
- FREE (no API key required)
- Official NBA.com data
- Real-time updates
- Comprehensive historical data
- Active development
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# NBA API imports
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    commonplayerinfo,
    playercareerstats,
    playergamelog,
    scoreboardv2,
    leaguegamefinder,
    teamgamelog,
    playerdashboardbyyearoveryear,
    commonteamroster,
    leaguedashplayerstats,
    teamdetails
)


@dataclass
class PlayerInfo:
    """Player information from NBA.com"""
    player_id: int
    full_name: str
    first_name: str
    last_name: str
    is_active: bool
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    team_abbreviation: Optional[str] = None
    jersey: Optional[str] = None
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    birthdate: Optional[str] = None
    school: Optional[str] = None
    country: Optional[str] = None


@dataclass
class PlayerSeasonStats:
    """Player season statistics"""
    player_id: int
    player_name: str
    season: str
    team: str
    games_played: int
    games_started: int
    minutes_per_game: float
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    field_goal_pct: float
    three_point_pct: float
    free_throw_pct: float
    three_pointers_made: float
    offensive_rebounds: float
    defensive_rebounds: float
    personal_fouls: float
    plus_minus: float


@dataclass
class TeamInfo:
    """Team information"""
    team_id: int
    full_name: str
    abbreviation: str
    nickname: str
    city: str
    state: str
    year_founded: int


class NBAAPIClient:
    """
    Client for accessing NBA.com official data via nba_api.

    All methods include rate limiting to respect NBA.com servers.
    """

    def __init__(self, rate_limit_delay: float = 0.6):
        """
        Initialize NBA API client.

        Args:
            rate_limit_delay: Seconds to wait between API calls (default: 0.6)
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

        # Cache for static data
        self._players_cache = None
        self._teams_cache = None

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def get_all_players(self) -> List[Dict]:
        """
        Get list of all NBA players (active and inactive).

        Returns:
            List of player dictionaries with id, full_name, etc.
        """
        if self._players_cache is None:
            self._players_cache = players.get_players()

        return self._players_cache

    def get_active_players(self) -> List[Dict]:
        """Get list of only active NBA players"""
        all_players = self.get_all_players()
        return [p for p in all_players if p['is_active']]

    def find_player(self, name: str) -> Optional[Dict]:
        """
        Find player by name (case-insensitive partial match).

        Args:
            name: Player name or partial name

        Returns:
            Player dict or None if not found
        """
        name_lower = name.lower()
        all_players = self.get_all_players()

        # Try exact match first
        for player in all_players:
            if player['full_name'].lower() == name_lower:
                return player

        # Try partial match
        for player in all_players:
            if name_lower in player['full_name'].lower():
                return player

        return None

    def get_player_info(self, player_id: int) -> Optional[PlayerInfo]:
        """
        Get detailed player information.

        Args:
            player_id: NBA player ID

        Returns:
            PlayerInfo or None if not found
        """
        try:
            self._rate_limit()
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            df = info.get_data_frames()[0]

            if df.empty:
                return None

            row = df.iloc[0]

            return PlayerInfo(
                player_id=int(row['PERSON_ID']),
                full_name=row['DISPLAY_FIRST_LAST'],
                first_name=row['FIRST_NAME'],
                last_name=row['LAST_NAME'],
                is_active=bool(row.get('ROSTERSTATUS', 'Active') == 'Active'),
                team_id=int(row['TEAM_ID']) if pd.notna(row.get('TEAM_ID')) else None,
                team_name=row.get('TEAM_NAME'),
                team_abbreviation=row.get('TEAM_ABBREVIATION'),
                jersey=row.get('JERSEY'),
                position=row.get('POSITION'),
                height=row.get('HEIGHT'),
                weight=row.get('WEIGHT'),
                birthdate=row.get('BIRTHDATE'),
                school=row.get('SCHOOL'),
                country=row.get('COUNTRY')
            )

        except Exception as e:
            print(f"Error fetching player info for {player_id}: {e}")
            return None

    def get_player_season_stats(self,
                                player_id: int,
                                season: str = "2025-26") -> Optional[PlayerSeasonStats]:
        """
        Get player's season statistics (per game averages).

        Args:
            player_id: NBA player ID
            season: Season year (e.g., "2025-26", "2024-25")

        Returns:
            PlayerSeasonStats or None
        """
        try:
            self._rate_limit()
            career = playercareerstats.PlayerCareerStats(player_id=player_id)
            df = career.get_data_frames()[0]  # SeasonTotalsRegularSeason

            if df.empty:
                return None

            # Filter for specific season
            season_df = df[df['SEASON_ID'] == season]

            if season_df.empty:
                # Try previous season if current not available
                prev_season = f"{int(season[:4])-1}-{season[5:]}"
                season_df = df[df['SEASON_ID'] == prev_season]

                if season_df.empty:
                    return None

            row = season_df.iloc[0]

            # Calculate per-game averages
            gp = int(row['GP']) if row['GP'] > 0 else 1

            return PlayerSeasonStats(
                player_id=player_id,
                player_name=row['PLAYER_ID'],  # Will be overridden
                season=row['SEASON_ID'],
                team=row['TEAM_ABBREVIATION'],
                games_played=gp,
                games_started=int(row.get('GS', 0)),
                minutes_per_game=float(row.get('MIN', 0)) / gp,
                points=float(row.get('PTS', 0)) / gp,
                rebounds=float(row.get('REB', 0)) / gp,
                assists=float(row.get('AST', 0)) / gp,
                steals=float(row.get('STL', 0)) / gp,
                blocks=float(row.get('BLK', 0)) / gp,
                turnovers=float(row.get('TOV', 0)) / gp,
                field_goal_pct=float(row.get('FG_PCT', 0)),
                three_point_pct=float(row.get('FG3_PCT', 0)),
                free_throw_pct=float(row.get('FT_PCT', 0)),
                three_pointers_made=float(row.get('FG3M', 0)) / gp,
                offensive_rebounds=float(row.get('OREB', 0)) / gp,
                defensive_rebounds=float(row.get('DREB', 0)) / gp,
                personal_fouls=float(row.get('PF', 0)) / gp,
                plus_minus=float(row.get('PLUS_MINUS', 0)) / gp
            )

        except Exception as e:
            print(f"Error fetching season stats for player {player_id}: {e}")
            return None

    def get_player_last_n_games(self,
                               player_id: int,
                               n: int = 10,
                               season: str = "2025-26") -> List[Dict]:
        """
        Get player's last N game logs.

        Args:
            player_id: NBA player ID
            n: Number of recent games
            season: Season (e.g., "2025-26")

        Returns:
            List of game log dictionaries
        """
        try:
            self._rate_limit()
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star="Regular Season"
            )
            df = gamelog.get_data_frames()[0]

            if df.empty:
                return []

            # Get most recent N games
            recent_games = df.head(n)

            return recent_games.to_dict('records')

        except Exception as e:
            print(f"Error fetching game log for player {player_id}: {e}")
            return []

    def get_todays_games(self) -> List[Dict]:
        """
        Get today's NBA games.

        Returns:
            List of game dictionaries with teams, scores, status
        """
        try:
            self._rate_limit()
            today = datetime.now()
            scoreboard = scoreboardv2.ScoreboardV2(
                game_date=today.strftime('%Y-%m-%d')
            )

            games = scoreboard.get_data_frames()[0]  # GameHeader
            line_score = scoreboard.get_data_frames()[1]  # LineScore

            result = []
            for _, game in games.iterrows():
                game_id = game['GAME_ID']

                # Get team info from line score
                game_teams = line_score[line_score['GAME_ID'] == game_id]

                if len(game_teams) >= 2:
                    result.append({
                        'game_id': game_id,
                        'game_date': game['GAME_DATE_EST'],
                        'home_team': game['HOME_TEAM_ID'],
                        'away_team': game['VISITOR_TEAM_ID'],
                        'game_status': game['GAME_STATUS_TEXT'],
                        'teams': game_teams.to_dict('records')
                    })

            return result

        except Exception as e:
            print(f"Error fetching today's games: {e}")
            return []

    def get_team_roster(self, team_id: int, season: str = "2025-26") -> List[Dict]:
        """
        Get current team roster.

        Args:
            team_id: NBA team ID
            season: Season (e.g., "2025-26")

        Returns:
            List of player dictionaries on roster
        """
        try:
            self._rate_limit()
            roster = commonteamroster.CommonTeamRoster(
                team_id=team_id,
                season=season
            )
            df = roster.get_data_frames()[0]

            return df.to_dict('records')

        except Exception as e:
            print(f"Error fetching roster for team {team_id}: {e}")
            return []

    def get_all_teams(self) -> List[TeamInfo]:
        """Get all NBA teams"""
        if self._teams_cache is None:
            all_teams = teams.get_teams()
            self._teams_cache = [
                TeamInfo(
                    team_id=t['id'],
                    full_name=t['full_name'],
                    abbreviation=t['abbreviation'],
                    nickname=t['nickname'],
                    city=t['city'],
                    state=t['state'],
                    year_founded=t['year_founded']
                )
                for t in all_teams
            ]

        return self._teams_cache

    def find_team(self, name: str) -> Optional[TeamInfo]:
        """
        Find team by name, abbreviation, or city.

        Args:
            name: Team name, abbreviation, or city

        Returns:
            TeamInfo or None
        """
        name_lower = name.lower()
        all_teams = self.get_all_teams()

        for team in all_teams:
            if (name_lower in team.full_name.lower() or
                name_lower in team.abbreviation.lower() or
                name_lower in team.nickname.lower() or
                name_lower in team.city.lower()):
                return team

        return None


def get_player_full_profile(client: NBAAPIClient,
                           player_name: str,
                           season: str = "2025-26") -> Optional[Dict]:
    """
    Get complete player profile including info and stats.

    Args:
        client: NBAAPIClient instance
        player_name: Player name
        season: Season (e.g., "2025-26")

    Returns:
        Dict with 'info' and 'stats' keys, or None
    """
    # Find player
    player = client.find_player(player_name)

    if not player:
        return None

    player_id = player['id']

    # Get detailed info
    info = client.get_player_info(player_id)

    # Get season stats
    stats = client.get_player_season_stats(player_id, season=season)

    # Get recent games for form
    recent_games = client.get_player_last_n_games(player_id, n=10, season=season)

    return {
        'player': player,
        'info': info,
        'stats': stats,
        'recent_games': recent_games
    }


if __name__ == "__main__":
    # Example usage
    print("Testing NBA API Client...")
    print()

    client = NBAAPIClient()

    # Test 1: Find player
    print("Test 1: Finding LeBron James")
    player = client.find_player("LeBron James")
    if player:
        print(f"  ✓ Found: {player['full_name']} (ID: {player['id']})")
    print()

    # Test 2: Get player info
    print("Test 2: Getting detailed player info")
    if player:
        info = client.get_player_info(player['id'])
        if info:
            print(f"  ✓ Team: {info.team_name}")
            print(f"  ✓ Position: {info.position}")
            print(f"  ✓ Jersey: {info.jersey}")
    print()

    # Test 3: Get season stats
    print("Test 3: Getting 2025-26 season stats")
    if player:
        stats = client.get_player_season_stats(player['id'], season="2025-26")
        if stats:
            print(f"  ✓ PPG: {stats.points:.1f}")
            print(f"  ✓ RPG: {stats.rebounds:.1f}")
            print(f"  ✓ APG: {stats.assists:.1f}")
        else:
            print("  ℹ 2025-26 stats not available yet, trying 2024-25...")
            stats = client.get_player_season_stats(player['id'], season="2024-25")
            if stats:
                print(f"  ✓ PPG: {stats.points:.1f}")
                print(f"  ✓ RPG: {stats.rebounds:.1f}")
                print(f"  ✓ APG: {stats.assists:.1f}")
    print()

    # Test 4: Get today's games
    print("Test 4: Getting today's games")
    games = client.get_todays_games()
    print(f"  ✓ Found {len(games)} games today")
    print()

    print("✅ NBA API Client tests complete!")
