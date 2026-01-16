#!/usr/bin/env python3
"""
One-Command NBA Analysis
Just run: python3 run_analysis.py
"""

import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / 'nba_fanduel_sim'))

def main():
    print("=" * 80)
    print("NBA BETTING SIMULATOR - TODAY'S GAMES ANALYSIS")
    print("=" * 80)
    print()

    # Check if API key is set up
    from config.secure_config import SecureConfig

    config = SecureConfig()
    api_key = config.get_api_key('the_odds_api')

    if not api_key:
        print("⚠️  API KEY NOT FOUND")
        print()
        print("You need to set up your API key first (one-time setup):")
        print()
        print("  python3 nba_fanduel_sim/config/secure_config.py setup")
        print()
        print("Or set it directly:")
        print("  export THE_ODDS_API_KEY='your_key_here'")
        print()

        # Offer to set it now
        try:
            print("Would you like to set it up now?")
            key = input("Paste your API key (or press Enter to skip): ").strip()

            if key:
                config.set_api_key(key, 'the_odds_api')
                print()
                print("✅ API key saved!")
                print()
            else:
                print("Setup skipped. Run setup later to use the simulator.")
                return
        except EOFError:
            print("Setup skipped (non-interactive mode).")
            return

    # Run the analysis
    print("Running live odds analysis...")
    print()

    from quick_analyze import main as analyze_main
    analyze_main()

if __name__ == "__main__":
    main()
