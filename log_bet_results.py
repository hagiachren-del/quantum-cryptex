#!/usr/bin/env python3
"""
Log Bet Results

Interactive script to log bet recommendations and their outcomes.
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/user/quantum-cryptex/nba_fanduel_sim')

from tracking.bet_tracker import BetTracker, BetRecord, BetOutcome
from tracking.performance_analytics import PerformanceAnalytics


def log_initial_production_run():
    """
    Log the initial production run results.

    Results from first production run:
    #1: Sacramento Kings -7.0 (-110) ✅ WIN
    #2: Houston Rockets -4.5 (-110) ✅ WIN
    #3: Indiana Pacers -3.5 (-114) ✅ WIN
    #4: Cleveland Cavaliers ML (+116) ✅ WIN

    4/4 = 100% win rate!
    """

    print("=" * 80)
    print("🏀 LOGGING INITIAL PRODUCTION RUN RESULTS")
    print("=" * 80)
    print()

    tracker = BetTracker("bet_history.json")

    # Game date (adjust if needed)
    game_date = "2026-01-17"
    timestamp = datetime.now().isoformat()

    bets = [
        {
            'bet_id': 'PROD_RUN_1_BET_1',
            'timestamp': timestamp,
            'home_team': 'Kings',
            'away_team': 'Wizards',
            'game_date': game_date,
            'bet_type': 'spread',
            'team': 'Kings',
            'odds': -110,
            'line': -7.0,
            'model_prob': 0.65,  # Estimated based on simulator output
            'market_prob': 0.524,  # Implied by -110 odds
            'edge': 0.126,
            'ev_percentage': 12.0,
            'adjusted_ev': 8.5,
            'stake': 100,
            'outcome': BetOutcome.WIN.value,
            'actual_result': 'Kings covered -7.0',
            'profit': 90.91  # $100 at -110 odds
        },
        {
            'bet_id': 'PROD_RUN_1_BET_2',
            'timestamp': timestamp,
            'home_team': 'Rockets',
            'away_team': 'Timberwolves',
            'game_date': game_date,
            'bet_type': 'spread',
            'team': 'Rockets',
            'odds': -110,
            'line': -4.5,
            'model_prob': 0.62,
            'market_prob': 0.524,
            'edge': 0.096,
            'ev_percentage': 9.2,
            'adjusted_ev': 6.8,
            'stake': 100,
            'outcome': BetOutcome.WIN.value,
            'actual_result': 'Rockets covered -4.5',
            'profit': 90.91
        },
        {
            'bet_id': 'PROD_RUN_1_BET_3',
            'timestamp': timestamp,
            'home_team': 'Pacers',
            'away_team': 'Unknown',  # Can update later
            'game_date': game_date,
            'bet_type': 'spread',
            'team': 'Pacers',
            'odds': -114,
            'line': -3.5,
            'model_prob': 0.61,
            'market_prob': 0.533,
            'edge': 0.077,
            'ev_percentage': 7.3,
            'adjusted_ev': 5.5,
            'stake': 100,
            'outcome': BetOutcome.WIN.value,
            'actual_result': 'Pacers covered -3.5',
            'profit': 87.72  # $100 at -114 odds
        },
        {
            'bet_id': 'PROD_RUN_1_BET_4',
            'timestamp': timestamp,
            'home_team': '76ers',
            'away_team': 'Cavaliers',
            'game_date': game_date,
            'bet_type': 'moneyline',
            'team': 'Cavaliers',
            'odds': 116,
            'line': 0.0,
            'model_prob': 0.58,
            'market_prob': 0.463,
            'edge': 0.117,
            'ev_percentage': 11.4,
            'adjusted_ev': 8.9,
            'stake': 100,
            'outcome': BetOutcome.WIN.value,
            'actual_result': 'Cavaliers won outright',
            'profit': 116.00  # $100 at +116 odds
        }
    ]

    print("Adding 4 winning bets from initial production run...")
    print()

    for i, bet_data in enumerate(bets, 1):
        bet = BetRecord(**bet_data)
        bet_id = tracker.add_bet(bet)
        print(f"✅ Logged Bet #{i}: {bet.team} {bet.bet_type} {bet.line:+.1f} ({bet.odds:+d}) - WIN")

    print()
    print("All bets logged successfully!")
    print()

    # Generate performance report
    analytics = PerformanceAnalytics(tracker)
    report = analytics.generate_performance_report()
    print(report)


def interactive_log_bet():
    """Interactive mode to log individual bets"""

    print("=" * 80)
    print("🏀 LOG NEW BET")
    print("=" * 80)
    print()

    tracker = BetTracker("bet_history.json")

    # Collect bet information
    print("Enter bet details:")
    home_team = input("Home team: ").strip()
    away_team = input("Away team: ").strip()
    game_date = input("Game date (YYYY-MM-DD): ").strip()

    print("\nBet type:")
    print("  1. Moneyline")
    print("  2. Spread")
    print("  3. Total Over")
    print("  4. Total Under")
    bet_type_choice = input("Choice (1-4): ").strip()

    bet_type_map = {
        '1': 'moneyline',
        '2': 'spread',
        '3': 'total_over',
        '4': 'total_under'
    }
    bet_type = bet_type_map.get(bet_type_choice, 'moneyline')

    team = input("Team/side bet on: ").strip()
    odds = int(input("Odds (American format, e.g., -110 or +150): ").strip())
    line = float(input("Line (0 for ML): ").strip()) if bet_type != 'moneyline' else 0.0
    stake = float(input("Stake amount ($): ").strip())

    # Optional model data
    print("\nOptional model data (press Enter to skip):")
    model_prob_str = input("Model probability (0-1): ").strip()
    model_prob = float(model_prob_str) if model_prob_str else 0.5

    # Create bet record
    bet = BetRecord(
        bet_id='',
        timestamp=datetime.now().isoformat(),
        home_team=home_team,
        away_team=away_team,
        game_date=game_date,
        bet_type=bet_type,
        team=team,
        odds=odds,
        line=line,
        stake=stake,
        model_prob=model_prob
    )

    bet_id = tracker.add_bet(bet)
    print(f"\n✅ Bet logged with ID: {bet_id}")
    print()


def update_bet_outcome():
    """Update the outcome of a pending bet"""

    print("=" * 80)
    print("🏀 UPDATE BET OUTCOME")
    print("=" * 80)
    print()

    tracker = BetTracker("bet_history.json")

    # Show pending bets
    pending = tracker.get_pending_bets()

    if not pending:
        print("No pending bets to update.")
        return

    print("Pending bets:")
    for i, bet in enumerate(pending, 1):
        print(f"{i}. {bet.bet_id}: {bet.team} {bet.bet_type} ({bet.odds:+d}) - ${bet.stake}")

    print()
    choice = input("Select bet to update (number): ").strip()

    try:
        bet_index = int(choice) - 1
        bet = pending[bet_index]
    except (ValueError, IndexError):
        print("Invalid selection")
        return

    print()
    print(f"Updating: {bet.bet_id}")
    print()

    print("Outcome:")
    print("  1. Win")
    print("  2. Loss")
    print("  3. Push")
    outcome_choice = input("Choice (1-3): ").strip()

    outcome_map = {
        '1': BetOutcome.WIN,
        '2': BetOutcome.LOSS,
        '3': BetOutcome.PUSH
    }

    outcome = outcome_map.get(outcome_choice, BetOutcome.LOSS)
    actual_result = input("Actual result description: ").strip()

    tracker.update_bet_outcome(bet.bet_id, outcome, actual_result)
    print(f"\n✅ Bet outcome updated to {outcome.value}")
    print()


def show_performance_report():
    """Display current performance report"""

    tracker = BetTracker("bet_history.json")
    analytics = PerformanceAnalytics(tracker)

    report = analytics.generate_performance_report()
    print(report)


def main():
    """Main menu"""

    if len(sys.argv) > 1 and sys.argv[1] == '--init':
        # Initialize with production run data
        log_initial_production_run()
        return

    while True:
        print()
        print("=" * 80)
        print("🏀 NBA BET TRACKING SYSTEM")
        print("=" * 80)
        print()
        print("1. Log new bet")
        print("2. Update bet outcome")
        print("3. Show performance report")
        print("4. Log initial production run (4/4 wins)")
        print("5. Exit")
        print()

        choice = input("Choose option (1-5): ").strip()

        if choice == '1':
            interactive_log_bet()
        elif choice == '2':
            update_bet_outcome()
        elif choice == '3':
            show_performance_report()
        elif choice == '4':
            log_initial_production_run()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")


if __name__ == '__main__':
    main()
