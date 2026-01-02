"""
Configuration management utilities.
"""

import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager for loading YAML config files."""

    def __init__(self, config_path: str | Path):
        """
        Initialize configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config if config else {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation).

        Args:
            key: Configuration key (e.g., "training.epochs")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value by key (supports nested keys with dot notation).

        Args:
            key: Configuration key (e.g., "training.epochs")
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: str | Path = None):
        """
        Save configuration to YAML file.

        Args:
            path: Path to save to (defaults to original path)
        """
        save_path = Path(path) if path else self.config_path

        with open(save_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-style assignment."""
        self.set(key, value)

    def __repr__(self) -> str:
        return f"Config({self.config_path})"


def load_config(config_path: str | Path) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Config object
    """
    return Config(config_path)
