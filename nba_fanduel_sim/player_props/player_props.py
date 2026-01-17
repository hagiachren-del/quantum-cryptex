"""
Player Props Module

Fetches and analyzes player proposition bets from The Odds API.
Supports points, rebounds, assists, 3-pointers, and combo props.
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PlayerProp:
    """Single player proposition bet"""

    # Player information
    player_name: str
    team: str
    opponent: str

    # Prop details
    prop_type: str  # 'points', 'rebounds', 'assists', 'threes', 'pts_rebs_asts'
    line: float
    over_odds: int
    under_odds: int

    # Game context
    game_time: str
    home_away: str  # 'home' or 'away'

    # Bookmaker
    bookmaker: str = 'fanduel'

    def __str__(self):
        return f"{self.player_name} {self.prop_type.upper()} O/U {self.line}"


class PlayerPropsAPI:
    """
    Fetches player props from The Odds API.

    Supports multiple prop types and same game parlay building.
    """

    def __init__(self, api_key: str):
        """
        Initialize with API key.

        Args:
            api_key: The Odds API key
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

    def fetch_player_props(self,
                          markets: Optional[List[str]] = None,
                          bookmaker: str = 'fanduel') -> List[PlayerProp]:
        """
        Fetch player props for all NBA games.

        Args:
            markets: List of prop markets to fetch. Defaults to common props.
            bookmaker: Bookmaker to get odds from

        Returns:
            List of PlayerProp objects
        """

        if markets is None:
            markets = [
                'player_points',
                'player_rebounds',
                'player_assists',
                'player_threes',
                'player_points_rebounds_assists'
            ]

        all_props = []

        for market in markets:
            props = self._fetch_market(market, bookmaker)
            all_props.extend(props)

        return all_props

    def _fetch_market(self, market: str, bookmaker: str) -> List[PlayerProp]:
        """Fetch a specific player prop market"""

        url = f"{self.base_url}/sports/basketball_nba/odds"

        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': market,
            'bookmakers': bookmaker,
            'oddsFormat': 'american'
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            games = response.json()

            return self._parse_props(games, market)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {market}: {e}")
            return []

    def _parse_props(self, games: List[Dict], market: str) -> List[PlayerProp]:
        """Parse API response into PlayerProp objects"""

        props = []

        # Map market names to prop types
        market_map = {
            'player_points': 'points',
            'player_rebounds': 'rebounds',
            'player_assists': 'assists',
            'player_threes': 'threes',
            'player_points_rebounds_assists': 'pts_rebs_asts'
        }

        prop_type = market_map.get(market, market)

        for game in games:
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            game_time = game.get('commence_time', '')

            # Get bookmaker data
            bookmakers = game.get('bookmakers', [])

            for bookmaker in bookmakers:
                markets_data = bookmaker.get('markets', [])

                for market_data in markets_data:
                    if market_data.get('key') != market:
                        continue

                    outcomes = market_data.get('outcomes', [])

                    # Group by player (over/under pairs)
                    player_outcomes = {}

                    for outcome in outcomes:
                        player_name = outcome.get('description', '')
                        outcome_type = outcome.get('name', '')  # 'Over' or 'Under'
                        odds = outcome.get('price', -110)
                        line = outcome.get('point', 0)

                        if player_name not in player_outcomes:
                            player_outcomes[player_name] = {}

                        player_outcomes[player_name][outcome_type] = {
                            'odds': odds,
                            'line': line
                        }

                    # Create PlayerProp objects
                    for player_name, outcomes_data in player_outcomes.items():
                        if 'Over' not in outcomes_data or 'Under' not in outcomes_data:
                            continue

                        over_data = outcomes_data['Over']
                        under_data = outcomes_data['Under']

                        # Determine player's team (simplified - would need roster lookup)
                        team = home_team  # Placeholder
                        opponent = away_team
                        home_away = 'home'

                        prop = PlayerProp(
                            player_name=player_name,
                            team=team,
                            opponent=opponent,
                            prop_type=prop_type,
                            line=over_data['line'],
                            over_odds=over_data['odds'],
                            under_odds=under_data['odds'],
                            game_time=game_time,
                            home_away=home_away,
                            bookmaker=bookmaker.get('key', 'fanduel')
                        )

                        props.append(prop)

        return props

    def get_props_by_player(self, player_name: str, all_props: List[PlayerProp]) -> List[PlayerProp]:
        """Get all props for a specific player"""
        return [p for p in all_props if p.player_name == player_name]

    def get_props_by_game(self, team1: str, team2: str, all_props: List[PlayerProp]) -> List[PlayerProp]:
        """Get all props for a specific game (for SGP building)"""
        return [
            p for p in all_props
            if (p.team == team1 and p.opponent == team2) or
               (p.team == team2 and p.opponent == team1)
        ]

    def get_props_by_type(self, prop_type: str, all_props: List[PlayerProp]) -> List[PlayerProp]:
        """Get all props of a specific type"""
        return [p for p in all_props if p.prop_type == prop_type]


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python player_props.py YOUR_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1]

    api = PlayerPropsAPI(api_key)

    print("Fetching player props...")
    props = api.fetch_player_props()

    print(f"\nFound {len(props)} player props")
    print("\nSample props:")

    for prop in props[:10]:
        print(f"  {prop}")
        print(f"    Over {prop.line}: {prop.over_odds:+d}")
        print(f"    Under {prop.line}: {prop.under_odds:+d}")
        print()
