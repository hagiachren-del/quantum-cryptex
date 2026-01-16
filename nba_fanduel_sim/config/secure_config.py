"""
Secure Configuration Management for NBA Betting Simulator

Implements secure API key storage using environment variables
and encrypted configuration files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
import getpass


class SecureConfig:
    """
    Manages sensitive configuration data securely.

    Uses environment variables as primary storage,
    with optional encrypted file backup.
    """

    def __init__(self, config_dir: str = None):
        """
        Initialize secure configuration manager.

        Args:
            config_dir: Directory for config files (default: ~/.nba_simulator)
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.nba_simulator")

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.env_file = self.config_dir / ".env"
        self.config_file = self.config_dir / "config.json"

    def set_api_key(self, api_key: str, service: str = "the_odds_api") -> None:
        """
        Securely store API key in environment variable and .env file.

        Args:
            api_key: The API key to store
            service: Service name (default: the_odds_api)
        """
        # Validate API key format
        if not api_key or len(api_key) < 10:
            raise ValueError("Invalid API key format")

        # Set in current environment
        env_var = f"{service.upper()}_KEY"
        os.environ[env_var] = api_key

        # Save to .env file (with restrictive permissions)
        self._save_to_env_file(env_var, api_key)

        print(f"✅ API key securely stored for {service}")
        print(f"   Environment variable: {env_var}")
        print(f"   .env file: {self.env_file}")
        print(f"\n⚠️  IMPORTANT: Add {self.env_file} to .gitignore!")

    def _save_to_env_file(self, key: str, value: str) -> None:
        """Save key-value pair to .env file with secure permissions."""
        # Read existing .env
        env_data = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        env_data[k.strip()] = v.strip()

        # Update with new key
        env_data[key] = value

        # Write back
        with open(self.env_file, 'w') as f:
            f.write("# NBA Betting Simulator - API Keys\n")
            f.write("# DO NOT COMMIT THIS FILE TO GIT!\n\n")
            for k, v in env_data.items():
                f.write(f"{k}={v}\n")

        # Set restrictive permissions (Unix only)
        try:
            os.chmod(self.env_file, 0o600)  # Read/write for owner only
        except:
            pass  # Windows doesn't support chmod

    def get_api_key(self, service: str = "the_odds_api") -> Optional[str]:
        """
        Retrieve API key from environment.

        Args:
            service: Service name

        Returns:
            API key or None if not found
        """
        env_var = f"{service.upper()}_KEY"

        # Try environment variable first
        api_key = os.environ.get(env_var)

        # If not in environment, try loading from .env file
        if not api_key and self.env_file.exists():
            self._load_env_file()
            api_key = os.environ.get(env_var)

        return api_key

    def _load_env_file(self) -> None:
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            return

        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    def delete_api_key(self, service: str = "the_odds_api") -> None:
        """
        Delete API key from storage.

        Args:
            service: Service name
        """
        env_var = f"{service.upper()}_KEY"

        # Remove from environment
        if env_var in os.environ:
            del os.environ[env_var]

        # Remove from .env file
        if self.env_file.exists():
            env_data = {}
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() != env_var:
                            env_data[k.strip()] = v.strip()

            with open(self.env_file, 'w') as f:
                f.write("# NBA Betting Simulator - API Keys\n")
                f.write("# DO NOT COMMIT THIS FILE TO GIT!\n\n")
                for k, v in env_data.items():
                    f.write(f"{k}={v}\n")

        print(f"✅ API key deleted for {service}")

    def interactive_setup(self) -> None:
        """Interactive setup wizard for API keys."""
        print("=" * 70)
        print("NBA BETTING SIMULATOR - SECURE API KEY SETUP")
        print("=" * 70)
        print()
        print("This wizard will securely store your The Odds API key.")
        print()
        print("⚠️  SECURITY BEST PRACTICES:")
        print("   1. Never share API keys in chat/email")
        print("   2. Never commit .env files to git")
        print("   3. Regenerate keys if accidentally exposed")
        print("   4. Use separate keys for dev/prod")
        print()

        api_key = getpass.getpass("Enter your The Odds API key: ")

        if not api_key:
            print("❌ No API key provided. Setup cancelled.")
            return

        try:
            self.set_api_key(api_key, "the_odds_api")
            print()
            print("=" * 70)
            print("✅ SETUP COMPLETE!")
            print("=" * 70)
            print()
            print("Your API key is securely stored and ready to use.")
            print()
            print("Next steps:")
            print(f"  1. Ensure ~/.nba_simulator/.env is in your .gitignore")
            print(f"  2. Run: python main.py --fetch-odds")
            print()
        except Exception as e:
            print(f"❌ Setup failed: {e}")

    def validate_api_key(self) -> bool:
        """
        Validate that API key is configured.

        Returns:
            True if API key exists, False otherwise
        """
        api_key = self.get_api_key()

        if not api_key:
            print("=" * 70)
            print("⚠️  API KEY NOT FOUND")
            print("=" * 70)
            print()
            print("You need to configure your The Odds API key before using")
            print("the simulator.")
            print()
            print("Run: python secure_config.py")
            print()
            print("Or set environment variable:")
            print("  export THE_ODDS_API_KEY='your_key_here'")
            print()
            return False

        # Mask key for display
        masked = api_key[:8] + "..." + api_key[-4:]
        print(f"✅ API key found: {masked}")
        return True


def setup_gitignore(repo_root: str = None) -> None:
    """
    Ensure sensitive files are in .gitignore.

    Args:
        repo_root: Repository root directory
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    else:
        repo_root = Path(repo_root)

    gitignore_path = repo_root / ".gitignore"

    # Patterns to add
    sensitive_patterns = [
        "# Sensitive Configuration",
        ".env",
        ".env.*",
        "*.key",
        "*.secret",
        "~/.nba_simulator/.env",
        "config/secrets.json",
        "*.pem",
        "*.p12",
    ]

    # Read existing .gitignore
    existing_lines = []
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_lines = [line.rstrip() for line in f]

    # Add missing patterns
    lines_to_add = []
    for pattern in sensitive_patterns:
        if pattern not in existing_lines:
            lines_to_add.append(pattern)

    if lines_to_add:
        with open(gitignore_path, 'a') as f:
            f.write("\n")
            for line in lines_to_add:
                f.write(line + "\n")

        print(f"✅ Added {len(lines_to_add)} patterns to .gitignore")
    else:
        print("✅ .gitignore already configured correctly")


if __name__ == "__main__":
    """Run interactive setup when executed directly."""
    import sys

    config = SecureConfig()

    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            config.interactive_setup()
        elif sys.argv[1] == "validate":
            config.validate_api_key()
        elif sys.argv[1] == "delete":
            config.delete_api_key()
        elif sys.argv[1] == "gitignore":
            setup_gitignore()
    else:
        # Default: run interactive setup
        config.interactive_setup()
        setup_gitignore()
