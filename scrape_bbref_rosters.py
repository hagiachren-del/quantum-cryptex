#!/usr/bin/env python3
"""
Scrape 2025-26 NBA Rosters from Basketball Reference

Pulls current season stats for all NBA players.
"""

import requests
import pandas as pd
import json
import time

def fetch_2025_26_stats():
    """Fetch all player stats from Basketball Reference 2025-26 season"""

    print("🏀 Fetching 2025-26 NBA Player Stats from Basketball Reference...")
    print("=" * 80)

    url = "https://www.basketball-reference.com/leagues/NBA_2026_per_game.html"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Parse with pandas
    print("\n📊 Parsing player stats table...")
    tables = pd.read_html(response.text)

    # The per_game stats table should be the first one
    df = tables[0]

    # Clean up the dataframe
    # Remove header rows that appear in the middle of the table
    df = df[df['Player'] != 'Player']

    # Convert numeric columns
    numeric_cols = ['Age', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA',
                    '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%',
                    'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Filter out rows with no data
    df = df.dropna(subset=['PTS', 'TRB', 'AST'])

    print(f"✓ Found {len(df)} players with stats")

    # Debug: Print columns
    print(f"\nColumns available: {list(df.columns)[:10]}...")

    # Convert to dictionary format
    players_dict = {}

    for _, row in df.iterrows():
        player_name = str(row['Player'])

        # Get team - handle different possible column names
        team = 'N/A'
        for col in ['Tm', 'Team']:
            if col in df.columns:
                team = str(row[col]) if pd.notna(row[col]) else 'N/A'
                break

        # Handle players traded (will have multiple rows)
        # Keep the TOT (total) row if it exists
        if player_name in players_dict and team != 'TOT':
            continue

        # Get position
        pos = 'N/A'
        for col in ['Pos', 'Position']:
            if col in df.columns:
                pos = str(row[col]) if pd.notna(row[col]) else 'N/A'
                break

        players_dict[player_name] = {
            'team': team,
            'position': pos,
            'games_played': int(row['G']) if pd.notna(row['G']) else 0,
            'points': float(row['PTS']) if pd.notna(row['PTS']) else 0.0,
            'rebounds': float(row['TRB']) if pd.notna(row['TRB']) else 0.0,
            'assists': float(row['AST']) if pd.notna(row['AST']) else 0.0,
            'threes': float(row['3P']) if pd.notna(row['3P']) else 0.0,
            'minutes': float(row['MP']) if pd.notna(row['MP']) else 0.0
        }

    return players_dict

def generate_roster_updates(players_dict):
    """Generate Python code for roster_updates_2025_26.py"""

    print("\n" + "=" * 80)
    print("📝 Generating STATS_OVERRIDES_2025_26 Code")
    print("=" * 80)

    # Sort by points per game (top scorers first)
    sorted_players = sorted(
        players_dict.items(),
        key=lambda x: x[1]['points'],
        reverse=True
    )

    # Output Python code
    output = []
    output.append("# 2025-26 NBA Season Stats from Basketball Reference")
    output.append("# Auto-generated - DO NOT EDIT MANUALLY\n")
    output.append("STATS_OVERRIDES_2025_26 = {")

    for player_name, stats in sorted_players:
        if stats['games_played'] >= 5 and stats['points'] > 5.0:  # Filter for active players
            output.append(f"    '{player_name}': {{")
            output.append(f"        'team': '{stats['team']}',")
            output.append(f"        'games_played': {stats['games_played']},")
            output.append(f"        'points': {stats['points']:.1f},")
            output.append(f"        'rebounds': {stats['rebounds']:.1f},")
            output.append(f"        'assists': {stats['assists']:.1f},")
            output.append(f"        'threes': {stats['threes']:.1f},")
            output.append(f"        'minutes': {stats['minutes']:.1f}")
            output.append(f"    }},")

    output.append("}")

    return "\n".join(output)

def main():
    """Main execution"""

    # Fetch stats
    players_dict = fetch_2025_26_stats()

    # Save raw data to JSON
    json_file = '/home/user/quantum-cryptex/bbref_rosters_2025_26.json'
    with open(json_file, 'w') as f:
        json.dump(players_dict, f, indent=2)
    print(f"\n✓ Saved raw data to {json_file}")

    # Generate Python code
    python_code = generate_roster_updates(players_dict)

    # Save to file
    output_file = '/home/user/quantum-cryptex/generated_roster_overrides.py'
    with open(output_file, 'w') as f:
        f.write(python_code)

    print(f"✓ Saved Python code to {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    active_players = [p for p in players_dict.values() if p['games_played'] >= 5]
    print(f"Total Players: {len(players_dict)}")
    print(f"Active Players (5+ games): {len(active_players)}")

    # Top 10 scorers
    print("\n🏆 TOP 10 SCORERS (2025-26):")
    sorted_players = sorted(
        players_dict.items(),
        key=lambda x: x[1]['points'],
        reverse=True
    )[:10]

    for i, (name, stats) in enumerate(sorted_players, 1):
        print(f"   {i:2d}. {name:25s} - {stats['points']:5.1f} PPG ({stats['team']})")

    print("\n" + "=" * 80)
    print("✅ DONE! Copy the content from generated_roster_overrides.py")
    print("   to update roster_updates_2025_26.py")
    print("=" * 80)

if __name__ == '__main__':
    main()
