#!/usr/bin/env python3
"""
Decky - Main entry point using modular architecture
"""

import argparse
import logging
import os
import signal
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decky.controller import DeckyController


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Decky - Stream Deck controller for Linux")
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    # Check config file exists
    config_path = os.path.expanduser(args.config)
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    # Create controller instance
    controller = DeckyController(config_path)

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        controller.running = False
        controller.shutting_down = True  # Prevent reconnection attempts
        # Raise KeyboardInterrupt to trigger the normal shutdown flow
        raise KeyboardInterrupt()

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)  # systemd stop
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C

    # Run controller
    try:
        controller.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
