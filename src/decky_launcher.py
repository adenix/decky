#!/usr/bin/env python3
"""
Decky Launcher - Validates config before starting Decky
This wrapper ensures the config is valid before starting the main application
"""

import sys
import os
import yaml
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_config(config_path: str) -> bool:
    """Validate YAML configuration file"""
    try:
        with open(config_path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        logger.error(f"Configuration file has YAML syntax error:")
        logger.error(f"  {e}")
        logger.error(f"")
        logger.error(f"Please fix the configuration file: {config_path}")
        logger.error(f"You can edit it with: deckyctl edit")
        return False
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.error(f"Create one with: cp ~/.decky/configs/minimal.yaml {config_path}")
        return False
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        logger.error("Usage: decky_launcher.py <config_file>")
        sys.exit(1)

    config_path = sys.argv[1]

    # Validate configuration
    if not validate_config(config_path):
        logger.error("Service failed to start due to configuration error")
        sys.exit(1)

    # Configuration is valid, run the main Decky application
    import decky
    sys.argv = ['decky.py', config_path] + sys.argv[2:]
    decky.main()


if __name__ == "__main__":
    main()