"""
Manual Roster and Injury Updates for 2025-26 Season

This file allows manual updates for trades, injuries, and current roster
changes that haven't happened yet in the real NBA (but exist in our simulator).

Update this file as trades happen and injuries are reported.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PlayerUpdate:
    """Manual player update"""
    current_team: str  # Current team abbreviation
    injury_status: Optional[str] = None  # 'healthy', 'out', 'questionable', 'doubtful'
    injury_description: Optional[str] = None
    est_return_date: Optional[str] = None


# MANUAL ROSTER UPDATES FOR 2025-26 SEASON
# Update this as trades happen
ROSTER_UPDATES = {
    # Major Trades
    'Anthony Davis': PlayerUpdate(
        current_team='DAL',  # Traded to Dallas Mavericks
        injury_status='healthy'
    ),

    'Luka Doncic': PlayerUpdate(
        current_team='LAL',  # Traded to Los Angeles Lakers
        injury_status='healthy'
    ),

    # Injuries
    'Jayson Tatum': PlayerUpdate(
        current_team='BOS',
        injury_status='out',
        injury_description='Ankle sprain',
        est_return_date='2026-01-25'
    ),

    'Kyrie Irving': PlayerUpdate(
        current_team='DAL',
        injury_status='out',
        injury_description='Knee injury',
        est_return_date='2026-02-01'
    ),

    # Add more as needed
}


# CURRENT 2025-26 STATS OVERRIDES
# When NBA API doesn't have current season data, use these
STATS_OVERRIDES_2025_26 = {
    'Luka Doncic': {
        'team': 'LAL',
        'games_played': 45,
        'points': 28.5,
        'rebounds': 8.2,
        'assists': 9.1,
        'threes': 3.2,
        'minutes': 36.5
    },

    'Anthony Davis': {
        'team': 'DAL',
        'games_played': 38,
        'points': 26.3,
        'rebounds': 12.1,
        'assists': 3.2,
        'threes': 0.8,
        'minutes': 35.2
    },

    # Injured players - use pre-injury stats
    'Jayson Tatum': {
        'team': 'BOS',
        'games_played': 42,  # Before injury
        'points': 27.8,
        'rebounds': 8.9,
        'assists': 4.5,
        'threes': 3.1,
        'minutes': 36.0
    },

    'Kyrie Irving': {
        'team': 'DAL',
        'games_played': 35,  # Before injury
        'points': 25.2,
        'rebounds': 4.1,
        'assists': 5.3,
        'threes': 2.9,
        'minutes': 34.5
    },

    # Add more as needed
}


def get_player_current_team(player_name: str) -> Optional[str]:
    """Get player's current team (accounting for trades)"""
    if player_name in ROSTER_UPDATES:
        return ROSTER_UPDATES[player_name].current_team
    return None


def get_player_injury_status(player_name: str) -> Optional[str]:
    """Get player's current injury status"""
    if player_name in ROSTER_UPDATES:
        return ROSTER_UPDATES[player_name].injury_status
    return 'healthy'


def get_player_current_stats(player_name: str) -> Optional[Dict]:
    """Get player's current 2025-26 season stats"""
    return STATS_OVERRIDES_2025_26.get(player_name)


def is_player_available(player_name: str) -> bool:
    """Check if player is available to play"""
    status = get_player_injury_status(player_name)
    return status == 'healthy' or status is None


# TEAM ROSTERS - Current 2025-26 rosters after trades
TEAM_ROSTERS = {
    'LAL': [  # Lakers
        'Luka Doncic',  # NEW - traded from Dallas
        'LeBron James',
        'Austin Reaves',
        'Rui Hachimura',
        'Bronny James',
        # Add full roster
    ],

    'DAL': [  # Mavericks
        'Anthony Davis',  # NEW - traded from Lakers
        # Kyrie Irving - injured
        'Derrick Jones Jr',
        'P.J. Washington',
        # Add full roster
    ],

    'BOS': [  # Celtics
        # Jayson Tatum - injured
        'Jaylen Brown',
        'Kristaps Porzingis',
        'Derrick White',
        'Jrue Holiday',
        # Add full roster
    ],

    # Add more teams as needed
}


def get_team_roster(team_abbrev: str) -> List[str]:
    """Get current team roster"""
    return TEAM_ROSTERS.get(team_abbrev, [])


def get_all_injured_players() -> List[str]:
    """Get list of all injured players"""
    return [
        player for player, update in ROSTER_UPDATES.items()
        if update.injury_status in ['out', 'doubtful', 'questionable']
    ]


# USAGE INSTRUCTIONS:
"""
To use this in your analysis:

1. Check for roster updates:
   current_team = get_player_current_team('Luka Doncic')
   # Returns: 'LAL'

2. Check injury status:
   status = get_player_injury_status('Jayson Tatum')
   # Returns: 'out'

3. Get current stats:
   stats = get_player_current_stats('Luka Doncic')
   # Returns: {'team': 'LAL', 'points': 28.5, ...}

4. Check availability:
   available = is_player_available('Kyrie Irving')
   # Returns: False (injured)

5. Get team roster:
   roster = get_team_roster('LAL')
   # Returns: ['Luka Doncic', 'LeBron James', ...]
"""


if __name__ == '__main__':
    print("=== 2025-26 ROSTER UPDATES ===")
    print()

    print("TRADES:")
    for player, update in ROSTER_UPDATES.items():
        if update.injury_status == 'healthy':
            print(f"  ✓ {player} → {update.current_team}")
    print()

    print("INJURED PLAYERS:")
    for player in get_all_injured_players():
        update = ROSTER_UPDATES[player]
        print(f"  ⚠ {player} ({update.current_team}): {update.injury_status.upper()}")
        if update.injury_description:
            print(f"      {update.injury_description}")
        if update.est_return_date:
            print(f"      Est. Return: {update.est_return_date}")
    print()

    print("CURRENT STATS AVAILABLE:")
    for player in STATS_OVERRIDES_2025_26.keys():
        stats = STATS_OVERRIDES_2025_26[player]
        print(f"  {player} ({stats['team']}): {stats['points']:.1f} PPG, {stats['rebounds']:.1f} RPG ({stats['games_played']} GP)")
