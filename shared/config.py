"""
Configuration management module.

This module provides a centralized configuration system that loads settings from:
1. Default values
2. JSON configuration files
3. Environment variables (for key operational parameters)

Configuration files are stored in the 'config' directory and organized by category.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

class Config:
    """Application configuration management."""
    
    # Default configuration paths
    CONFIG_DIR = Path("config")
    CONFIG_FILES = {
        "hardware": "hardware.json",
        "irrigation": "irrigation.json",
        "database": "database.json",
        "server": "server.json",
        "logging": "logging.json"  # Added logging configuration
    }
    
    # Default hardware configuration
    DEFAULT_HARDWARE_CONFIG = {
        "sensors": {
            "ui_update_interval": 1,
            "db_update_interval": 60,
            "pins": {
                "dht22": 26,
                "soil_moisture": {
                    "channel": 0,
                    "dry_value": 1023,
                    "wet_value": 300
                },
                "water_level": 17,
                "relay": 21,
                "bmp180": {
                    "i2c_address": "0x77",
                    "i2c_bus": 1
                },
                "lcd": {
                    "cols": 16,
                    "rows": 2,
                    "pin_rs": 25,
                    "pin_e": 24,
                    "pins_data": [23, 17, 18, 22]
                },
                "ldr": {
                    "channel": 1,
                    "min_value": 0,
                    "max_value": 1023
                },
                "rain": {
                    "channel": 2,
                    "dry_value": 1023,
                    "wet_value": 300
                }
            }
        }
    }
    
    # Environment variable mappings to configuration keys
    ENV_MAPPINGS = {
        "UI_UPDATE_INTERVAL": "hardware.sensors.ui_update_interval",
        "DB_UPDATE_INTERVAL": "hardware.sensors.db_update_interval",
        "PORT": "server.port",
        "DEBUG": "server.debug",
        "DATA_RETENTION_DAYS": "database.retention.max_days",
        "DATA_RETENTION_ENABLED": "database.retention.enabled"
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration from files and environment variables.
        
        Args:
            config_dir: Optional custom configuration directory path
        """
        # Set configuration directory
        if config_dir:
            self.CONFIG_DIR = Path(config_dir)
        
        # Initialize empty configuration
        self.config = {}
        
        # Load configuration from files
        self._load_config_files()
        
        # Override with environment variables
        self._load_from_env()
        
        # Set Flask-specific configuration
        self.SECRET_KEY = self.get("server.secret_key", "dev-key-change-in-production")
        self.SQLALCHEMY_DATABASE_URI = self.get("database.main.uri", "sqlite:///instance/irrigation.db")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        logger.info("Configuration loaded successfully")
    
    def _load_config_files(self) -> None:
        """Load configuration from JSON files."""
        for section, filename in self.CONFIG_FILES.items():
            file_path = self.CONFIG_DIR / filename
            try:
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        self.config[section] = json.load(f)
                    logger.debug(f"Loaded configuration from {file_path}")
                else:
                    logger.warning(f"Configuration file {file_path} not found")
                    # Use default configuration for hardware if file not found
                    if section == "hardware":
                        self.config[section] = self.DEFAULT_HARDWARE_CONFIG
                        logger.info("Using default hardware configuration")
                    else:
                        self.config[section] = {}
            except Exception as e:
                logger.error(f"Error loading configuration file {file_path}: {e}")
                # Use default configuration for hardware if error loading file
                if section == "hardware":
                    self.config[section] = self.DEFAULT_HARDWARE_CONFIG
                    logger.info("Using default hardware configuration due to error")
                else:
                    self.config[section] = {}
    
    def _load_from_env(self) -> None:
        """Override configuration with environment variables."""
        for env_var, config_path in self.ENV_MAPPINGS.items():
            if env_var in os.environ:
                # Parse the value based on type
                value = os.environ[env_var]
                
                # Convert to appropriate type
                if value.lower() in ('true', 'false'):
                    # Boolean value
                    value = value.lower() == 'true'
                elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                    # Integer value
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    # Float value
                    value = float(value)
                
                # Set the configuration value
                self.set(config_path, value)
                logger.debug(f"Set {config_path} from environment variable {env_var}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Dot-separated configuration key (e.g., 'hardware.sensors.ui_update_interval')
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        parts = key.split('.')
        value = self.config
        
        # Navigate through the nested dictionaries
        for part in parts:
            if part not in value:
                return default
            value = value[part]
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Dot-separated configuration key (e.g., 'hardware.sensors.ui_update_interval')
            value: Value to set
        """
        parts = key.split('.')
        
        # Navigate to the parent dictionary
        parent = self.config
        for part in parts[:-1]:
            if part not in parent:
                parent[part] = {}
            parent = parent[part]
        
        # Set the value
        parent[parts[-1]] = value
    
    def save(self) -> None:
        """Save the current configuration to files."""
        for section, filename in self.CONFIG_FILES.items():
            if section in self.config:
                file_path = self.CONFIG_DIR / filename
                try:
                    # Ensure directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write configuration to file
                    with open(file_path, 'w') as f:
                        json.dump(self.config[section], f, indent=2)
                    
                    logger.debug(f"Saved configuration to {file_path}")
                except Exception as e:
                    logger.error(f"Error saving configuration to {file_path}: {e}")