# 🚀 HOW TO RUN THE SIMULATOR

## ❌ Your Error Explained

```python
TypeError: 'module' object is not callable
```

This means you tried to call `secure_config(args.config)` but `secure_config` is a module, not a function. The correct function is `load_config(args.config)`.

## ✅ 3 EASY WAYS TO RUN IT

---

## **METHOD 1: Quick Analysis (RECOMMENDED)** ⭐

This is the **easiest** way and uses all 4 improvements:

```bash
# One-time setup (paste your new API key when prompted)
cd /Users/hagiachren/Desktop/quantum-cryptex
python3 nba_fanduel_sim/config/secure_config.py setup

# Run analysis for today's games
python3 run_analysis.py
```

**What it does:**
- ✅ Fetches live NBA odds from FanDuel
- ✅ Analyzes with enhanced Elo model
- ✅ Reality checks all opportunities
- ✅ Shows variance analysis
- ✅ Outputs ranked betting opportunities

---

## **METHOD 2: Direct Quick Analysis**

If you already set up your API key:

```bash
cd /Users/hagiachren/Desktop/quantum-cryptex
python3 nba_fanduel_sim/quick_analyze.py
```

This is the same as Method 1 but without the wrapper.

---

## **METHOD 3: Traditional Main Script**

If you want to use the original simulator with backtesting:

```bash
cd /Users/hagiachren/Desktop/quantum-cryptex

# Generate sample data (first time only)
python3 nba_fanduel_sim/main.py --generate-sample-data

# Run backtest
python3 nba_fanduel_sim/main.py
```

**Note:** This does backtesting on historical data, not live analysis.

---

## 🔧 FIXING YOUR ERROR

If you modified `main.py` and got the error, here's the fix:

**❌ Wrong (causes error):**
```python
from config import secure_config
config = secure_config(args.config)  # ← Error!
```

**✅ Correct:**
```python
from config import load_config
config = load_config(args.config)  # ← Works!
```

OR if you want to use secure config:

```python
from config.secure_config import SecureConfig
secure_config = SecureConfig()
api_key = secure_config.get_api_key('the_odds_api')
```

---

## 📋 STEP-BY-STEP: Run Analysis for Today's Games

### **Step 1: Setup API Key (One-Time)**

```bash
cd /Users/hagiachren/Desktop/quantum-cryptex
python3 nba_fanduel_sim/config/secure_config.py setup
```

**When prompted:**
- Paste your new The Odds API key
- Press Enter
- Key is saved to `~/.nba_simulator/.env`

### **Step 2: Run Today's Analysis**

```bash
python3 run_analysis.py
```

**You'll see:**
```
================================================================================
NBA BETTING SIMULATOR - LIVE ANALYSIS
================================================================================

📡 Step 1: Loading API key...
✅ API key found: abcd1234...xyz9

📊 Step 2: Fetching live NBA odds from FanDuel...
✅ Found 7 NBA games

🧮 Step 3: Initializing enhanced Elo model...

🔍 Step 4: Analyzing games with reality checks...
================================================================================

🎯 FOUND 3 POTENTIAL OPPORTUNITIES
================================================================================

#1. Cleveland Cavaliers @ Philadelphia 76ers
    ML: +116 / -136
    Spread: -2.5
    Model Prob: 61.3%
    Market Prob: 57.6%
    Edge: +3.7%
    Raw EV: +7.2%

    Reality Check: PROCEED WITH CAUTION
    Adjusted EV: +5.4%

    ⚠️  Warnings:
        [MODERATE] Edge of 3.7% is significant

--------------------------------------------------------------------------------

📉 VARIANCE ANALYSIS FOR RECOMMENDED BETS
================================================================================

Portfolio: 3 bets at $100 each = $300 total risk

Expected Profit:     $18
Probability Profit:  65.2%
Probability Loss:    34.8%

Best 5%:   $250+
Median:    $15
Worst 5%:  -$200

✅ ANALYSIS COMPLETE
```

---

## 🎯 WHAT EACH SCRIPT DOES

| Script | Purpose | Use When |
|--------|---------|----------|
| `run_analysis.py` | **Live game analysis** | You want today's betting opportunities |
| `quick_analyze.py` | Same as above | API key already set up |
| `main.py` | Historical backtesting | You want to test strategies on past data |
| `demo_improvements.py` | Show all 4 improvements | You want to understand features |

---

## 🔥 RECOMMENDED WORKFLOW

### **Daily Routine:**

```bash
# Morning: Check today's games
python3 run_analysis.py

# Review output
# - Identify +EV opportunities
# - Check reality warnings
# - Review variance analysis

# Make informed decisions
# (Not automated - you decide!)
```

### **Weekly Review:**

```python
# Track your bets
from evaluation.market_efficiency import MarketEfficiencyAnalyzer

analyzer = MarketEfficiencyAnalyzer()
report = analyzer.generate_efficiency_report(your_bet_history)
print(report)
```

---

## 💡 PRO TIPS

1. **Run analysis 2-3 hours before games start**
   - Lines are more stable
   - You have time to research

2. **Always check injury reports manually**
   - The model uses static Elo ratings
   - Update for new injuries

3. **Compare with multiple sources**
   - Don't blindly follow any model
   - Use as one input in your decision

4. **Track everything**
   - Every bet you place
   - Actual outcomes
   - Weekly efficiency reports

---

## 🚨 IF YOU GET ERRORS

### **"API key not found"**
```bash
python3 nba_fanduel_sim/config/secure_config.py setup
```

### **"Module not found"**
```bash
cd /Users/hagiachren/Desktop/quantum-cryptex
pip install -r requirements.txt
```

### **"Permission denied"**
```bash
chmod +x run_analysis.py
python3 run_analysis.py
```

### **"TypeError: 'module' object is not callable"**
You modified `main.py` incorrectly. Use `run_analysis.py` instead.

---

## ✅ QUICK START CHECKLIST

- [ ] Navigate to project directory
- [ ] Run: `python3 nba_fanduel_sim/config/secure_config.py setup`
- [ ] Enter your API key when prompted
- [ ] Run: `python3 run_analysis.py`
- [ ] Review output and make decisions

---

## 🎓 NEXT LEVEL

Once you're comfortable:

1. **Update Elo ratings** in `quick_analyze.py`
2. **Add real injury data** (scrape from ESPN/NBA.com)
3. **Track bet history** and generate reports
4. **Adjust thresholds** based on your results
5. **Build your own models** using the framework

---

Ready to start? Run:
```bash
python3 run_analysis.py
```
