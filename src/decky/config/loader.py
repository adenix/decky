"""
Configuration loader for Decky
"""

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

# Maximum config file size (1MB should be plenty for YAML configs)
MAX_CONFIG_SIZE = 1024 * 1024


class ConfigLoader:
    """Loads and validates YAML configuration files"""

    def load(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Validated configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid or too large
            PermissionError: If config file is not readable
        """
        # Expand user path and resolve to absolute path
        resolved_path = Path(config_path).expanduser().resolve()

        # Security: Validate the path is safe
        self._validate_config_path(resolved_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

        # Check file size to prevent DoS attacks
        file_size = resolved_path.stat().st_size
        if file_size > MAX_CONFIG_SIZE:
            raise ValueError(
                f"Configuration file too large: {file_size} bytes "
                f"(maximum {MAX_CONFIG_SIZE} bytes)"
            )

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Validate basic structure
            self._validate(config)

            # Apply defaults
            config = self._apply_defaults(config)

            logger.info(f"Loaded configuration from {resolved_path}")
            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except PermissionError as e:
            raise PermissionError(f"Cannot read configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

    def _validate_config_path(self, config_path: Path) -> None:
        """
        Validate that the configuration file path is safe to load.

        This prevents path traversal attacks and ensures configs are only
        loaded from expected locations.

        Args:
            config_path: Resolved absolute path to config file

        Raises:
            ValueError: If path is not safe to load
        """
        # Ensure it's a file, not a directory or special file
        if config_path.is_dir():
            raise ValueError(f"Path is a directory, not a file: {config_path}")

        # Check file extension
        if config_path.suffix.lower() not in [".yaml", ".yml"]:
            logger.warning(
                f"Configuration file has unexpected extension: {config_path.suffix}. "
                f"Expected .yaml or .yml"
            )

        # Optional: Restrict to specific directories (commented out by default)
        # This can be enabled if you want to enforce configs only from specific locations
        # allowed_dirs = [
        #     Path.home() / ".decky" / "configs",
        #     Path.cwd() / "configs",
        # ]
        # if not any(config_path.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs):
        #     raise ValueError(
        #         f"Configuration file must be in an allowed directory. "
        #         f"Got: {config_path}"
        #     )

        logger.debug(f"Configuration path validated: {config_path}")

    def _validate(self, config: Dict[str, Any]) -> None:
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
