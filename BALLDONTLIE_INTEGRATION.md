# BallDontLie API Integration for Real NBA Stats

## Overview

The SGP Builder now integrates with the **BallDontLie API** to use real, current NBA player statistics instead of demo data. This provides:

✅ **Accurate season averages** - Real 2024-25 PPG, RPG, APG, etc.
✅ **Current rosters** - Know which team each player is on (e.g., Anthony Davis's actual team)
✅ **Live injury reports** - Automatic injury status for all players
✅ **Actual player profiles** - Height, weight, position, jersey number

## Why BallDontLie API?

The BallDontLie API (https://www.balldontlie.io) is a free NBA statistics API that provides:

- **Player Stats**: Season averages and game logs
- **Team Rosters**: Current team assignments
- **Injury Reports**: Up-to-date injury status
- **Game Data**: Schedules, scores, and box scores
- **Free Tier**: 500 API requests per month

## Getting Started

### 1. Get Your API Key

Visit https://www.balldontlie.io and sign up for a free API key.

Free tier includes:
- 500 requests per month
- No credit card required
- Full access to all endpoints

### 2. Use Real Stats in SGP Analysis

#### Option A: Demo Script with API Integration

```bash
python3 sgp_balldontlie_demo.py YOUR_ODDS_API_KEY YOUR_BALLDONTLIE_API_KEY
```

This will:
1. Test BallDontLie API connection
2. Fetch real stats for LeBron James, Stephen Curry, Nikola Jokic
3. Display current teams and season averages
4. Show current injury report
5. Run SGP analysis with real projections

#### Option B: Full Production Run with Real Stats

Update `sgp_production_run.py` to use BallDontLie API:

```python
from data.balldontlie_api import BallDontLieAPI
from player_props.player_stats_model import PlayerStatsModel

# Initialize with API key
balldontlie_api = BallDontLieAPI(api_key="YOUR_BALLDONTLIE_API_KEY")

# Pass to stats model
stats_model = PlayerStatsModel(balldontlie_api=balldontlie_api)

# Now all projections use real stats!
projection = stats_model.project_player_prop(
    player_name="LeBron James",
    prop_type="points",
    line=24.5,
    opponent="Warriors",
    home_away="away"
)
```

#### Option C: Without API Key (Demo Mode)

If you don't have an API key yet, the system gracefully falls back to demo data:

```bash
python3 sgp_balldontlie_demo.py YOUR_ODDS_API_KEY
```

The system will:
- Use demo statistics (randomized but consistent)
- Print warning: "ℹ No BallDontLie API key provided - using demo stats"
- Still perform full analysis with adjusted projections

## What Real Stats Are Used

### Player Season Averages

When you project a prop, the system fetches:

```python
stats = api.get_player_season_averages(player_id, season=2024)

# Returns:
stats.points          # Points per game
stats.rebounds        # Rebounds per game
stats.assists         # Assists per game
stats.steals          # Steals per game
stats.blocks          # Blocks per game
stats.turnovers       # Turnovers per game
stats.field_goal_pct  # FG%
stats.three_point_pct # 3P%
stats.free_throw_pct  # FT%
stats.games_played    # Games played
stats.minutes         # Minutes per game
```

### Current Team Rosters

Example: Checking if Anthony Davis is still on the Lakers

```python
player = api.get_player_by_name("Anthony Davis")

print(f"{player.first_name} {player.last_name}")
print(f"Current Team: {player.team}")  # e.g., "MIA" if traded to Heat
print(f"Position: {player.position}")
```

### Injury Status

Automatically fetched for all players:

```python
injuries = api.get_injuries()

for injury in injuries:
    print(f"{injury.player_name}: {injury.status}")
    # Status: "Out", "Questionable", "Probable", "Doubtful"
```

The `PlayerStatsModel` automatically:
1. Checks if player is in injury report
2. Applies appropriate injury factor:
   - Questionable: 0.85 (reduce expected stats 15%)
   - Probable: 0.92 (reduce 8%)
   - Doubtful: 0.70 (reduce 30%)
   - Out: 0.0 (cannot play)

## Example Output Comparison

### Without BallDontLie API (Demo Data)

```
⚠ Could not fetch real stats for LeBron James, using demo data

Projection for LeBron James points:
  Season Average: 18.3 ± 6.1  (random demo value)
  Line: 24.5
  Expected: 17.8
  Over Probability: 36.2%
```

### With BallDontLie API (Real Stats)

```
✓ Using real stats for LeBron James: points = 25.4 ± 7.6

Projection for LeBron James points:
  Season Average: 25.4 ± 7.6  (actual 2024-25 stats)
  Line: 24.5
  Expected: 24.7 (with adjustments)
  Over Probability: 51.2%
```

Much more accurate!

## Integration Architecture

### Data Flow

```
1. User requests prop analysis
   ↓
2. PlayerStatsModel checks if BallDontLie API available
   ↓
3a. API Available:
    - Fetch player profile by name
    - Get player_id
    - Fetch season averages
    - Use real stats for projection
   ↓
3b. API Not Available:
    - Use demo stats
    - Print warning
   ↓
4. Apply adjustment factors (injury, matchup, rest, home/away)
   ↓
5. Return projection with probabilities
```

### Code Structure

```
nba_fanduel_sim/
├── data/
│   ├── balldontlie_api.py         # BallDontLie API client
│   ├── __init__.py                # Exports API classes
│   └── loaders.py
├── player_props/
│   ├── player_stats_model.py      # Uses BallDontLie for real stats
│   ├── sgp_analyzer.py
│   └── player_props.py
└── ...
```

## API Endpoints Used

### `/v1/players`
Search for players by name

```python
api.get_player_by_name("LeBron James")
# Returns: PlayerInfo with team, position, etc.
```

### `/v1/season_averages`
Get player season statistics

```python
api.get_player_season_averages(player_id=237, season=2024)
# Returns: PlayerStats with PPG, RPG, APG, etc.
```

### `/v1/injuries`
Get current injury report

```python
api.get_injuries()
# Returns: List[InjuryReport] for all injured players
```

### `/v1/teams/{id}/roster`
Get team roster (optional)

```python
api.get_team_roster(team_id=14)  # Lakers
# Returns: List of player IDs on team
```

## Error Handling

The integration is robust with graceful fallbacks:

### API Key Invalid

```
API Error: 401 Client Error: Unauthorized
⚠ Could not fetch real stats for LeBron James, using demo data
```

### Player Not Found

```
⚠ Player not found in BallDontLie database
⚠ Could not fetch real stats for Unknown Player, using demo data
```

### Rate Limit Exceeded

```
API Error: 429 Too Many Requests
⚠ Could not fetch real stats (rate limited), using demo data
```

### Network Error

```
API Error: Connection timeout
⚠ Could not fetch real stats, using demo data
```

All errors fall back to demo data automatically, so the analysis continues.

## Rate Limits and Optimization

### Free Tier Limits

- **500 requests/month**
- Resets monthly

### Caching Strategy

The `PlayerStatsModel` caches results:

```python
# First request - hits API
projection1 = model.project_player_prop("LeBron James", "points", 24.5)
# ✓ Using real stats for LeBron James: points = 25.4 ± 7.6

# Second request - uses cache
projection2 = model.project_player_prop("LeBron James", "rebounds", 7.5)
# (uses cached LeBron stats, no API call)
```

### Optimizing API Usage

For Saturday's 11 games with 34 player props:

1. **Without optimization**: 34 API calls (one per player-stat combo)
2. **With caching**: ~15-20 API calls (one per unique player)
3. **With batch processing**: Could reduce to ~2-3 calls

Example weekly usage:
- Saturday analysis: 20 API calls
- Sunday analysis: 15 API calls
- Total per week: ~100 calls
- **Fits comfortably in 500/month free tier**

## Real vs Demo Stats: Impact on Analysis

### Demo Stats Issues

1. **Inconsistent with reality**: Random player skills
2. **No injury awareness**: Must manually input
3. **Outdated rosters**: Doesn't know trades
4. **Generic projections**: Same variance for all players

### Real Stats Benefits

1. **Accurate baselines**: Actual 2024-25 season performance
2. **Automatic injury integration**: Fetches latest status
3. **Current team info**: Knows where players actually play
4. **Player-specific variance**: Stars have lower variance than role players

### Example: Impact on Edge Detection

**LeBron James Points Over 24.5 (-110)**

Demo Stats:
- Projects 18.3 PPG (way too low)
- Shows UNDER as +EV
- False signal

Real Stats:
- Projects 25.4 PPG (accurate)
- Shows OVER has slight edge
- Correct analysis

**Result**: Real stats prevent costly mistakes!

## Troubleshooting

### "401 Unauthorized" Error

**Problem**: API key not accepted

**Solutions**:
1. Verify API key is correct
2. Check key has not expired
3. Ensure key is passed correctly:
   ```python
   api = BallDontLieAPI(api_key="your_key_here")
   ```

### "Player Not Found"

**Problem**: Name doesn't match database

**Solutions**:
1. Try variations: "LeBron James" vs "Lebron James"
2. Check spelling
3. Use partial match if available
4. Fall back to demo data

### "No Stats for 2024 Season"

**Problem**: Player hasn't played yet this season

**Solutions**:
1. Use previous season (2023)
2. Use demo data for rookies
3. Check if player is injured/inactive

## Next Steps

1. **Get API Key**: Sign up at https://www.balldontlie.io

2. **Test Integration**:
   ```bash
   python3 sgp_balldontlie_demo.py YOUR_ODDS_KEY YOUR_BALLDONTLIE_KEY
   ```

3. **Update Production Runs**: Add BallDontLie to your main SGP scripts

4. **Verify Accuracy**: Compare projections with and without real stats

5. **Monitor API Usage**: Track requests to stay within free tier

## Future Enhancements

Potential improvements to the integration:

1. **Team Defensive Stats**: Use opponent defensive ratings for matchup factor
2. **Recent Form**: Weight last 10 games more heavily than season average
3. **Home/Away Splits**: Use actual home/away performance data
4. **Advanced Metrics**: Incorporate usage rate, pace, etc.
5. **Historical Props**: Track which props have hit for calibration

## Summary

The BallDontLie API integration transforms the SGP Builder from a demo system to a production-ready tool with:

✅ Real player statistics
✅ Current roster information
✅ Live injury reports
✅ Accurate projections
✅ Better edge detection
✅ Graceful fallbacks

Get started today by signing up for a free API key at https://www.balldontlie.io!
