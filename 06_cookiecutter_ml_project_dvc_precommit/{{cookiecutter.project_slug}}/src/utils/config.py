#!/usr/bin/env python3
"""Configuration utilities for {{cookiecutter.project_name}}."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file. If not provided,
                    defaults to config/params.yaml
    
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path("config/params.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    return config


def load_env_vars(env_file: Optional[Path] = None) -> None:
    """Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file. If not provided,
                 searches for .env in current directory
    """
    if env_file is None:
        env_file = Path(".env")
    
    if env_file.exists():
        load_dotenv(env_file)


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get environment variable value.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required
    
    Returns:
        Environment variable value
    
    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable not found: {key}")
    
    return value


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries.
    
    Later configurations override earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
    
    Returns:
        Merged configuration dictionary
    """
    result = {}
    
    for config in configs:
        result = _deep_merge(result, config)
    
    return result


def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge into dict1
    
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


class Config:
    """Configuration manager class."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        load_env_vars()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Supports nested keys using dot notation (e.g., "model.type").
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()