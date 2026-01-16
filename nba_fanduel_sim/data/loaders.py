"""
Data Loaders for NBA Games and FanDuel Odds

Loads historical NBA game data and FanDuel odds data from CSV files.
Includes placeholder loaders with clear documentation for swapping in real data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from pathlib import Path


@dataclass
class NBAGame:
    """
    Represents a single NBA game with final scores and metadata.

    Attributes:
        game_id: Unique identifier for the game
        date: Game date
        home_team: Home team abbreviation (e.g., 'LAL', 'GSW')
        away_team: Away team abbreviation
        home_score: Final home team score
        away_score: Final away team score
        home_rest_days: Days of rest for home team before game
        away_rest_days: Days of rest for away team before game
        season: Season year (e.g., 2023 for 2023-24 season)
        is_playoff: Whether game is a playoff game
    """
    game_id: str
    date: datetime
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_rest_days: int
    away_rest_days: int
    season: int
    is_playoff: bool = False

    @property
    def home_won(self) -> bool:
        """Returns True if home team won."""
        return self.home_score > self.away_score

    @property
    def margin(self) -> int:
        """Returns home team margin (positive if home won)."""
        return self.home_score - self.away_score

    @property
    def total_points(self) -> int:
        """Returns total points scored in game."""
        return self.home_score + self.away_score


@dataclass
class FanDuelOdds:
    """
    Represents FanDuel odds for a single NBA game.

    FanDuel odds are typically closing lines (final odds before game starts).
    All odds are in American format.

    Attributes:
        game_id: Links to NBAGame.game_id
        moneyline_home: Home team moneyline (e.g., -150)
        moneyline_away: Away team moneyline (e.g., +130)
        spread: Point spread, home team perspective (e.g., -4.5)
        spread_odds_home: Odds for home team covering spread (typically -110)
        spread_odds_away: Odds for away team covering spread (typically -110)
        total: Over/under total points (optional for V1)
        over_odds: Odds for over (optional for V1)
        under_odds: Odds for under (optional for V1)
        line_timestamp: When these odds were recorded (closing preferred)
    """
    game_id: str
    moneyline_home: float
    moneyline_away: float
    spread: float
    spread_odds_home: float
    spread_odds_away: float
    total: Optional[float] = None
    over_odds: Optional[float] = None
    under_odds: Optional[float] = None
    line_timestamp: Optional[datetime] = None


def load_games_csv(filepath: Path) -> List[NBAGame]:
    """
    Load NBA game data from CSV file.

    Expected CSV columns:
        - game_id: Unique identifier
        - date: Game date (YYYY-MM-DD format)
        - home_team: Home team abbreviation
        - away_team: Away team abbreviation
        - home_score: Home team final score
        - away_score: Away team final score
        - home_rest_days: Days rest for home team
        - away_rest_days: Days rest for away team
        - season: Season year (optional)
        - is_playoff: Playoff flag (optional, default False)

    Args:
        filepath: Path to CSV file

    Returns:
        List of NBAGame objects

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Game data file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = [
        'game_id', 'date', 'home_team', 'away_team',
        'home_score', 'away_score', 'home_rest_days', 'away_rest_days'
    ]
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Parse dates
    df['date'] = pd.to_datetime(df['date'])

    # Add optional columns with defaults
    if 'season' not in df.columns:
        # Infer season from date (Oct-Sep season)
        df['season'] = df['date'].apply(
            lambda d: d.year if d.month < 10 else d.year + 1
        )
    if 'is_playoff' not in df.columns:
        df['is_playoff'] = False

    # Convert to NBAGame objects
    games = []
    for _, row in df.iterrows():
        game = NBAGame(
            game_id=str(row['game_id']),
            date=row['date'],
            home_team=str(row['home_team']),
            away_team=str(row['away_team']),
            home_score=int(row['home_score']),
            away_score=int(row['away_score']),
            home_rest_days=int(row['home_rest_days']),
            away_rest_days=int(row['away_rest_days']),
            season=int(row['season']),
            is_playoff=bool(row['is_playoff'])
        )
        games.append(game)

    return games


def load_fanduel_odds_csv(filepath: Path) -> List[FanDuelOdds]:
    """
    Load FanDuel odds data from CSV file.

    Expected CSV columns:
        - game_id: Links to game
        - fanduel_moneyline_home: Home moneyline (American odds)
        - fanduel_moneyline_away: Away moneyline (American odds)
        - fanduel_spread: Point spread (home team perspective)
        - fanduel_spread_odds_home: Home spread odds (typically -110)
        - fanduel_spread_odds_away: Away spread odds (typically -110)
        - fanduel_total: Total points line (optional)
        - fanduel_over_odds: Over odds (optional)
        - fanduel_under_odds: Under odds (optional)
        - line_timestamp: When odds recorded (optional)

    Args:
        filepath: Path to CSV file

    Returns:
        List of FanDuelOdds objects

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Odds data file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = [
        'game_id', 'fanduel_moneyline_home', 'fanduel_moneyline_away',
        'fanduel_spread', 'fanduel_spread_odds_home', 'fanduel_spread_odds_away'
    ]
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Parse timestamps if present
    if 'line_timestamp' in df.columns:
        df['line_timestamp'] = pd.to_datetime(df['line_timestamp'])

    # Convert to FanDuelOdds objects
    odds_list = []
    for _, row in df.iterrows():
        odds = FanDuelOdds(
            game_id=str(row['game_id']),
            moneyline_home=float(row['fanduel_moneyline_home']),
            moneyline_away=float(row['fanduel_moneyline_away']),
            spread=float(row['fanduel_spread']),
            spread_odds_home=float(row['fanduel_spread_odds_home']),
            spread_odds_away=float(row['fanduel_spread_odds_away']),
            total=float(row['fanduel_total']) if 'fanduel_total' in row and pd.notna(row['fanduel_total']) else None,
            over_odds=float(row['fanduel_over_odds']) if 'fanduel_over_odds' in row and pd.notna(row['fanduel_over_odds']) else None,
            under_odds=float(row['fanduel_under_odds']) if 'fanduel_under_odds' in row and pd.notna(row['fanduel_under_odds']) else None,
            line_timestamp=row['line_timestamp'] if 'line_timestamp' in row and pd.notna(row['line_timestamp']) else None
        )
        odds_list.append(odds)

    return odds_list


def merge_games_and_odds(
    games: List[NBAGame],
    odds: List[FanDuelOdds]
) -> List[Dict]:
    """
    Merge game data with FanDuel odds data.

    Creates a combined dataset with both game outcomes and betting lines.
    Only includes games that have both game data and odds data.

    Args:
        games: List of NBA games
        odds: List of FanDuel odds

    Returns:
        List of dictionaries containing merged game and odds data,
        sorted chronologically by game date

    Example:
        >>> games = load_games_csv('games.csv')
        >>> odds = load_fanduel_odds_csv('odds.csv')
        >>> merged = merge_games_and_odds(games, odds)
        >>> len(merged)
        1230
    """
    # Create lookup dictionary for odds
    odds_dict = {o.game_id: o for o in odds}

    # Merge games with odds
    merged = []
    for game in games:
        if game.game_id in odds_dict:
            game_odds = odds_dict[game.game_id]

            merged_data = {
                # Game info
                'game_id': game.game_id,
                'date': game.date,
                'home_team': game.home_team,
                'away_team': game.away_team,
                'home_score': game.home_score,
                'away_score': game.away_score,
                'home_rest_days': game.home_rest_days,
                'away_rest_days': game.away_rest_days,
                'season': game.season,
                'is_playoff': game.is_playoff,
                'home_won': game.home_won,
                'margin': game.margin,
                'total_points': game.total_points,
                # FanDuel odds
                'moneyline_home': game_odds.moneyline_home,
                'moneyline_away': game_odds.moneyline_away,
                'spread': game_odds.spread,
                'spread_odds_home': game_odds.spread_odds_home,
                'spread_odds_away': game_odds.spread_odds_away,
                'total': game_odds.total,
                'over_odds': game_odds.over_odds,
                'under_odds': game_odds.under_odds,
                'line_timestamp': game_odds.line_timestamp,
            }
            merged.append(merged_data)

    # Sort by date
    merged.sort(key=lambda x: x['date'])

    return merged


def generate_sample_data(
    output_dir: Path,
    n_games: int = 100,
    start_date: str = "2023-10-01",
    random_seed: int = 42
) -> None:
    """
    Generate sample NBA game and FanDuel odds data for testing.

    This creates realistic-looking placeholder data with:
    - Plausible NBA scores
    - Realistic FanDuel odds patterns
    - Proper correlations between odds and outcomes

    NOTE: This is SYNTHETIC data for testing only.
    Replace with real historical data for actual analysis.

    Args:
        output_dir: Directory to save CSV files
        n_games: Number of games to generate
        start_date: Starting date for games
        random_seed: Random seed for reproducibility
    """
    np.random.seed(random_seed)

    teams = [
        'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN',
        'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA',
        'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHX',
        'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS'
    ]

    games_data = []
    odds_data = []

    current_date = pd.to_datetime(start_date)

    for i in range(n_games):
        game_id = f"2024{i:05d}"

        # Random teams
        home_team = np.random.choice(teams)
        away_team = np.random.choice([t for t in teams if t != home_team])

        # Generate realistic scores (home court advantage ~3 points)
        base_score = np.random.normal(110, 10)
        home_advantage = np.random.normal(3, 5)

        home_score = int(max(80, base_score + home_advantage))
        away_score = int(max(80, base_score - home_advantage + np.random.normal(0, 10)))

        # Rest days
        home_rest = np.random.choice([0, 1, 2, 3], p=[0.2, 0.5, 0.2, 0.1])
        away_rest = np.random.choice([0, 1, 2, 3], p=[0.2, 0.5, 0.2, 0.1])

        games_data.append({
            'game_id': game_id,
            'date': current_date.strftime('%Y-%m-%d'),
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'home_rest_days': home_rest,
            'away_rest_days': away_rest,
            'season': 2024,
            'is_playoff': False
        })

        # Generate FanDuel odds (with home bias and realistic vig)
        actual_margin = home_score - away_score

        # Spread centered near actual margin with noise
        spread = np.random.normal(actual_margin * 0.7, 3)
        spread = round(spread * 2) / 2  # Round to nearest 0.5

        # Moneyline based on spread
        if spread < -7:
            ml_home = np.random.uniform(-300, -200)
            ml_away = np.random.uniform(+200, +300)
        elif spread < -3:
            ml_home = np.random.uniform(-180, -120)
            ml_away = np.random.uniform(+120, +180)
        elif spread < 3:
            ml_home = np.random.uniform(-120, +120)
            ml_away = np.random.uniform(-120, +120)
        elif spread < 7:
            ml_home = np.random.uniform(+120, +180)
            ml_away = np.random.uniform(-180, -120)
        else:
            ml_home = np.random.uniform(+200, +300)
            ml_away = np.random.uniform(-300, -200)

        # Spread odds typically -110, sometimes -108/-112
        spread_juice = np.random.choice([-110, -108, -112], p=[0.8, 0.1, 0.1])

        odds_data.append({
            'game_id': game_id,
            'fanduel_moneyline_home': round(ml_home),
            'fanduel_moneyline_away': round(ml_away),
            'fanduel_spread': spread,
            'fanduel_spread_odds_home': spread_juice,
            'fanduel_spread_odds_away': spread_juice,
        })

        # Advance date (games every 1-2 days)
        current_date += pd.Timedelta(days=np.random.choice([1, 2]))

    # Save to CSV
    output_dir.mkdir(parents=True, exist_ok=True)

    games_df = pd.DataFrame(games_data)
    games_df.to_csv(output_dir / 'sample_games.csv', index=False)

    odds_df = pd.DataFrame(odds_data)
    odds_df.to_csv(output_dir / 'sample_fanduel_odds.csv', index=False)

    print(f"Generated {n_games} sample games and odds")
    print(f"Saved to {output_dir}/sample_games.csv and {output_dir}/sample_fanduel_odds.csv")
