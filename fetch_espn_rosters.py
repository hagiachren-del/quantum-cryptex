#!/usr/bin/env python3
"""
Fetch Current NBA Rosters from ESPN API

Pulls 2024-25 season rosters and stats for all 30 NBA teams.
Updates roster_updates_2025_26.py with current data.
"""

import requests
import json
import time
from typing import Dict, List

def fetch_all_teams() -> List[Dict]:
    """Fetch all NBA teams from ESPN API"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    teams = data['sports'][0]['leagues'][0]['teams']

    return [team['team'] for team in teams]

def fetch_team_roster(team_id: str) -> Dict:
    """Fetch roster for a specific team"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()

def fetch_player_stats(player_id: str) -> Dict:
    """Fetch stats for a specific player"""
    # ESPN athlete stats endpoint
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/2025/types/2/athletes/{player_id}/statistics"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def main():
    """Fetch all rosters and generate stats overrides"""

    print("🏀 Fetching NBA Rosters from ESPN API...")
    print("=" * 80)

    # Fetch all teams
    print("\n📋 Fetching teams...")
    teams = fetch_all_teams()
    print(f"✓ Found {len(teams)} NBA teams")

    all_players = {}
    team_count = 0

    for team in teams:
        team_id = team['id']
        team_abbr = team['abbreviation']
        team_name = team['displayName']

        print(f"\n🏀 {team_name} ({team_abbr})...")

        try:
            # Fetch roster
            roster_data = fetch_team_roster(team_id)

            if 'athletes' not in roster_data:
                print(f"   ⚠️  No roster data available")
                continue

            athletes = roster_data['athletes']
            player_count = 0

            for athlete in athletes:
                player_name = athlete.get('displayName', athlete.get('fullName'))
                player_id = athlete.get('id')
                position = athlete.get('position', {}).get('abbreviation', 'N/A')

                # Try to get stats from athlete object
                stats = None
                if 'statistics' in athlete:
                    stats = athlete['statistics']

                # Extract season averages if available
                if stats and 'splits' in stats:
                    # Look for season averages
                    for split in stats['splits']['categories']:
                        if split['name'] == 'general':
                            stat_dict = {}
                            for stat in split['stats']:
                                stat_dict[stat['name']] = stat.get('value', 0)

                            # Store player data
                            all_players[player_name] = {
                                'team': team_abbr,
                                'position': position,
                                'games_played': int(stat_dict.get('gamesPlayed', 0)),
                                'points': float(stat_dict.get('avgPoints', 0)),
                                'rebounds': float(stat_dict.get('avgRebounds', 0)),
                                'assists': float(stat_dict.get('avgAssists', 0)),
                                'threes': float(stat_dict.get('avgThreePointFieldGoalsMade', 0)),
                                'minutes': float(stat_dict.get('avgMinutes', 0))
                            }
                            player_count += 1
                            print(f"   ✓ {player_name} ({position}) - {stat_dict.get('avgPoints', 0):.1f} PPG")
                            break
                else:
                    # No stats available, just add basic info
                    all_players[player_name] = {
                        'team': team_abbr,
                        'position': position,
                        'games_played': 0,
                        'points': 0.0,
                        'rebounds': 0.0,
                        'assists': 0.0,
                        'threes': 0.0,
                        'minutes': 0.0
                    }
                    print(f"   • {player_name} ({position}) - No stats available")

            print(f"   ✓ {player_count} players with stats")
            team_count += 1

            # Rate limit - be nice to ESPN
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue

    print(f"\n{'=' * 80}")
    print(f"✅ Fetched {len(all_players)} players from {team_count} teams")

    # Save to JSON file
    output_file = '/home/user/quantum-cryptex/espn_rosters_2024_25.json'
    with open(output_file, 'w') as f:
        json.dump(all_players, f, indent=2)

    print(f"✓ Saved to {output_file}")

    # Generate Python code for roster_updates file
    print(f"\n{'=' * 80}")
    print("📝 Generating STATS_OVERRIDES_2025_26 code...")
    print(f"{'=' * 80}\n")

    # Sort by PPG descending
    top_players = sorted(
        [(name, data) for name, data in all_players.items() if data['points'] > 10],
        key=lambda x: x[1]['points'],
        reverse=True
    )[:100]  # Top 100 scorers

    print("# Add these to STATS_OVERRIDES_2025_26 in roster_updates_2025_26.py:\n")
    print("STATS_OVERRIDES_2025_26 = {")

    for player_name, stats in top_players:
        if stats['games_played'] > 0:
            print(f"    '{player_name}': {{")
            print(f"        'team': '{stats['team']}',")
            print(f"        'games_played': {stats['games_played']},")
            print(f"        'points': {stats['points']:.1f},")
            print(f"        'rebounds': {stats['rebounds']:.1f},")
            print(f"        'assists': {stats['assists']:.1f},")
            print(f"        'threes': {stats['threes']:.1f},")
            print(f"        'minutes': {stats['minutes']:.1f}")
            print(f"    }},\n")

    print("}")

    print(f"\n{'=' * 80}")
    print("✅ Done! Copy the output above to update roster_updates_2025_26.py")
    print(f"{'=' * 80}")

if __name__ == '__main__':
    main()
