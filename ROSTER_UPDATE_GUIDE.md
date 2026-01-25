# 🔄 Manual Roster Update System - User Guide

## Why This System Exists

**Problem:** The NBA API provides **real current NBA data** from NBA.com, which only has data for the actual current season. It cannot predict future trades, injuries, or stats.

**Solution:** Manual roster update system that you maintain with current 2025-26 season information.

---

## Current Status (January 17, 2026)

### ✅ Trades Tracked

| Player | From | To | Status |
|--------|------|----|----|
| **Luka Doncic** | Mavericks | **Lakers** | 28.5 PPG (45 GP) |
| **Anthony Davis** | Lakers | **Mavericks** | 26.3 PPG, 12.1 RPG (38 GP) |

### ⚠️ Injuries Tracked

| Player | Team | Status | Injury | Return Date |
|--------|------|--------|--------|-------------|
| **Jayson Tatum** | Celtics | **OUT** | Ankle sprain | Jan 25, 2026 |
| **Kyrie Irving** | Mavericks | **OUT** | Knee injury | Feb 1, 2026 |

---

## How to Update

### File Location

```
nba_fanduel_sim/data/roster_updates_2025_26.py
```

### 1. Adding a Trade

When a player is traded, add them to `ROSTER_UPDATES`:

```python
ROSTER_UPDATES = {
    'Player Full Name': PlayerUpdate(
        current_team='TEAM_ABBREV',  # DAL, LAL, BOS, etc.
        injury_status='healthy'
    ),
}
```

**Example - Bradley Beal traded to Miami:**

```python
'Bradley Beal': PlayerUpdate(
    current_team='MIA',
    injury_status='healthy'
),
```

### 2. Adding an Injury

When a player gets injured:

```python
'Player Name': PlayerUpdate(
    current_team='TEAM_ABBREV',
    injury_status='out',  # or 'questionable', 'doubtful'
    injury_description='Injury type (e.g., Ankle sprain)',
    est_return_date='2026-01-25'  # Optional
),
```

**Example - Giannis Antetokounmpo injured:**

```python
'Giannis Antetokounmpo': PlayerUpdate(
    current_team='MIL',
    injury_status='questionable',
    injury_description='Back tightness',
    est_return_date='2026-01-20'
),
```

### 3. Adding Current Season Stats

For players with trades or limited games, add stats to `STATS_OVERRIDES_2025_26`:

```python
'Player Name': {
    'team': 'TEAM_ABBREV',
    'games_played': 45,
    'points': 28.5,
    'rebounds': 8.2,
    'assists': 9.1,
    'threes': 3.2,
    'minutes': 36.5
},
```

**Example - Damian Lillard stats:**

```python
'Damian Lillard': {
    'team': 'MIL',
    'games_played': 52,
    'points': 26.8,
    'rebounds': 4.2,
    'assists': 7.1,
    'threes': 3.9,
    'minutes': 35.2
},
```

### 4. Updating Injury Status

When a player returns from injury:

**Before:**
```python
'Jayson Tatum': PlayerUpdate(
    current_team='BOS',
    injury_status='out',
    injury_description='Ankle sprain',
    est_return_date='2026-01-25'
),
```

**After (player returns):**
```python
'Jayson Tatum': PlayerUpdate(
    current_team='BOS',
    injury_status='healthy'  # Change to healthy
),
```

Or simply remove them from `ROSTER_UPDATES` if no longer needed.

---

## Team Abbreviations

| Team | Abbrev | Team | Abbrev |
|------|--------|------|--------|
| Atlanta Hawks | ATL | Memphis Grizzlies | MEM |
| Boston Celtics | BOS | Miami Heat | MIA |
| Brooklyn Nets | BKN | Milwaukee Bucks | MIL |
| Charlotte Hornets | CHA | Minnesota Timberwolves | MIN |
| Chicago Bulls | CHI | New Orleans Pelicans | NOP |
| Cleveland Cavaliers | CLE | New York Knicks | NYK |
| Dallas Mavericks | DAL | Oklahoma City Thunder | OKC |
| Denver Nuggets | DEN | Orlando Magic | ORL |
| Detroit Pistons | DET | Philadelphia 76ers | PHI |
| Golden State Warriors | GSW | Phoenix Suns | PHX |
| Houston Rockets | HOU | Portland Trail Blazers | POR |
| Indiana Pacers | IND | Sacramento Kings | SAC |
| Los Angeles Clippers | LAC | San Antonio Spurs | SAS |
| Los Angeles Lakers | LAL | Toronto Raptors | TOR |
| Utah Jazz | UTA | Washington Wizards | WAS |

---

## Testing Your Updates

After making changes, test the update file:

```bash
python3 nba_fanduel_sim/data/roster_updates_2025_26.py
```

**Expected Output:**

```
=== 2025-26 ROSTER UPDATES ===

TRADES:
  ✓ Luka Doncic → LAL
  ✓ Anthony Davis → DAL

INJURED PLAYERS:
  ⚠ Jayson Tatum (BOS): OUT
      Ankle sprain
      Est. Return: 2026-01-25
  ⚠ Kyrie Irving (DAL): OUT
      Knee injury
      Est. Return: 2026-02-01

CURRENT STATS AVAILABLE:
  Luka Doncic (LAL): 28.5 PPG, 8.2 RPG (45 GP)
  Anthony Davis (DAL): 26.3 PPG, 12.1 RPG (38 GP)
  ...
```

---

## How the System Works

### Priority System

When analyzing player props, the system checks in this order:

1. **Manual 2025-26 Updates** (highest priority)
   - Checks `ROSTER_UPDATES` and `STATS_OVERRIDES_2025_26`
   - Uses your manually entered current season data

2. **NBA API 2025-26 Season**
   - Tries to fetch current season from NBA.com
   - May not have data for ongoing season

3. **NBA API 2024-25 Season**
   - Falls back to last completed season
   - Used if current season data unavailable

4. **Demo Data**
   - Last resort fallback
   - Generates realistic but random stats

### Example Output

```
Testing: Luka Doncic - points
  Injury Status: healthy
✓ Using MANUAL 2025-26 stats for Luka Doncic: points = 28.5 ± 8.5 (LAL, 45 GP)
  Points: 28.5 ± 8.5
```

This confirms the system is using your manual updates!

---

## Daily Maintenance Checklist

### Before Each Game Day:

1. **Check Latest Trades**
   - Visit ESPN.com, NBA.com, or Twitter
   - Add any new trades to `ROSTER_UPDATES`

2. **Update Injury Report**
   - Check official NBA injury report
   - Update injury statuses (out → questionable → healthy)
   - Add estimated return dates

3. **Verify Stats**
   - For recently traded players, update their current season averages
   - Use NBA.com or Basketball Reference for accurate stats

4. **Test Updates**
   ```bash
   python3 nba_fanduel_sim/data/roster_updates_2025_26.py
   ```

5. **Run Production Analysis**
   ```bash
   python3 player_props_analysis.py
   ```

---

## Common Scenarios

### Scenario 1: Player Gets Traded Mid-Season

**Example:** Zach LaVine traded from Bulls to Lakers

**Steps:**

1. Add to `ROSTER_UPDATES`:
   ```python
   'Zach LaVine': PlayerUpdate(
       current_team='LAL',  # New team
       injury_status='healthy'
   ),
   ```

2. Add his stats to `STATS_OVERRIDES_2025_26`:
   ```python
   'Zach LaVine': {
       'team': 'LAL',
       'games_played': 48,  # Total this season
       'points': 22.5,      # Season average
       'rebounds': 4.8,
       'assists': 4.2,
       'threes': 2.8,
       'minutes': 34.0
   },
   ```

3. Test:
   ```bash
   python3 nba_fanduel_sim/data/roster_updates_2025_26.py
   ```

### Scenario 2: Player Returns from Injury

**Example:** Jayson Tatum returns January 25

**Steps:**

1. Update in `ROSTER_UPDATES`:
   ```python
   'Jayson Tatum': PlayerUpdate(
       current_team='BOS',
       injury_status='healthy'  # Changed from 'out'
   ),
   ```

2. Or remove entirely if healthy and no trade

3. Keep stats in `STATS_OVERRIDES_2025_26` for accurate projections

### Scenario 3: New Injury

**Example:** Kevin Durant sprains ankle

**Steps:**

1. Add to `ROSTER_UPDATES`:
   ```python
   'Kevin Durant': PlayerUpdate(
       current_team='PHX',
       injury_status='out',
       injury_description='Ankle sprain',
       est_return_date='2026-02-10'
   ),
   ```

2. System will automatically exclude from betting opportunities

3. Maintain his pre-injury stats in `STATS_OVERRIDES_2025_26`

---

## Integration with Analysis Scripts

The manual updates work seamlessly with all analysis scripts:

### Player Props Analysis
```bash
python3 player_props_analysis.py
```
- Automatically uses manual roster data
- Shows injury warnings
- Excludes injured players

### Production Run
```bash
python3 production_run_nba_api.py YOUR_ODDS_KEY
```
- Checks injuries before analysis
- Uses current team rosters
- Applies injury factors to projections

---

## Advanced: Adding Multiple Players

For bulk updates (e.g., trade deadline), update all at once:

```python
# Multiple trades at deadline
ROSTER_UPDATES = {
    # Trade 1: 3-team deal
    'Player A': PlayerUpdate(current_team='MIA', injury_status='healthy'),
    'Player B': PlayerUpdate(current_team='BOS', injury_status='healthy'),
    'Player C': PlayerUpdate(current_team='LAL', injury_status='healthy'),

    # Trade 2: Star moves
    'Player D': PlayerUpdate(current_team='NYK', injury_status='healthy'),

    # Injuries
    'Player E': PlayerUpdate(current_team='GSW', injury_status='out', injury_description='Surgery'),
    'Player F': PlayerUpdate(current_team='DAL', injury_status='questionable', injury_description='Illness'),
}
```

---

## Troubleshooting

### Problem: Player showing old team

**Solution:**
- Add player to `ROSTER_UPDATES` with new team
- Run test script to verify

### Problem: Injury status not updating

**Solution:**
- Check spelling of player name (must match exactly)
- Ensure `injury_status` is one of: 'healthy', 'out', 'questionable', 'doubtful'

### Problem: Stats seem wrong

**Solution:**
- Update `STATS_OVERRIDES_2025_26` with current season averages
- Use per-game averages, not totals
- Source from NBA.com or Basketball Reference

### Problem: System using old data

**Solution:**
- Clear cache: Delete `player_cache` dict and re-run
- Check manual updates file for typos
- Verify player name matches exactly (case-sensitive)

---

## Quick Reference Card

**Add Trade:**
```python
'Name': PlayerUpdate(current_team='TEAM', injury_status='healthy')
```

**Add Injury:**
```python
'Name': PlayerUpdate(current_team='TEAM', injury_status='out', injury_description='Type')
```

**Add Stats:**
```python
'Name': {'team': 'TEAM', 'points': 25.0, 'rebounds': 8.0, 'games_played': 50}
```

**Test:**
```bash
python3 nba_fanduel_sim/data/roster_updates_2025_26.py
```

---

## Summary

This manual roster system ensures your betting simulator has **accurate, up-to-date 2025-26 season data** despite the NBA API only having real current data.

**Key Points:**
- ✅ Update file after every trade
- ✅ Check injury reports daily
- ✅ Test changes before running analysis
- ✅ System automatically uses manual data as priority
- ✅ Injured players excluded from betting opportunities

**File to Edit:**
```
nba_fanduel_sim/data/roster_updates_2025_26.py
```

Keep this file updated and your betting simulator will always have accurate data! 🏀
