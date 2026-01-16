"""
Configuration Module

Handles secure configuration management for API keys and settings.
"""

from .secure_config import SecureConfig, setup_gitignore

__all__ = ['SecureConfig', 'setup_gitignore']
