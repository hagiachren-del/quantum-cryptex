#!/usr/bin/env python3
"""
Quick test script for the NBA FanDuel Simulator

Tests basic functionality without running a full backtest.
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent / 'nba_fanduel_sim'))

from odds import (
    american_to_probability,
    probability_to_american,
    calculate_payout,
    remove_vig,
)

from models import EloModel
from strategy import calculate_ev, find_ev_opportunities


def test_odds_conversion():
    """Test FanDuel odds utilities."""
    print("Testing odds conversion...")

    # Test American to probability
    prob = american_to_probability(-110)
    assert abs(prob - 0.5238) < 0.001, f"Expected ~0.5238, got {prob}"

    # Test probability to American
    odds = probability_to_american(0.5238)
    assert abs(odds - (-110)) < 1, f"Expected ~-110, got {odds}"

    # Test payout calculation
    payout = calculate_payout(100, -110)
    assert abs(payout - 190.91) < 0.1, f"Expected ~190.91, got {payout}"

    print("✓ Odds conversion tests passed")


def test_vig_removal():
    """Test vig removal."""
    print("Testing vig removal...")

    # -110 on both sides
    prob_a = american_to_probability(-110)
    prob_b = american_to_probability(-110)

    fair_a, fair_b = remove_vig(prob_a, prob_b, method="proportional")

    assert abs(fair_a - 0.5) < 0.001, f"Expected 0.5, got {fair_a}"
    assert abs(fair_b - 0.5) < 0.001, f"Expected 0.5, got {fair_b}"
    assert abs(fair_a + fair_b - 1.0) < 0.001, "Probabilities should sum to 1"

    print("✓ Vig removal tests passed")


def test_elo_model():
    """Test Elo model."""
    print("Testing Elo model...")

    model = EloModel(k_factor=20, home_advantage=100)

    # Create sample games
    games = [
        {
            'game_id': '1',
            'date': '2024-01-01',
            'home_team': 'LAL',
            'away_team': 'GSW',
            'home_score': 110,
            'away_score': 105,
            'home_won': True,
            'margin': 5,
            'home_rest_days': 1,
            'away_rest_days': 2,
            'season': 2024,
        }
    ]

    # Fit model
    model.fit(games)
    assert model.is_fitted, "Model should be fitted"

    # Predict
    prob = model.predict_proba(games[0])
    assert 0 < prob < 1, f"Probability should be between 0 and 1, got {prob}"

    print(f"  LAL vs GSW win prob: {prob:.3f}")
    print("✓ Elo model tests passed")


def test_ev_calculation():
    """Test EV calculation."""
    print("Testing EV calculation...")

    # Positive EV scenario
    model_prob = 0.55  # Model thinks 55% chance
    odds = -110  # FanDuel offers -110

    ev = calculate_ev(model_prob, odds, stake=100)

    # Should be positive EV
    assert ev > 0, f"Expected positive EV, got {ev}"

    print(f"  EV for 55% prob at -110: ${ev:.2f}")
    print("✓ EV calculation tests passed")


def test_bet_opportunity_finding():
    """Test finding EV opportunities."""
    print("Testing bet opportunity detection...")

    game = {
        'game_id': '1',
        'home_team': 'LAL',
        'away_team': 'GSW',
        'moneyline_home': -110,
        'moneyline_away': -110,
        'spread': -2.5,
        'spread_odds_home': -110,
        'spread_odds_away': -110,
    }

    # Model slightly favors home team
    home_win_prob = 0.55

    opportunities = find_ev_opportunities(
        game=game,
        home_win_prob=home_win_prob,
        min_ev=0.01,  # 1% minimum EV
        min_edge=0.005,
    )

    print(f"  Found {len(opportunities)} opportunities")

    for opp in opportunities:
        print(f"    {opp.bet_type}: EV={opp.ev_percent:.2f}%, edge={opp.edge:.3f}")

    print("✓ Bet opportunity tests passed")


def main():
    """Run all tests."""
    print("=" * 70)
    print("NBA FANDUEL SIMULATOR - FUNCTIONALITY TESTS")
    print("=" * 70)
    print()

    try:
        test_odds_conversion()
        test_vig_removal()
        test_elo_model()
        test_ev_calculation()
        test_bet_opportunity_finding()

        print()
        print("=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Generate sample data: python nba_fanduel_sim/main.py --generate-sample-data")
        print("2. Run backtest: python nba_fanduel_sim/main.py")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
