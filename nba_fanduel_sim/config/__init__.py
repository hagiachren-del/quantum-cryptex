"""
Configuration management for NBA FanDuel Simulator.
"""

from pathlib import Path
import yaml
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file (default: config/settings.yaml)

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default config path
        config_path = Path(__file__).parent / 'settings.yaml'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def get_model_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract model configuration."""
    return config.get('model', {})


def get_strategy_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract strategy configuration."""
    return config.get('strategy', {})


def get_bankroll_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract bankroll configuration."""
    return config.get('bankroll', {})


def get_data_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data configuration."""
    return config.get('data', {})


__all__ = [
    'load_config',
    'get_model_config',
    'get_strategy_config',
    'get_bankroll_config',
    'get_data_config',
]
