#!/usr/bin/env python3
"""
Quick test to verify Sportradar API is working as primary data source
"""

import sys
sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from data.sportradar_api import SportradarNBAClient
from player_props.player_stats_model import PlayerStatsModel

print("\n" + "="*80)
print("🏀 TESTING SPORTRADAR PRIMARY DATA SOURCE")
print("="*80)

# Test 1: Initialize Sportradar client
print("\n1. Initializing Sportradar API...")
api_key = "93Qg8StSODooorMmFtlsvkrzpd8z7GxNPwUe16bn"
sportradar = SportradarNBAClient(api_key)
print("   ✓ Sportradar client initialized")

# Test 2: Get all teams (should be cached)
print("\n2. Testing team hierarchy (cached)...")
teams = sportradar.get_all_teams()
print(f"   ✓ Found {len(teams)} NBA teams")
if teams:
    print(f"   Example: {teams[0].market} {teams[0].name} ({teams[0].alias})")

# Test 3: Initialize PlayerStatsModel with Sportradar
print("\n3. Initializing PlayerStatsModel (Sportradar primary)...")
stats_model = PlayerStatsModel(sportradar_api=sportradar)
print("   ✓ Model initialized with Sportradar as primary")

# Test 4: Get stats for a star player
print("\n4. Testing player stats retrieval...")
test_players = ['LeBron James', 'Stephen Curry', 'Luka Doncic']

for player in test_players:
    print(f"\n   Testing: {player}")
    try:
        mean, std = stats_model._get_player_stats(player, 'points')
        print(f"      Points: {mean:.1f} ± {std:.1f}")
    except Exception as e:
        print(f"      Error: {e}")

# Test 5: Test cache performance
print("\n5. Testing cache performance (second lookup)...")
print("   Re-fetching LeBron James stats...")
import time
start = time.time()
mean, std = stats_model._get_player_stats('LeBron James', 'points')
elapsed = time.time() - start
print(f"   ✓ Retrieved in {elapsed*1000:.1f}ms (should be instant if cached)")
print(f"      Points: {mean:.1f} ± {std:.1f}")

print("\n" + "="*80)
print("✅ SPORTRADAR PRIMARY SOURCE TEST COMPLETE")
print("="*80 + "\n")
