# Historical Performance Tracking Guide

## Overview

The NBA betting simulator now includes a comprehensive historical performance tracking system. This allows you to:

- **Log all bet recommendations** with full details (odds, edge, EV, etc.)
- **Track outcomes** (win/loss/push)
- **Analyze performance** over time
- **Calculate statistics** like win rate, ROI, Sharpe ratio
- **Monitor model calibration** to ensure predictions remain accurate

## Quick Start

### 1. View Current Performance

```bash
python3 view_performance.py
```

This displays:
- Overall win rate and ROI
- Performance breakdown by bet type (ML, spread, totals)
- Performance by edge size
- Longest streaks
- Model calibration analysis
- ROI over time

### 2. Log Your Initial Results

Your first production run went **4/4 (100% win rate)**:

```bash
python3 log_bet_results.py --init
```

This logs:
1. Sacramento Kings -7.0 (-110) ✅
2. Houston Rockets -4.5 (-110) ✅
3. Indiana Pacers -3.5 (-114) ✅
4. Cleveland Cavaliers ML (+116) ✅

Total profit: **$385.54** on **$400** staked = **+96.38% ROI**

### 3. Add Future Bets

Use the interactive menu:

```bash
python3 log_bet_results.py
```

Options:
1. Log new bet (before game starts)
2. Update bet outcome (after game finishes)
3. Show performance report
4. Exit

## Understanding Your Performance Report

### Overall Performance

```
Total Bets Placed:     4
Wins:                  4
Losses:                0
Win Rate:              100.0%
Total Profit/Loss:     $385.54
ROI:                   +96.38%
```

**What it means:**
- You've won all 4 bets
- Made $385.54 profit on $400 staked
- 96.38% return on investment

**Important caveat:**
- Sample size is small (4 bets)
- Results are heavily influenced by variance
- Need 50+ bets to assess true edge

### Model Calibration

```
Expected Win Rate:     61.5% (based on model probs)
Actual Win Rate:       100.0%
Calibration Error:     38.5%
```

**What it means:**
- The model predicted ~62% win rate across your bets
- You actually won 100%
- 38.5% difference shows **short-term variance**

**What to expect:**
- With more bets, actual win rate should converge to expected
- Calibration error should drop below 10%
- Current error is HIGH because sample size is small

### Performance by Bet Type

```
Type            Bets   Win%     ROI        Profit
moneyline       1      100.0%   +116.0%    $116.00
spread          3      100.0%   +89.8%     $269.54
```

**What it means:**
- Spreads: 3 bets, all won, 89.8% ROI
- Moneylines: 1 bet, won, 116% ROI

**Tracking value:**
- Helps identify which bet types are most profitable
- May reveal strengths/weaknesses in the model

### Performance by Edge Size

```
Edge Range      Bets   Win%     ROI        Profit
5-10% edge      2      100.0%   +89.3%     $178.63
10-15% edge     2      100.0%   +103.5%    $206.91
```

**What it means:**
- Bets with 5-10% edge: 2 bets, both won
- Bets with 10-15% edge: 2 bets, both won

**Tracking value:**
- Validates that larger edges correlate with better returns
- Over time, should see win rate increase with edge size

### Streaks

```
Longest Win Streak:    4 bets
Longest Loss Streak:   0 bets
Current Streak:        4 WIN
```

**What it means:**
- You're on a 4-bet winning streak (your only streak so far!)

**Psychological value:**
- Helps prepare for inevitable cold streaks
- Even with 60% win rate, expect 5+ bet losing streaks

### Sharpe Ratio

```
Sharpe Ratio:          8.455
```

**What it means:**
- Sharpe ratio measures risk-adjusted returns
- Higher = better returns relative to volatility
- **8.45 is extremely high** (but based on small sample)

**Benchmarks:**
- \>1.0 = excellent
- \>0.5 = good
- \>0 = positive

**Reality check:**
- Your 8.45 is inflated by 4/4 start
- Expect this to decline toward 0.5-1.5 range over time

## How to Use Going Forward

### After Each Production Run

1. **Immediately after getting bet recommendations:**

```bash
python3 log_bet_results.py
```

Select option 1 (Log new bet) and enter:
- Teams
- Bet type
- Odds
- Stake
- Model probability (if available)

2. **After games finish:**

```bash
python3 log_bet_results.py
```

Select option 2 (Update bet outcome):
- Choose the bet
- Enter outcome (win/loss/push)
- Add description

3. **View updated stats:**

```bash
python3 view_performance.py
```

### Weekly/Monthly Reviews

Run the performance report to:
- Check if win rate is tracking to model expectations
- Identify which bet types are most profitable
- Monitor ROI trends over time
- Ensure model remains calibrated

## Data Storage

All bets are stored in:
```
bet_history.json
```

**Backup recommended:**
```bash
cp bet_history.json bet_history_backup_$(date +%Y%m%d).json
```

## Expected Long-Term Performance

Based on the simulator's approach:

### Win Rate Expectations

**By Bet Type:**
- Spreads: 52-56% (need 52.4% to break even at -110)
- Moneylines: 55-60% (varies by odds)
- Totals: 53-57%

**Overall:**
- Target: 55-58% win rate
- Minimum profitable: 52.4% at -110 odds

### ROI Expectations

**Realistic targets:**
- Year 1: 3-8% ROI (learning phase)
- Year 2+: 5-12% ROI (refined model)
- Elite: 10-15% ROI (rare, sustainable)

**Your current 96% ROI:**
- Unsustainable (variance)
- Expect regression toward 5-10% range
- Still excellent if you maintain 8-12%

### Variance Expectations

**Over 100 bets:**
- Expect 10-15 bet losing streaks
- Expect drawdowns of 20-30% of bankroll
- Expect 40-45 losses even with 55% win rate

**Psychological preparation:**
- Losing streaks are normal
- Don't chase losses with bigger bets
- Trust the process over large samples

## Key Metrics to Watch

### 1. Win Rate vs Expected

**Healthy:**
- Within 5% of model expectation

**Concerning:**
- \>10% below expectation after 50+ bets
- May indicate model drift or market adaptation

### 2. ROI Trend

**Healthy:**
- Positive and stable
- Small fluctuations around mean

**Concerning:**
- Consistent downward trend
- May indicate market efficiency increasing

### 3. Model Calibration

**Healthy:**
- Calibration error <5% after 100+ bets
- Actual win rate ≈ expected win rate

**Concerning:**
- Calibration error >10% persistently
- Model may need retraining

## Export Options

### Export to CSV

From Python:
```python
from tracking.bet_tracker import BetTracker

tracker = BetTracker("bet_history.json")
tracker.export_to_csv("my_bets.csv")
```

Opens in Excel/Google Sheets for further analysis.

## Advanced Analytics

The tracking system also supports:

- **ROI over time**: See cumulative profit chart
- **Performance by team**: Which teams are most profitable
- **Performance by date**: Identify hot/cold periods
- **Edge bucket analysis**: Validate edge → profit correlation

## Congratulations on 4/4! 🎉

Your initial production run was perfect. This tracking system will help you:

1. **Validate** the model's edge over time
2. **Identify** profitable patterns
3. **Avoid** overbetting during hot streaks
4. **Maintain** discipline during cold streaks

Remember: **Sample size matters.** 4 bets is a great start, but 100+ bets is needed to truly validate the approach.

Keep logging, keep analyzing, and trust the math over large samples!
