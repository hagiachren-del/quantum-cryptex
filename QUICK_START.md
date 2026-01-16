# Quick Start Guide - NBA FanDuel Simulator v2.0

## 🚀 Getting Started with Your New API Key

### Step 1: Secure API Key Setup (5 minutes)

Your new API key should be stored securely. **Never paste it in code or conversations!**

```bash
# Navigate to project
cd /home/user/quantum-cryptex/nba_fanduel_sim

# Run secure setup wizard
python config/secure_config.py setup

# Follow prompts:
# - Enter your new The Odds API key
# - Key will be saved to ~/.nba_simulator/.env
# - Permissions automatically set to 600 (owner read/write only)
```

**What this does:**
- ✅ Stores key in environment variable
- ✅ Saves encrypted .env file
- ✅ Updates .gitignore automatically
- ✅ Never commits key to git

### Step 2: Verify Setup (1 minute)

```bash
# Check API key is configured
python config/secure_config.py validate

# Expected output:
# ✅ API key found: abcd1234...xyz9
```

### Step 3: Run the Demo (10 minutes)

See all 4 improvements in action:

```bash
python demo_improvements.py
```

This interactive demo shows:
1. 🔒 Secure API key management
2. 📊 Enhanced Elo model (injuries, form, rest)
3. ⚠️  Market efficiency reality checks
4. 📉 Comprehensive variance analysis

### Step 4: Fetch Live Odds with Improvements

```python
from nba_fanduel_sim.config import SecureConfig
import requests

# Get API key securely
config = SecureConfig()
api_key = config.get_api_key('the_odds_api')

# Fetch live odds
url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
params = {
    'apiKey': api_key,
    'regions': 'us',
    'markets': 'h2h,spreads,totals',
    'bookmakers': 'fanduel',
    'oddsFormat': 'american'
}

response = requests.get(url, params=params)
games = response.json()

print(f"Found {len(games)} NBA games")
```

### Step 5: Analyze with Enhanced Model

```python
from nba_fanduel_sim.models import EnhancedEloModel, STAR_PLAYER_INJURY
from nba_fanduel_sim.evaluation import MarketEfficiencyAnalyzer, VarianceAnalyzer

# Initialize enhanced model
model = EnhancedEloModel()
model.set_rating("Cleveland Cavaliers", 1650)
model.set_rating("Philadelphia 76ers", 1470)

# Account for injuries
sixers_injuries = [
    STAR_PLAYER_INJURY("Joel Embiid", "C"),  # Star player out
]

# Get prediction with all factors
prob = model.predict_win_probability(
    home_team="Philadelphia 76ers",
    away_team="Cleveland Cavaliers",
    home_injuries=sixers_injuries,
    home_rest_days=0,  # Back-to-back
    away_rest_days=2,
    home_back_to_back=True
)

print(f"Cleveland win probability: {(1-prob)*100:.1f}%")

# Reality check the opportunity
analyzer = MarketEfficiencyAnalyzer()
check = analyzer.reality_check_ev_opportunity(
    model_prob=1-prob,
    market_prob=0.463,  # From FanDuel odds
    odds=+116,
    ev_percentage=0.324
)

print(f"Recommendation: {check['recommendation']}")
print(f"Adjusted EV: {check['adjusted_ev']*100:+.1f}%")

# Analyze variance
if check['recommendation'] == 'PROCEED':
    var_analyzer = VarianceAnalyzer()
    bets = [{'model_prob': 1-prob, 'odds': +116, 'stake': 500}]

    sim = var_analyzer.simulate_betting_outcomes(bets, 10000)
    print(f"Win probability: {sim['prob_profit']*100:.1f}%")
    print(f"Expected profit: ${sim['mean_profit']:,.0f}")
```

---

## 📋 Quick Command Reference

### API Key Management
```bash
# Setup new key
python nba_fanduel_sim/config/secure_config.py setup

# Validate key
python nba_fanduel_sim/config/secure_config.py validate

# Delete key
python nba_fanduel_sim/config/secure_config.py delete

# Update .gitignore
python nba_fanduel_sim/config/secure_config.py gitignore
```

### Running Demos
```bash
# All improvements demo
python nba_fanduel_sim/demo_improvements.py

# Enhanced Elo model only
python nba_fanduel_sim/models/enhanced_elo_model.py

# Market efficiency check
python nba_fanduel_sim/evaluation/market_efficiency.py

# Variance analysis
python nba_fanduel_sim/evaluation/variance_analyzer.py
```

### Fetching Live Odds
```bash
# Using your secure API key
python /tmp/advanced_fanduel_analysis.py

# Output: Full analysis with reality checks
```

---

## 🎯 Typical Workflow

### 1. Morning: Setup (One-time)
```bash
python nba_fanduel_sim/config/secure_config.py setup
# Enter your new API key securely
```

### 2. Pre-Game: Fetch & Analyze
```python
# Fetch live odds
odds = fetch_fanduel_odds()

# Enhanced model with injuries
for game in odds:
    prob = enhanced_model.predict_win_probability(
        home_team=game['home'],
        away_team=game['away'],
        home_injuries=get_injuries(game['home']),
        away_injuries=get_injuries(game['away']),
        home_rest_days=game['home_rest'],
        away_rest_days=game['away_rest']
    )

    # Reality check
    check = analyzer.reality_check_ev_opportunity(...)

    if check['recommendation'] == 'PROCEED':
        # Analyze variance
        variance = var_analyzer.simulate_betting_outcomes(...)

        # Make informed decision
        if variance['prob_profit'] > 0.65 and check['adjusted_ev'] > 0.03:
            print(f"✅ PLACE BET: {game}")
```

### 3. Post-Game: Track & Learn
```python
# Log result
result = {
    'bet': bet_info,
    'won': outcome == 'win',
    'profit': profit_amount
}

# Generate efficiency report
report = analyzer.generate_efficiency_report(bet_history)
print(report)
```

---

## ⚠️ Important Reminders

### API Security
- ✅ API key is in `~/.nba_simulator/.env` (never commit!)
- ✅ Check `.gitignore` includes sensitive patterns
- ✅ Rotate key every 3-6 months
- ✅ Use separate keys for dev/prod

### Model Limitations
- 📊 Enhanced Elo is better, but not perfect
- 🏥 Manually verify injury reports
- 📰 Check latest news before betting
- 🔄 Model updates with each game

### Market Efficiency
- 💰 NBA markets are 85-95% efficient
- 🚫 Edges >10% are usually errors
- ⏰ FanDuel limits winning accounts
- 📉 ROI regresses toward market efficiency

### Variance Reality
- 🎲 Short-term results are mostly luck
- 📊 Need 1000+ bets to validate
- 🌊 Losing streaks are normal
- 💪 Bankroll management is critical

---

## 🔧 Troubleshooting

### "API key not found"
```bash
# Re-run setup
python nba_fanduel_sim/config/secure_config.py setup
```

### "Module not found"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "Permission denied on .env"
```bash
# Fix permissions
chmod 600 ~/.nba_simulator/.env
```

### "Import error"
```bash
# Ensure you're in correct directory
cd /home/user/quantum-cryptex
python -m nba_fanduel_sim.demo_improvements
```

---

## 📚 Documentation

- **IMPROVEMENTS.md** - Full documentation of all 4 improvements
- **NBA_README.md** - Original simulator documentation
- **requirements.txt** - Python dependencies
- Module docstrings - Detailed API reference

---

## 🎓 Learning Path

**Beginner** (Day 1-2):
1. Run `demo_improvements.py`
2. Read IMPROVEMENTS.md
3. Understand variance analysis output

**Intermediate** (Week 1):
1. Fetch live odds with secure API key
2. Experiment with enhanced Elo adjustments
3. Practice reality checks on opportunities

**Advanced** (Ongoing):
1. Track bet history and analyze efficiency
2. Refine injury impact estimates
3. Develop your own models
4. Integrate multiple data sources

---

## 💡 Pro Tips

1. **Start Small**: Use small stakes until you understand variance
2. **Keep Records**: Track every bet with outcomes
3. **Review Weekly**: Analyze what worked and what didn't
4. **Stay Disciplined**: Don't chase losses or increase stakes emotionally
5. **Accept Limits**: FanDuel will limit you if you win consistently
6. **Diversify**: Don't rely on one sportsbook
7. **Continuous Learning**: Markets evolve, so should your models

---

## ✅ Next Steps

Now that you have secure API access and enhanced models:

1. ✅ Run the demo to understand improvements
2. ✅ Fetch today's NBA games with live odds
3. ✅ Analyze with enhanced Elo (injuries, form, rest)
4. ✅ Reality check all opportunities (market efficiency)
5. ✅ Understand variance before placing bets
6. ✅ Start with small stakes and track results
7. ✅ Review efficiency reports weekly

**Remember**: This is a research tool for understanding sports betting markets, not a guaranteed profit system. Bet responsibly!

---

**Ready to start?**
```bash
python nba_fanduel_sim/demo_improvements.py
```
