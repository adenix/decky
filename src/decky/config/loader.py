"""
Configuration loader for Decky
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates YAML configuration files"""

    def load(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = os.path.expanduser(config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Validate basic structure
            self._validate(config)

            # Apply defaults
            config = self._apply_defaults(config)

            logger.info(f"Loaded configuration from {config_path}")
            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

    def _validate(self, config: Dict[str, Any]):
        """Validate configuration structure"""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Pages are required
        if "pages" not in config:
            raise ValueError("Configuration must have 'pages' section")

        pages = config["pages"]
        if not isinstance(pages, dict) or not pages:
            raise ValueError("'pages' must be a non-empty dictionary")

        # Validate each page
        for page_name, page_config in pages.items():
            if not isinstance(page_config, dict):
                raise ValueError(f"Page '{page_name}' must be a dictionary")

            # Each page should have buttons
            if "buttons" in page_config:
                if not isinstance(page_config["buttons"], dict):
                    raise ValueError(f"Buttons in page '{page_name}' must be a dictionary")

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to configuration"""
        # Device defaults
        if "device" not in config:
            config["device"] = {}
        if "brightness" not in config["device"]:
            config["device"]["brightness"] = 100

        # Style defaults
        if "styles" not in config:
            config["styles"] = {}
        if "default" not in config["styles"]:
            config["styles"]["default"] = {
                "font": "DejaVu Sans",
                "font_size": 14,
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "text_align": "bottom",
                "text_offset": 0,
            }

        # Feedback defaults
        if "feedback" not in config:
            config["feedback"] = {"visual": True}

        return config
