#!/usr/bin/env python3
"""
NBA FanDuel Betting Simulator - Main Entry Point

Usage:
    python main.py [--config CONFIG_FILE]

Example:
    python main.py
    python main.py --config my_config.yaml
"""

import argparse
from pathlib import Path
import sys

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from data import load_games_csv, load_fanduel_odds_csv, merge_games_and_odds, generate_sample_data
from models import EloModel, LogisticModel, LogisticWithEloModel
from simulator import Backtester, BacktestConfig
from evaluation import calculate_metrics, generate_full_report, print_backtest_summary


def create_model_from_config(model_config: dict):
    """
    Create model instance from configuration.

    Args:
        model_config: Model configuration dictionary

    Returns:
        Instantiated model
    """
    model_type = model_config.get('type', 'elo')

    if model_type == 'elo':
        elo_params = model_config.get('elo', {})
        return EloModel(
            k_factor=elo_params.get('k_factor', 20.0),
            home_advantage=elo_params.get('home_advantage', 100.0),
            initial_rating=elo_params.get('initial_rating', 1500.0),
            mean_reversion=elo_params.get('mean_reversion', 0.75),
        )

    elif model_type == 'logistic':
        logistic_params = model_config.get('logistic', {})
        return LogisticModel(
            retrain_frequency=logistic_params.get('retrain_frequency', 100),
            min_training_games=logistic_params.get('min_training_games', 200),
        )

    elif model_type == 'logistic_with_elo':
        elo_params = model_config.get('elo', {})
        logistic_params = model_config.get('logistic', {})
        return LogisticWithEloModel(
            elo_k_factor=elo_params.get('k_factor', 20.0),
            elo_home_advantage=elo_params.get('home_advantage', 100.0),
            retrain_frequency=logistic_params.get('retrain_frequency', 100),
        )

    else:
        raise ValueError(f"Unknown model type: {model_type}")


def main():
    """Main entry point for the simulator."""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='NBA FanDuel Betting Simulator'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: config/settings.yaml)'
    )
    parser.add_argument(
        '--generate-sample-data',
        action='store_true',
        help='Generate sample data and exit'
    )
    args = parser.parse_args()

    # Load configuration
    print("Loading configuration...")
    config = load_config(args.config)

    # Generate sample data if requested
    if args.generate_sample_data:
        print("Generating sample data...")
        data_dir = Path('nba_fanduel_sim/data/raw')
        generate_sample_data(data_dir, n_games=500, start_date="2023-10-01")
        print("Sample data generated successfully!")
        return

    # Load data
    print("Loading data...")
    data_config = config['data']

    games_path = Path(data_config['games_file'])
    odds_path = Path(data_config['odds_file'])

    # Check if files exist, if not, generate sample data
    if not games_path.exists() or not odds_path.exists():
        print("Data files not found. Generating sample data...")
        data_dir = Path('nba_fanduel_sim/data/raw')
        generate_sample_data(data_dir, n_games=500, start_date="2023-10-01")

        # Update paths to generated files
        games_path = data_dir / 'sample_games.csv'
        odds_path = data_dir / 'sample_fanduel_odds.csv'

    games = load_games_csv(games_path)
    odds = load_fanduel_odds_csv(odds_path)

    print(f"Loaded {len(games)} games and {len(odds)} odds records")

    # Merge data
    merged_data = merge_games_and_odds(games, odds)
    print(f"Merged to {len(merged_data)} games with both data and odds")

    if not merged_data:
        print("Error: No games with both data and odds!")
        sys.exit(1)

    # Create model
    print("Creating model...")
    model = create_model_from_config(config['model'])
    print(f"Model: {model}")

    # Create backtest configuration
    print("Setting up backtest...")
    bankroll_config = config['bankroll']
    strategy_config = config['strategy']

    backtest_config = BacktestConfig(
        model=model,
        initial_bankroll=bankroll_config['initial_bankroll'],
        max_bet_percentage=bankroll_config['max_bet_percentage'],
        max_daily_bets=bankroll_config['max_daily_bets'],
        max_game_exposure=bankroll_config['max_game_exposure'],
        min_ev=strategy_config['min_ev'],
        min_edge=strategy_config['min_edge'],
        bet_sizing_method=bankroll_config['sizing_method'],
        kelly_fraction=bankroll_config['kelly_fraction'],
        flat_percentage=bankroll_config['flat_percentage'],
        min_bet_amount=bankroll_config['min_bet_amount'],
        max_bet_amount=bankroll_config.get('max_bet_amount'),
        vig_method=config['sportsbook']['vig_method'],
        start_date=data_config.get('start_date'),
        end_date=data_config.get('end_date'),
        seasons=data_config.get('seasons'),
    )

    # Run backtest
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST")
    print("=" * 70 + "\n")

    backtester = Backtester(backtest_config)
    results = backtester.run(merged_data)

    # Print summary
    print("\n")
    print_backtest_summary(results)

    # Calculate additional metrics
    print("\nCalculating detailed metrics...")
    metrics = calculate_metrics(results)

    # Generate full report
    full_report = generate_full_report(results, metrics)

    # Save results
    output_config = config['output']
    results_dir = Path(output_config['results_dir'])

    if output_config['save_bet_history'] or output_config['save_summary']:
        print(f"\nSaving results to {results_dir}/...")
        backtester.save_results(results, results_dir)

    if output_config['save_full_report']:
        report_path = results_dir / 'full_report.txt'
        with open(report_path, 'w') as f:
            f.write(full_report)
        print(f"Full report saved to {report_path}")

    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
