# Same Game Parlay (SGP) Builder Guide

## Overview

The SGP Builder is a comprehensive system for analyzing NBA player props and building optimal Same Game Parlay combinations. It includes:

✅ **Live player prop odds** from The Odds API
✅ **Player performance projections** with injury/matchup/rest factors
✅ **Correlation analysis** for SGP pricing
✅ **Monte Carlo simulations** showing profit distributions
✅ **Probability visualizations** comparing model vs market
✅ **Reality checks** to filter unrealistic edges

## Quick Start

### Run Full SGP Analysis

```bash
python3 sgp_production_run.py YOUR_API_KEY
```

This will:
1. Fetch all player props (points, rebounds, assists, threes)
2. Project each player's performance
3. Identify positive EV individual props
4. Build optimal SGP combinations
5. Run Monte Carlo simulations on all opportunities
6. Display detailed analysis with visualizations

## What You Get

### 1. Individual Player Props Analysis

For each prop with positive EV, you'll see:

```
🏀 Stephen Curry - POINTS OVER 27.5
================================================================================

Projection: 29.2 (Line: 27.5)
Best Side: OVER (-110)
Model Probability: 64.3%
Edge: +11.9%

📊 Stephen Curry points over
======================================================================
Model  ( 64.3%): │████████████████████████████████                  │
Market ( 52.4%): │░░░░░░░░░░░░░░░░░░░░░░░░░░                        │

Edge: +11.9% ↑↑↑↑↑↑↑↑↑↑

🎲 MONTE CARLO SIMULATION (10,000 trials)
--------------------------------------------------------------------------------
  Expected Profit:       $   23.45
  Median Outcome:        $   90.91
  Probability of Win:    64.1%

  Best Case (95th):      +$  90.91
  Worst Case (5th):      $-100.00
```

### 2. Same Game Parlay Combinations

For optimal parlay builds:

```
🎯 SAME GAME PARLAY (3 LEGS) - +450 ODDS
================================================================================

Parlay Legs:
  1. LeBron James points over 25.5 (-110)
  2. LeBron James assists over 7.5 (-110)
  3. Anthony Davis rebounds over 10.5 (-110)

CORRELATION ANALYSIS
--------------------------------------------------------------------------------
  Naive Probability (independent):  18.2%
  True Probability (correlated):    16.8%
  Correlation Impact:                -1.4%

  Implied Probability (odds):        18.2%
  Edge:                              -1.4%
  Adjusted EV:                       -5.2%

🎲 MONTE CARLO SIMULATION (10,000 trials)
--------------------------------------------------------------------------------
  Expected Profit:       $  -5.20
  Median Outcome:        $-100.00
  Probability of Win:    16.5%
```

## Understanding Correlations

### Why Correlations Matter

**Without correlation adjustment:**
- 3 bets at 55% each = 16.6% parlay win rate
- Looks like fair +500 odds

**With correlation adjustment:**
- Negative correlation (teammates) reduces to 14.2%
- Now -EV at +500 odds

### Correlation Types

#### 1. **Same Player Props** (Varies by combination)

**Points vs Threes: +0.40**
- More 3-pointers directly = more points
- Strong positive correlation

**Points vs Assists: -0.15**
- Ball-dominant scorers assist less
- Slight negative correlation

**Points vs Rebounds: +0.20**
- Both benefit from playing time
- Moderate positive correlation

#### 2. **Teammate Props** (Generally Negative)

**Teammate Scoring: -0.20**
- Limited possessions per game
- If one teammate scores more, others score less

**Teammate Rebounds: -0.30**
- Only one player can get each rebound
- Strong negative correlation

**Teammate Assists: -0.10**
- Multiple players can assist same basket
- Weak negative correlation

#### 3. **Opponent Props** (Generally Positive)

**Opponent Scorers: +0.25**
- High-pace games benefit both teams
- Positive correlation

**Opponent Mixed Stats: +0.15**
- Game flow affects all players
- Moderate positive correlation

## Player Stats Model

### How It Works

The model projects player performance using:

```
Projected Stats = Base Average × Injury Factor × Matchup Factor × Rest Factor × Home/Away Factor
```

### Adjustment Factors

#### 1. **Injury Factor** (0.0 - 1.0)

| Status | Factor | Impact |
|--------|--------|--------|
| Healthy | 1.00 | No adjustment |
| Probable | 0.92 | -8% expected stats |
| Questionable | 0.85 | -15% expected stats |
| Doubtful | 0.70 | -30% expected stats |
| Out | 0.00 | Cannot play |

#### 2. **Matchup Factor** (0.85 - 1.15)

- **Elite defense (0.85)**: -15% to offensive stats
- **Average defense (1.00)**: No adjustment
- **Poor defense (1.15)**: +15% to offensive stats

#### 3. **Rest Factor** (0.92 - 1.02)

| Days Rest | Factor | Impact |
|-----------|--------|--------|
| Back-to-back | 0.92 | Fatigue -8% |
| 1 day | 0.98 | Slight fatigue -2% |
| 2 days | 1.00 | Normal |
| 3+ days | 1.02 | Extra rest +2% |

#### 4. **Home/Away Factor** (0.97 - 1.03)

| Location | Scoring Stats | Other Stats |
|----------|---------------|-------------|
| Home | 1.03 (+3%) | 1.01 (+1%) |
| Away | 0.97 (-3%) | 0.99 (-1%) |

## Example Analysis

### Scenario: Lakers @ Warriors

**Player:** Stephen Curry
**Prop:** Points Over 27.5 (-110)
**Context:**
- Home game
- 1 day rest
- Facing Lakers (average defense)
- Healthy

**Calculation:**

```
Base Average: 29.0 points
Injury Factor: 1.00 (healthy)
Matchup Factor: 1.00 (average defense)
Rest Factor: 0.98 (1 day rest)
Home/Away Factor: 1.03 (home advantage for scoring)

Projected = 29.0 × 1.00 × 1.00 × 0.98 × 1.03 = 29.3 points
```

**Analysis:**
- Line: 27.5
- Projection: 29.3
- Difference: +1.8 points
- Standard Deviation: 7.5 points
- Z-score: (29.3 - 27.5) / 7.5 = 0.24
- Over Probability: 59.5%

**Market:**
- Odds: -110
- Implied: 52.4%
- Fair (vig-removed): 50.0%

**Edge:**
- 59.5% - 50.0% = +9.5% edge
- Positive EV!

## Monte Carlo Simulations

### Individual Props

Each prop is simulated 10,000 times:

```python
for trial in range(10000):
    won = random() < model_probability
    if won:
        profit = calculate_win_profit(odds)
    else:
        profit = -stake
```

**What You Learn:**
- Expected profit (mean)
- Probability of winning
- Range of outcomes (5th to 95th percentile)
- Profit distribution shape

### Same Game Parlays

SGPs account for correlations:

```python
for trial in range(10000):
    # Simulate correlated outcomes
    won = random() < true_probability_with_correlations
    if won:
        profit = calculate_parlay_payout(odds)
    else:
        profit = -stake
```

**Key Insight:**
- Correlation can significantly change parlay probability
- Bookmakers price in correlations
- True edges in SGPs are rare

## Best Practices

### 1. **Check Injury Reports**

**CRITICAL:** Always verify latest injury status before betting.

- NBA injury reports update 90 minutes before tipoff
- Players can be late scratches
- Injury status changes invalidate entire analysis

### 2. **Start with Individual Props**

- Individual props are easier to find value in
- Less complex than SGPs
- Good for building track record

### 3. **Be Selective with SGPs**

- Most SGP combinations are -EV
- Bookmakers have sophisticated pricing
- Only bet when correlation analysis shows clear edge

### 4. **Bankroll Management**

**For Individual Props:**
- Use 1/4 Kelly sizing
- Risk 1-3% of bankroll per bet
- Diversify across multiple props

**For SGPs:**
- Use even smaller sizing (1/8 Kelly)
- Higher variance than single bets
- Never more than 1-2% of bankroll

### 5. **Track Your Results**

```bash
python3 log_bet_results.py
```

- Log all props and SGPs
- Track win rate by prop type
- Monitor model calibration
- Adjust strategy based on results

## Common Pitfalls

### ❌ Ignoring Correlations

**Mistake:** Building 3-leg SGP with teammates' scoring props

```
LeBron points over
Anthony Davis points over
D'Angelo Russell points over
```

**Problem:** All three compete for the same possessions. Negative correlation makes this much less likely than assuming independence.

**Better:** Mix opponent props or different stat types

```
LeBron points over
Anthony Davis rebounds over
Stephen Curry (opponent) assists over
```

### ❌ Chasing Big Payouts

**Mistake:** Building 5-leg parlay for +2000 odds

**Problem:**
- Even at 60% per leg, true probability ~7.8%
- With correlations, likely <7%
- Bookmaker prices at 4.8% (implied)
- Variance is massive

**Better:** 2-3 leg parlays with strong individual edges

### ❌ Overestimating Edges

**Mistake:** Betting every prop with >5% model edge

**Problem:**
- Player props markets are ~80-85% efficient
- True edges >10% are extremely rare
- Model uncertainty is high

**Better:** Require >10% edge after reality checks

### ❌ Not Accounting for Blowouts

**Situation:** Star player typically plays 36 minutes

**Problem:** If game is blowout, might only play 24 minutes

**Impact:**
- Points prop over becomes unlikely
- Rebounds/assists also affected
- No way to predict blowouts accurately

**Better:** Consider player's role - starters in close games safer

## API Usage

### Player Prop Markets

The system fetches these markets:

1. **player_points** - Points over/under
2. **player_rebounds** - Total rebounds over/under
3. **player_assists** - Assists over/under
4. **player_threes** - Three-pointers made over/under
5. **player_points_rebounds_assists** - Combo prop

### API Costs

Each market = 1 API request

**Full analysis (4 markets):**
- 4 API requests
- With 500 requests/month free tier
- Can run ~125 full analyses per month

## Interpreting Results

### When to Bet

✅ **Individual Prop:**
- Adjusted EV > 10%
- Model probability > 55%
- Reality check: PROCEED or PROCEED WITH CAUTION
- Monte Carlo shows >60% win rate

✅ **Same Game Parlay:**
- Positive correlation impact OR
- Each leg has strong individual edge
- Parlay odds > true probability
- Adjusted EV > 5%

### When to Pass

❌ **Individual Prop:**
- Edge < 5%
- Reality check warnings about unrealistic edge
- Injury status uncertain
- Late scratch possible

❌ **Same Game Parlay:**
- Negative correlation reducing probability
- Building parlay just for big payout
- Weak individual leg edges
- More than 3-4 legs

## Comparison to Game-Level Betting

| Aspect | Game Betting | Player Props | Same Game Parlays |
|--------|--------------|--------------|-------------------|
| Market Efficiency | 90-95% | 80-85% | 85-90% |
| Variance | Medium | High | Very High |
| Edge Opportunities | Rare | Moderate | Rare |
| Information Edge | Minimal | Injuries critical | Complex |
| Bankroll Sizing | 2-5% | 1-3% | 0.5-2% |
| Sample Size Needed | 100+ | 200+ | 300+ |

## Advanced: Correlation Matrix

For 3+ leg parlays, the system builds a correlation matrix:

```
           Leg1   Leg2   Leg3
Leg1       1.00  -0.20   0.15
Leg2      -0.20   1.00  -0.25
Leg3       0.15  -0.25   1.00
```

This is used to estimate true parlay probability via multivariate normal approximation.

## Real Example

**Date:** January 17, 2026
**Game:** Lakers @ Warriors

**Props Analyzed:**
1. LeBron James Points O 25.5 (-110)
2. Stephen Curry Points O 27.5 (-110)
3. Anthony Davis Rebounds O 11.5 (-110)

**Individual Analysis:**
- LeBron: 58% model prob vs 52% market = +6% edge ✅
- Curry: 62% model prob vs 52% market = +10% edge ✅
- AD: 54% model prob vs 52% market = +2% edge ❌

**SGP Analysis (LeBron + Curry):**
```
Correlation: Opponents, both scoring = +0.25
Naive probability: 58% × 62% = 36.0%
True probability: 36.0% × 1.025 = 36.9%
Parlay odds: +165 (implied 37.7%)
Edge: 36.9% - 37.7% = -0.8% ❌
```

**Result:** Skip the parlay, take individual Curry prop.

## Conclusion

The SGP Builder provides comprehensive analysis of player props and same game parlays with:

- **Sophisticated modeling** of player performance
- **Correlation analysis** for accurate SGP pricing
- **Monte Carlo simulations** showing true variance
- **Reality checks** preventing overconfidence

Remember:
- Player props have higher variance than game bets
- SGPs are complex and bookmakers price them well
- Injury information is critical
- Track results to validate your edge

Good luck! 🍀
