#!/usr/bin/env python3
"""
Demonstration of 4 Key Improvements to NBA Betting Simulator

1. Secure API Key Management
2. Enhanced Elo Model (injuries, form, rest)
3. Market Efficiency Reality Checks
4. Comprehensive Variance Analysis
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

from config.secure_config import SecureConfig
from models.enhanced_elo_model import (
    EnhancedEloModel,
    STAR_PLAYER_INJURY,
    STARTER_INJURY
)
from evaluation.market_efficiency import MarketEfficiencyAnalyzer
from evaluation.variance_analyzer import VarianceAnalyzer


def demo_1_secure_api_keys():
    """Demo 1: Secure API Key Management"""
    print("=" * 80)
    print("DEMO 1: SECURE API KEY MANAGEMENT")
    print("=" * 80)
    print()

    config = SecureConfig()

    print("🔒 Security Features:")
    print("  ✓ API keys stored in environment variables")
    print("  ✓ .env file with restricted permissions (chmod 600)")
    print("  ✓ Keys never committed to git")
    print("  ✓ Interactive setup wizard")
    print("  ✓ Automatic .gitignore updates")
    print()

    print("Usage:")
    print("  # Setup API key securely")
    print("  python -m nba_fanduel_sim.config.secure_config setup")
    print()
    print("  # In your code")
    print("  config = SecureConfig()")
    print("  api_key = config.get_api_key('the_odds_api')")
    print()

    # Check if key is configured
    has_key = config.get_api_key('the_odds_api') is not None
    if has_key:
        print("✅ API key is currently configured")
    else:
        print("⚠️  No API key found - run setup wizard:")
        print("   python nba_fanduel_sim/config/secure_config.py")

    print()
    print()


def demo_2_enhanced_elo_model():
    """Demo 2: Enhanced Elo Model with Injuries & Form"""
    print("=" * 80)
    print("DEMO 2: ENHANCED ELO MODEL")
    print("=" * 80)
    print()

    model = EnhancedEloModel()

    # Set team ratings
    model.set_rating("Cleveland Cavaliers", 1650)
    model.set_rating("Philadelphia 76ers", 1470)

    print("Game: Cleveland Cavaliers @ Philadelphia 76ers")
    print()

    # Scenario 1: No injuries, normal conditions
    print("SCENARIO 1: Normal Conditions")
    print("-" * 80)

    prob_normal = model.predict_win_probability(
        home_team="Philadelphia 76ers",
        away_team="Cleveland Cavaliers",
        home_rest_days=2,
        away_rest_days=2
    )

    breakdown = model.get_adjustment_breakdown(
        "Philadelphia 76ers",
        "Cleveland Cavaliers",
        home_rest_days=2,
        away_rest_days=2
    )

    print(f"Home Elo: {breakdown['home_base_elo']:.0f}")
    print(f"Away Elo: {breakdown['away_base_elo']:.0f}")
    print(f"Home Court Advantage: +{breakdown['home_court_adv']:.0f}")
    print(f"Philadelphia Win Probability: {prob_normal*100:.1f}%")
    print(f"Cleveland Win Probability: {(1-prob_normal)*100:.1f}%")
    print()

    # Scenario 2: 76ers missing Joel Embiid (star) and Tyrese Maxey (starter)
    print("SCENARIO 2: 76ers Missing Embiid (Star) & Maxey (Starter)")
    print("-" * 80)

    sixers_injuries = [
        STAR_PLAYER_INJURY("Joel Embiid", "C"),
        STARTER_INJURY("Tyrese Maxey", "PG")
    ]

    prob_injured = model.predict_win_probability(
        home_team="Philadelphia 76ers",
        away_team="Cleveland Cavaliers",
        home_injuries=sixers_injuries,
        home_rest_days=2,
        away_rest_days=2
    )

    breakdown_injured = model.get_adjustment_breakdown(
        "Philadelphia 76ers",
        "Cleveland Cavaliers",
        home_rest_days=2,
        away_rest_days=2
    )

    print(f"Home Elo: {breakdown_injured['home_base_elo']:.0f}")
    print(f"Injury Adjustment: {breakdown_injured['home_injury_adj']:+.0f}")
    print(f"Adjusted Home Elo: {breakdown_injured['home_final_elo']:.0f}")
    print(f"Philadelphia Win Probability: {prob_injured*100:.1f}%")
    print(f"Cleveland Win Probability: {(1-prob_injured)*100:.1f}%")
    print()
    print(f"Impact of Injuries: {(prob_normal - prob_injured)*100:.1f}% swing")
    print()

    # Scenario 3: Cavaliers on hot streak
    print("SCENARIO 3: Cavaliers on 5-Game Win Streak")
    print("-" * 80)

    cavs_recent_games = [
        {'won': True, 'point_diff': 15},
        {'won': True, 'point_diff': 8},
        {'won': True, 'point_diff': 12},
        {'won': True, 'point_diff': 5},
        {'won': True, 'point_diff': 10},
    ]
    model.update_team_form("Cleveland Cavaliers", cavs_recent_games)

    prob_hot_streak = model.predict_win_probability(
        home_team="Philadelphia 76ers",
        away_team="Cleveland Cavaliers",
        home_injuries=sixers_injuries,
        home_rest_days=2,
        away_rest_days=2
    )

    print(f"Cleveland with hot streak: {(1-prob_hot_streak)*100:.1f}% win probability")
    print(f"Philadelphia: {prob_hot_streak*100:.1f}% win probability")
    print()
    print(f"Impact of Form: {(prob_hot_streak - prob_injured)*100:.1f}% swing")
    print()

    # Scenario 4: 76ers on back-to-back
    print("SCENARIO 4: 76ers on Back-to-Back Game")
    print("-" * 80)

    prob_b2b = model.predict_win_probability(
        home_team="Philadelphia 76ers",
        away_team="Cleveland Cavaliers",
        home_injuries=sixers_injuries,
        home_rest_days=0,
        away_rest_days=2,
        home_back_to_back=True,
        away_back_to_back=False
    )

    print(f"76ers on back-to-back with injuries: {prob_b2b*100:.1f}%")
    print(f"Cavaliers rested: {(1-prob_b2b)*100:.1f}%")
    print()

    print("📊 Summary of Adjustments:")
    print(f"  Normal conditions:        76ers {prob_normal*100:.1f}%")
    print(f"  + Injuries (Embiid/Maxey): 76ers {prob_injured*100:.1f}%")
    print(f"  + Cavs hot streak:        76ers {prob_hot_streak*100:.1f}%")
    print(f"  + Back-to-back:           76ers {prob_b2b*100:.1f}%")
    print()
    print(f"Total Swing: {(prob_normal - prob_b2b)*100:.1f}%")
    print()
    print()


def demo_3_market_efficiency():
    """Demo 3: Market Efficiency Reality Checks"""
    print("=" * 80)
    print("DEMO 3: MARKET EFFICIENCY & REALITY CHECKS")
    print("=" * 80)
    print()

    analyzer = MarketEfficiencyAnalyzer()

    # Example: Claimed +86% EV bet from earlier analysis
    print("Testing: Memphis Grizzlies ML (+172)")
    print("Model Probability: 68.5% | Market Probability: 35.4%")
    print("Claimed EV: +86.3%")
    print()

    reality_check = analyzer.reality_check_ev_opportunity(
        model_prob=0.685,
        market_prob=0.354,
        odds=+172,
        ev_percentage=0.8634
    )

    print(f"🔍 Reality Check Result: {reality_check['recommendation']}")
    print(f"   Confidence Multiplier: {reality_check['confidence_multiplier']:.2f}x")
    print(f"   Adjusted EV: {reality_check['adjusted_ev']*100:+.1f}%")
    print(f"   Original EV: {reality_check['original_ev']*100:+.1f}%")
    print()

    if reality_check['warnings']:
        print("⚠️  WARNINGS:")
        for warning in reality_check['warnings']:
            print(f"\n  [{warning['level']}] {warning['message']}")
            print(f"    → {warning['explanation']}")
            print(f"    → ACTION: {warning['action']}")
    else:
        print("✅ No major warnings - bet appears reasonable")

    print()
    print()

    # Example: More reasonable edge
    print("Testing: Indiana Pacers -3.5 (-114)")
    print("Model Probability: 76% | Market Probability: 50.9%")
    print("Claimed EV: +42.7%")
    print()

    reality_check2 = analyzer.reality_check_ev_opportunity(
        model_prob=0.760,
        market_prob=0.509,
        odds=-114,
        ev_percentage=0.427
    )

    print(f"🔍 Reality Check Result: {reality_check2['recommendation']}")
    print(f"   Confidence Multiplier: {reality_check2['confidence_multiplier']:.2f}x")
    print(f"   Adjusted EV: {reality_check2['adjusted_ev']*100:+.1f}%")
    print()

    if reality_check2['warnings']:
        print("⚠️  WARNINGS:")
        for warning in reality_check2['warnings']:
            print(f"  [{warning['level']}] {warning['message']}")
    else:
        print("✅ No major warnings")

    print()
    print()


def demo_4_variance_analysis():
    """Demo 4: Comprehensive Variance Analysis"""
    print("=" * 80)
    print("DEMO 4: COMPREHENSIVE VARIANCE ANALYSIS")
    print("=" * 80)
    print()

    analyzer = VarianceAnalyzer()

    # Portfolio of 5 bets (from earlier analysis)
    portfolio = [
        {'model_prob': 0.613, 'odds': +116, 'stake': 500, 'bet': 'Cavs ML'},
        {'model_prob': 0.760, 'odds': -114, 'stake': 500, 'bet': 'Pacers -3.5'},
        {'model_prob': 0.785, 'odds': -110, 'stake': 500, 'bet': 'Rockets -4.5'},
        {'model_prob': 0.851, 'odds': -110, 'stake': 500, 'bet': 'Kings -7.0'},
        {'model_prob': 0.685, 'odds': +172, 'stake': 500, 'bet': 'Grizzlies ML'},
    ]

    print("Portfolio: 5 bets, $2,500 total risk")
    for i, bet in enumerate(portfolio, 1):
        print(f"  {i}. {bet['bet']:20s} {bet['model_prob']*100:.0f}% @ {bet['odds']:+4.0f}")
    print()

    # Run simulation
    print("Running Monte Carlo simulation (10,000 trials)...")
    sim = analyzer.simulate_betting_outcomes(portfolio, 10000)
    print()

    print("📊 SIMULATION RESULTS:")
    print("-" * 80)
    print(f"  Expected Profit:       ${sim['mean_profit']:,.0f}")
    print(f"  Standard Deviation:    ${sim['std_dev']:,.0f}")
    print(f"  Median Profit:         ${sim['median_profit']:,.0f}")
    print()
    print("  Outcome Distribution:")
    print(f"    Best 5%:             ${sim['percentile_95']:,.0f}+")
    print(f"    Upper Quartile:      ${sim['percentile_75']:,.0f}")
    print(f"    Median:              ${sim['median_profit']:,.0f}")
    print(f"    Lower Quartile:      ${sim['percentile_25']:,.0f}")
    print(f"    Worst 5%:            ${sim['percentile_5']:,.0f} or worse")
    print()
    print(f"  Probability of Profit: {sim['prob_profit']*100:.1f}%")
    print(f"  Probability of Loss:   {sim['prob_loss']*100:.1f}%")
    print()

    print("⚠️  VARIANCE REALITY:")
    print(f"  • Despite +EV, you'll LOSE {sim['prob_loss']*100:.0f}% of the time")
    print(f"  • 1 in 4 times, you'll lose ${abs(sim['percentile_25']):,.0f}+")
    print(f"  • 1 in 20 times, you'll lose ${abs(sim['percentile_5']):,.0f}+")
    print()

    # Losing streak analysis
    print("-" * 80)
    avg_prob = np.mean([b['model_prob'] for b in portfolio])
    streaks = analyzer.analyze_losing_streaks(avg_prob, 100)

    print(f"LOSING STREAK ANALYSIS (with {avg_prob*100:.0f}% avg win rate):")
    print()
    print("  Expected losing streaks in 100 bets:")
    for length, data in streaks['streak_probabilities'].items():
        if length <= 10:
            print(f"    {length}-bet streak: {data['prob_occurs_in_sample']*100:.0f}% chance")
    print()
    print(f"  Expected max losing streak: {streaks['expected_max_streak']:.0f} bets")
    print()

    print("🚨 CRITICAL TAKEAWAYS:")
    print("  1. Even with 72% win rate, expect 5+ bet losing streaks")
    print("  2. Short-term results are mostly variance, not skill")
    print("  3. Need 1000+ bets to validate a strategy")
    print("  4. Bankroll management prevents ruin during cold streaks")
    print()
    print()


def main():
    """Run all demos."""
    print("\n\n")
    print("#" * 80)
    print("NBA BETTING SIMULATOR - 4 KEY IMPROVEMENTS DEMONSTRATION")
    print("#" * 80)
    print()
    print("This demo showcases enhancements to address:")
    print("  1. API Security")
    print("  2. Model Limitations")
    print("  3. Market Efficiency")
    print("  4. Variance Understanding")
    print()
    input("Press Enter to continue...")
    print("\n\n")

    demo_1_secure_api_keys()
    input("Press Enter for next demo...")
    print("\n\n")

    demo_2_enhanced_elo_model()
    input("Press Enter for next demo...")
    print("\n\n")

    demo_3_market_efficiency()
    input("Press Enter for next demo...")
    print("\n\n")

    demo_4_variance_analysis()

    print()
    print("=" * 80)
    print("DEMOS COMPLETE")
    print("=" * 80)
    print()
    print("All improvements are now integrated into the simulator.")
    print()
    print("Next steps:")
    print("  1. Run secure setup: python nba_fanduel_sim/config/secure_config.py")
    print("  2. Fetch live odds with enhanced analysis")
    print("  3. Review market efficiency and variance reports before betting")
    print()


if __name__ == "__main__":
    main()
