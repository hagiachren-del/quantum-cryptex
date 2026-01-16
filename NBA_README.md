# NBA FanDuel Betting Simulator

A comprehensive research and simulation platform for modeling **FanDuel Sportsbook NBA markets**, with a focus on **expected value (EV)**, **probability modeling**, and **bankroll management**.

> **⚠️ IMPORTANT**: This system is for **simulation and research only**. It is **NOT** for live betting automation or scraping. Sports betting involves significant risk, and sportsbooks limit or ban winning players.

---

## Table of Contents

1. [Overview](#overview)
2. [FanDuel Assumptions](#fanduel-assumptions)
3. [Project Structure](#project-structure)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [How It Works](#how-it-works)
7. [Configuration](#configuration)
8. [Adding New Models](#adding-new-models)
9. [Understanding the Results](#understanding-the-results)
10. [Limitations](#limitations)
11. [FAQ](#faq)

---

## Overview

This simulator models NBA betting strategies on **FanDuel Sportsbook** by:

* **Ingesting** historical NBA game data and FanDuel-formatted odds
* **Estimating** true win probabilities using Elo ratings and/or machine learning
* **Identifying** mispriced FanDuel lines (positive expected value)
* **Simulating** bet placement under FanDuel-style constraints
* **Tracking** realistic performance metrics (ROI, Sharpe ratio, drawdown)
* **Allowing** modular experimentation with different models and strategies

### What This System Does

- Backtests betting strategies on historical data
- Evaluates probability models against FanDuel odds
- Calculates optimal bet sizing using Kelly Criterion
- Tracks bankroll performance with realistic constraints
- Generates comprehensive performance reports

### What This System Does NOT Do

- Real-time betting automation
- Live odds scraping
- Parlays or Same Game Parlays (V1)
- Player props (V1)
- Arbitrage between sportsbooks
- Violate sportsbook terms of service

---

## FanDuel Assumptions

### How FanDuel Odds Work

FanDuel uses **American odds** format:

- **Negative odds** (e.g., -110): Favorite. Bet $110 to win $100.
- **Positive odds** (e.g., +150): Underdog. Bet $100 to win $150.

### Vig (Juice)

FanDuel builds a profit margin into all markets. For a typical NBA game:

- Both sides of a spread might be priced at **-110**
- This creates implied probabilities that sum to ~**104.8%** (not 100%)
- The extra ~**4.8%** is the sportsbook's edge (vig/juice)

**This simulator removes vig** to estimate the "fair" market probability, then compares model probabilities to find +EV opportunities.

### Typical FanDuel NBA Pricing

| Market | Typical Pricing |
|--------|----------------|
| **Spread** | -110 / -110 (sometimes -108 / -112) |
| **Moneyline** | Varies widely based on team strength |
| **Total (Over/Under)** | -110 / -110 (V1 excludes totals) |

### FanDuel vs. "Fair" Odds

- FanDuel odds represent **what you can bet at**, not necessarily **true probabilities**
- Sharp bettors win by finding games where their model disagrees with FanDuel's pricing
- The simulator tries to beat **FanDuel's lines**, not the actual games

---

## Project Structure

```
nba_fanduel_sim/
│
├── data/
│   ├── raw/                    # Raw data files
│   ├── processed/              # Processed data (optional)
│   ├── __init__.py
│   └── loaders.py              # Data loading utilities
│
├── models/
│   ├── __init__.py
│   ├── base_model.py           # Abstract base class
│   ├── elo_model.py            # Elo rating system (primary)
│   └── logistic_model.py       # Logistic regression
│
├── odds/
│   ├── __init__.py
│   ├── fanduel_odds_utils.py  # Odds conversion utilities
│   └── vig_removal.py          # Vig removal methods
│
├── strategy/
│   ├── __init__.py
│   ├── ev_strategy.py          # EV detection
│   └── bet_sizing.py           # Kelly criterion, flat stakes
│
├── simulator/
│   ├── __init__.py
│   ├── backtester.py           # Main backtesting engine
│   └── bankroll.py             # Bankroll management
│
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py              # Performance metrics
│   └── reports.py              # Report generation
│
├── config/
│   ├── __init__.py
│   └── settings.yaml           # Configuration file
│
├── main.py                     # Main entry point
└── __init__.py
```

---

## Installation

### Requirements

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

Required packages:
- `numpy` - Numerical computing
- `pandas` - Data manipulation
- `scipy` - Statistical functions
- `scikit-learn` - Machine learning models
- `PyYAML` - Configuration files

3. **Verify installation:**

```bash
python -c "import numpy, pandas, sklearn; print('Dependencies installed successfully')"
```

---

## Quick Start

### 1. Generate Sample Data

The simulator includes a sample data generator:

```bash
cd nba_fanduel_sim
python main.py --generate-sample-data
```

This creates:
- `data/raw/sample_games.csv` (500 synthetic NBA games)
- `data/raw/sample_fanduel_odds.csv` (corresponding FanDuel odds)

> **Note**: This is **synthetic data** for testing. Replace with real historical data for actual analysis.

### 2. Run a Backtest

```bash
python main.py
```

This will:
1. Load sample data
2. Initialize Elo model
3. Run chronological backtest
4. Display performance summary
5. Save results to `results/`

### 3. View Results

Check the `results/` directory for:
- `bet_history.csv` - Every bet placed
- `summary.json` - Performance metrics
- `full_report.txt` - Comprehensive analysis

---

## How It Works

### 1. Data Loading

The system loads two CSV files:

**Games Data** (`games.csv`):
```csv
game_id,date,home_team,away_team,home_score,away_score,home_rest_days,away_rest_days
20240001,2023-10-01,LAL,GSW,112,108,2,1
```

**FanDuel Odds** (`odds.csv`):
```csv
game_id,fanduel_moneyline_home,fanduel_moneyline_away,fanduel_spread,fanduel_spread_odds_home,fanduel_spread_odds_away
20240001,-130,+110,-2.5,-110,-110
```

### 2. Probability Modeling

The **Elo model** (default) maintains team ratings that update after each game:

```
Expected Win Prob = 1 / (1 + 10^(-(home_elo - away_elo + home_adv) / 400))
```

- **Home court advantage**: ~100 Elo points (~3 point spread)
- **K-factor**: Controls update speed (20 is default)
- **Mean reversion**: Ratings partially reset between seasons

### 3. Expected Value Detection

For each game, the system:

1. **Predicts** home win probability using the model
2. **Removes vig** from FanDuel odds to get fair probability
3. **Calculates EV**:
   ```
   EV = (Model_Prob × Profit) - ((1 - Model_Prob) × Stake)
   ```
4. **Flags bet** if EV > threshold (default 2%)

### 4. Bet Sizing

Using **Fractional Kelly Criterion** (default 1/4 Kelly):

```
Kelly% = (Probability × Decimal_Odds - 1) / (Decimal_Odds - 1)
Stake = Bankroll × Kelly% × Kelly_Fraction
```

Constraints applied:
- Max 5% of bankroll per bet
- Max 10% total exposure per game
- Minimum $10 per bet
- Max 10 bets per day

### 5. Chronological Processing

**Critical**: Games are processed in date order to prevent lookahead bias:

```python
for game in games:  # sorted by date
    prediction = model.predict(game)  # Uses only past data
    opportunities = find_ev(game, prediction)
    place_bets(opportunities)
    model.update(game)  # Update AFTER betting
```

### 6. Performance Tracking

Metrics calculated:
- **ROI**: Return on investment
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: Worst peak-to-trough decline
- **Win Rate**: Percentage of bets won
- **Calibration**: Are probabilities accurate?

---

## Configuration

All settings are in `config/settings.yaml`.

### Key Settings

**Model Selection:**
```yaml
model:
  type: "elo"  # Options: "elo", "logistic", "logistic_with_elo"
```

**Bet Sizing:**
```yaml
bankroll:
  initial_bankroll: 10000.0
  sizing_method: "fractional_kelly"  # or "flat", "kelly"
  kelly_fraction: 0.25  # 1/4 Kelly (conservative)
```

**Strategy:**
```yaml
strategy:
  min_ev: 0.02  # 2% minimum EV
  min_edge: 0.01  # 1% minimum edge
```

**Data Filtering:**
```yaml
data:
  start_date: "2023-10-01"  # YYYY-MM-DD
  end_date: "2024-04-15"
  seasons: [2024]  # Or null for all
```

See `config/settings.yaml` for full documentation.

---

## Adding New Models

All models must implement the `BaseModel` interface:

```python
from models.base_model import BaseModel

class MyModel(BaseModel):
    def fit(self, data: List[Dict[str, Any]]) -> None:
        """Train on historical data."""
        pass

    def predict_proba(self, game_row: Dict[str, Any]) -> float:
        """Predict home win probability."""
        return 0.5  # Placeholder

    def update(self, game_row: Dict[str, Any]) -> None:
        """Update after game completes (optional)."""
        pass
```

Then update `main.py` to instantiate your model.

---

## Understanding the Results

### Sample Output

```
======================================================================
NBA FANDUEL BETTING SIMULATOR - BACKTEST RESULTS
======================================================================

CONFIGURATION
----------------------------------------------------------------------
Model:              Elo
Initial Bankroll:   $10,000.00
Bet Sizing:         fractional_kelly
Kelly Fraction:     0.25
Min EV Threshold:   2.0%

GAME STATISTICS
----------------------------------------------------------------------
Games Processed:    500
Bets Attempted:     47
Bets Placed:        45
Bets Rejected:      2
Bet Rate:           9.0% (bets per game)

BANKROLL PERFORMANCE
----------------------------------------------------------------------
Initial Bankroll:   $10,000.00
Final Bankroll:     $10,523.45
Peak Bankroll:      $10,892.13
Total Profit:       $523.45
Profit %:           +5.23%

BETTING STATISTICS
----------------------------------------------------------------------
Total Bets:         45
Wins:               25
Losses:             20
Win Rate:           55.56%
Total Staked:       $8,234.12
ROI:                +6.35%
Profit Factor:      1.142

RISK METRICS
----------------------------------------------------------------------
Current Drawdown:   0.00%
Max Drawdown:       8.42%
```

### Key Metrics Explained

- **ROI**: Profit per dollar wagered (not per dollar of bankroll)
- **Profit Factor**: Total wins / total losses (>1.0 = profitable)
- **Sharpe Ratio**: Risk-adjusted return (>1.0 is good, >2.0 is excellent)
- **Max Drawdown**: Worst decline from peak (lower is better)
- **Calibration Error**: How accurate are probabilities? (<5% is good)

---

## Limitations

### 1. Market Efficiency

NBA betting markets are **highly efficient**. Consistent +EV is extremely difficult to find in reality.

### 2. Sample Size

Even 500 games is a small sample. Variance is high. A profitable backtest doesn't guarantee future success.

### 3. Sportsbook Limits

**FanDuel limits winning players**. If you consistently beat closing lines, expect:
- Bet limits reduced (often to $50-$300)
- Account restrictions
- Delayed grading
- Potential account closure

### 4. Closing Lines vs. Opening Lines

This simulator uses **closing lines**. In reality:
- You must bet before the line moves
- Closing lines incorporate all information
- Beating closing lines is much harder than backtests suggest

### 5. Execution Slippage

Real-world betting involves:
- Lines moving while you place bets
- Bets rejected due to stake limits
- Odds changing between viewing and confirmation

### 6. No Parlays/Props (V1)

This version excludes:
- Parlays and Same Game Parlays
- Player props
- Alternate lines
- Live betting
- Promotions and boosts

### 7. Data Quality

Results depend entirely on data quality:
- Accurate historical odds (closing lines)
- Correct game outcomes
- No retroactive line adjustments

---

## FAQ

### Q: Can this make me money on FanDuel?

**A**: This is a **research tool**, not a money-making system. Real-world sports betting is:
- Highly competitive
- Subject to limits
- High variance
- Requires deep domain knowledge

Even profitable models may lose over extended periods due to variance.

### Q: Why use Elo instead of advanced ML?

**A**: Elo is:
- Transparent and interpretable
- Computationally efficient
- Resistant to overfitting
- Updates sequentially (ideal for backtesting)

Advanced ML often doesn't outperform Elo enough to justify complexity.

### Q: What's the difference between "edge" and "EV"?

- **Edge**: Difference between your probability and fair market probability
- **EV**: Expected profit in dollars (accounts for odds and stake)

A bet can have positive edge but negative EV if the odds are too unfavorable.

### Q: How do I get real FanDuel odds data?

Options:
1. **Historical odds providers** (e.g., Odds Portal, Sports Odds History)
2. **Web scraping** (check FanDuel's Terms of Service first)
3. **Third-party APIs** (e.g., The Odds API, Odds Jam)

**Important**: Never automate live betting or violate FanDuel's Terms of Service.

### Q: Should I use full Kelly or fractional Kelly?

**Fractional Kelly** (1/4 to 1/2) is recommended:
- Reduces variance
- Protects against model errors
- Still achieves strong long-term growth

Full Kelly is extremely aggressive and can lead to large drawdowns.

### Q: What's a good Sharpe ratio for sports betting?

- **< 0.5**: Poor risk-adjusted returns
- **0.5 - 1.0**: Decent
- **1.0 - 2.0**: Good
- **> 2.0**: Excellent (but verify for overfitting)

For context, the stock market has a Sharpe ratio of ~0.5 historically.

---

## Warning

**Sports betting involves significant risk.** Even with a statistical edge:

1. **Variance is high** - Long losing streaks are normal
2. **Sportsbooks limit winners** - Success leads to restrictions
3. **Past performance ≠ future results** - Markets adapt
4. **Addiction risk** - Only bet what you can afford to lose

This system is for **educational and research purposes only**.

---

## Contributing

To extend this simulator:

1. **Add new models** - Implement `BaseModel` interface
2. **Add new bet types** - Extend `ev_strategy.py`
3. **Improve calibration** - Experiment with vig removal methods
4. **Add visualizations** - matplotlib/seaborn plots

See `TODO.md` for planned features.

---

## License

This project is for educational and research purposes.

**Disclaimer**: Not financial advice. Not affiliated with FanDuel or any sportsbook.

---

## References

- [FiveThirtyEight NBA Elo](https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/)
- [Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion)
- [Vig Removal Methods](https://help.smarkets.com/hc/en-gb/articles/214058369-How-to-calculate-implied-probability-in-betting)
- [Expected Value in Sports Betting](https://www.pinnacle.com/en/betting-articles/Betting-Strategy/expected-value-in-betting/NESCPENKKXQNQJ9Z)

---

**Built for research. Bet responsibly.**
