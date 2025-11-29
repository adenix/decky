#!/usr/bin/env python3
"""
Decky CLI - Unified command-line interface for Decky Stream Deck controller.

This module provides both the daemon entry point and service management commands.
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeckyCLI:
    """Main CLI handler for Decky commands."""

    def __init__(self) -> None:
        self.service_name: str = "decky"
        self.config_dir: Path = Path.home() / ".decky"
        self.configs_dir: Path = self.config_dir / "configs"
        self.systemd_user_dir: Path = Path.home() / ".config" / "systemd" / "user"
        self.service_file: Path = self.systemd_user_dir / f"{self.service_name}.service"

        # Ensure directories exist
        self.configs_dir.mkdir(parents=True, exist_ok=True)

    def run_daemon(self, config_path: str, log_level: str = "INFO") -> int:
        """
        Run the Decky daemon directly.

        This is what systemd calls to start the service.
        """
        # Import here to avoid circular imports
        from .main import main as daemon_main

        # Set up arguments for the daemon
        sys.argv = ["decky", config_path, "--log-level", log_level]

        try:
            daemon_main()
            return 0
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
            return 0
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            return 1

    def start_service(self) -> int:
        """Start the Decky systemd service."""
        print("Starting Decky service...")
        result = subprocess.run(
            ["systemctl", "--user", "start", self.service_name], capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"Failed to start service: {result.stderr}")
            return 1

        # Wait a moment for service to start
        time.sleep(1)

        # Show status
        return self.show_status()

    def stop_service(self) -> int:
        """Stop the Decky systemd service."""
        print("Stopping Decky service...")
        result = subprocess.run(
            ["systemctl", "--user", "stop", self.service_name], capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"Failed to stop service: {result.stderr}")
            return 1

        print("Decky service stopped.")
        return 0

    def restart_service(self) -> int:
        """Restart the Decky systemd service."""
        print("Restarting Decky service...")
        result = subprocess.run(
            ["systemctl", "--user", "restart", self.service_name], capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"Failed to restart service: {result.stderr}")
            return 1

        # Wait a moment for service to restart
        time.sleep(1)

        # Show status
        return self.show_status()

    def show_status(self) -> int:
        """Show the status of the Decky systemd service."""
        result = subprocess.run(
            ["systemctl", "--user", "status", self.service_name, "--no-pager"], text=True
        )
        return result.returncode

    def show_logs(self, follow: bool = True, lines: int = 50) -> int:
        """
        Show logs from the Decky service.

        Args:
            follow: If True, follow log output (like tail -f)
            lines: Number of recent lines to show
        """
        cmd = ["journalctl", "--user", "-u", self.service_name]

        if follow:
            print("Showing Decky logs (Ctrl+C to exit)...")
            cmd.append("-f")
        else:
            cmd.extend(["-n", str(lines)])

        try:
            result = subprocess.run(cmd, text=True)
            return result.returncode
        except KeyboardInterrupt:
            print("\nStopped following logs.")
            return 0

    def list_configs(self) -> int:
        """List available configuration files."""
        print(f"Available configurations in {self.configs_dir}:\n")

        # Get current active config from service file if it exists
        active_config = None
        if self.service_file.exists():
            try:
                content = self.service_file.read_text()
                # Extract config name from ExecStart line
                for line in content.split("\n"):
                    if "ExecStart=" in line and ".yaml" in line:
                        # Extract the config file name
                        parts = line.split("configs/")
                    if len(parts) > 1:
                        active_config = parts[1].split(".yaml")[0]
                        break
            except Exception:
                pass

        # List all yaml files
        configs = list(self.configs_dir.glob("*.yaml"))
        if not configs:
            print("  No configurations found.")
            print(f"\nCreate a configuration file in {self.configs_dir}/")
            return 1

        for config_file in sorted(configs):
            name = config_file.stem
            if name == active_config:
                print(f"  ● {name} (active)")
            else:
                print(f"  ○ {name}")

        return 0

    def edit_config(self, config_name: str = "default") -> int:
        """
        Open a configuration file in the default editor.

        Args:
            config_name: Name of the config file (without .yaml extension)
        """
        # Remove .yaml if provided
        config_name = config_name.replace(".yaml", "")
        config_file = self.configs_dir / f"{config_name}.yaml"

        if not config_file.exists():
            print(f"Configuration not found: {config_file}")
            print("\nAvailable configurations:")
            self.list_configs()
            return 1

        # Get editor from environment or default to nano
        editor = os.environ.get("EDITOR", "nano")

        print(f"Opening {config_file} in {editor}...")
        result = subprocess.run([editor, str(config_file)])

        if result.returncode == 0:
            print("\nConfiguration edited.")
            response = input("Restart Decky to apply changes? [Y/n] ")
            if response.lower() != "n":
                return self.restart_service()

        return result.returncode

    def use_config(self, config_name: str) -> int:
        """
        Switch to a different configuration file.

        Args:
            config_name: Name of the config file to use
        """
        # Remove .yaml if provided
        config_name = config_name.replace(".yaml", "")
        config_file = self.configs_dir / f"{config_name}.yaml"

        if not config_file.exists():
            print(f"Configuration not found: {config_file}")
            print("\nAvailable configurations:")
            self.list_configs()
            return 1

        # Update the service file
        if not self.service_file.exists():
            print(f"Service file not found: {self.service_file}")
            print("Please install the service first.")
            return 1

        try:
            # Read the service file
            content = self.service_file.read_text()

            # Replace the config path in ExecStart
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("ExecStart="):
                    # Find and replace the config file path
                    if "configs/" in line:
                        old_config = line.split("configs/")[1].split()[0]
                        new_line = line.replace(old_config, f"{config_name}.yaml")
                        lines[i] = new_line
                        break

            # Write back the updated service file
            self.service_file.write_text("\n".join(lines))

            # Reload systemd and restart service
            print(f"Switching to configuration: {config_name}")
            subprocess.run(["systemctl", "--user", "daemon-reload"])

            return self.restart_service()

        except Exception as e:
            print(f"Failed to update service configuration: {e}")
            return 1

    def validate_config(self, config_name: str = "default") -> int:
        """
        Validate a configuration file.

        Args:
            config_name: Name of the config file to validate
        """
        # Remove .yaml if provided
        config_name = config_name.replace(".yaml", "")
        config_file = self.configs_dir / f"{config_name}.yaml"

        if not config_file.exists():
            print(f"Configuration not found: {config_file}")
            return 1

        print(f"Validating {config_file}...")

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            # Basic validation checks
            errors = []
            warnings = []

            # Check required sections
            if "pages" not in config:
                errors.append("Missing required 'pages' section")
            else:
                if "main" not in config["pages"]:
                    warnings.append("No 'main' page defined (will show blank screen)")

            # Check device settings
            if "device" in config:
                brightness = config["device"].get("brightness", 75)
                if not 0 <= brightness <= 100:
                    warnings.append(f"Brightness {brightness} is out of range (0-100)")

            # Check styles
            if "styles" not in config:
                warnings.append("No 'styles' section defined (will use defaults)")

            # Validate page structure
            if "pages" in config:
                for page_name, page_config in config["pages"].items():
                    if "buttons" not in page_config:
                        warnings.append(f"Page '{page_name}' has no buttons defined")
                    else:
                        for button_num, button_config in page_config["buttons"].items():
                            try:
                                button_int = int(button_num)
                                if button_int < 1 or button_int > 32:
                                    warnings.append(
                                        f"Button {button_num} is out of typical range (1-32)"
                                    )
                            except ValueError:
                                errors.append(f"Invalid button number: {button_num}")

                            # Check actions
                            if "action" in button_config:
                                action = button_config["action"]
                                if "type" not in action:
                                    warnings.append(f"Button {button_num} has action without type")

            # Print results
            if errors:
                print("\n❌ Validation FAILED with errors:")
                for error in errors:
                    print(f"  ERROR: {error}")
            else:
                print("\n✅ Configuration is valid")

            if warnings:
                print("\n⚠️  Warnings:")
                for warning in warnings:
                    print(f"  WARNING: {warning}")

            if not errors and not warnings:
                print("\n✨ Configuration looks good!")

            return 1 if errors else 0

        except yaml.YAMLError as e:
            print(f"\n❌ YAML syntax error:\n  {e}")
            return 1
        except Exception as e:
            print(f"\n❌ Error reading configuration:\n  {e}")
            return 1

    def enable_service(self) -> int:
        """Enable the service to start automatically on login."""
        print("Enabling Decky service...")
        result = subprocess.run(
            ["systemctl", "--user", "enable", self.service_name], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("Decky will start automatically on login.")
        else:
            print(f"Failed to enable service: {result.stderr}")

        return result.returncode

    def disable_service(self) -> int:
        """Disable the service from starting automatically."""
        print("Disabling Decky service...")
        result = subprocess.run(
            ["systemctl", "--user", "disable", self.service_name], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("Decky will not start automatically on login.")
        else:
            print(f"Failed to disable service: {result.stderr}")

        return result.returncode


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="decky",
        description="Decky - Stream Deck controller for Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  decky run ~/.decky/configs/kde.yaml    # Run daemon directly
  decky start                            # Start service
  decky stop                             # Stop service
  decky status                           # Show service status
  decky logs                             # Follow service logs
  decky config list                      # List configurations
  decky config edit work                 # Edit work.yaml
  decky config use kde                   # Switch to kde.yaml
  decky config validate myconfig         # Validate myconfig.yaml
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command (for daemon mode)
    run_parser = subparsers.add_parser("run", help="Run the daemon directly")
    run_parser.add_argument("config", help="Path to configuration file")
    run_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    # Service management commands
    subparsers.add_parser("start", help="Start the Decky service")
    subparsers.add_parser("stop", help="Stop the Decky service")
    subparsers.add_parser("restart", help="Restart the Decky service")
    subparsers.add_parser("status", help="Show service status")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show service logs")
    logs_parser.add_argument(
        "-f", "--follow", action="store_true", default=True, help="Follow log output (default)"
    )
    logs_parser.add_argument(
        "-n", "--lines", type=int, default=50, help="Number of lines to show (when not following)"
    )
    logs_parser.add_argument(
        "--no-follow", action="store_true", help="Don't follow, just show recent logs"
    )

    # Config subcommands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command")

    config_subparsers.add_parser("list", help="List available configurations")

    edit_parser = config_subparsers.add_parser("edit", help="Edit a configuration")
    edit_parser.add_argument(
        "name", nargs="?", default="default", help="Configuration name (default: default)"
    )

    use_parser = config_subparsers.add_parser("use", help="Switch to a configuration")
    use_parser.add_argument("name", help="Configuration name to use")

    validate_parser = config_subparsers.add_parser("validate", help="Validate a configuration")
    validate_parser.add_argument(
        "name", nargs="?", default="default", help="Configuration name (default: default)"
    )

    # Service enable/disable
    subparsers.add_parser("enable", help="Enable automatic start on login")
    subparsers.add_parser("disable", help="Disable automatic start")

    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    cli = DeckyCLI()

    # Handle commands
    if args.command == "run":
        # Run as daemon
        return cli.run_daemon(args.config, args.log_level)

    elif args.command == "start":
        return cli.start_service()

    elif args.command == "stop":
        return cli.stop_service()

    elif args.command == "restart":
        return cli.restart_service()

    elif args.command == "status":
        return cli.show_status()

    elif args.command == "logs":
        follow = not args.no_follow
        return cli.show_logs(follow=follow, lines=args.lines)

    elif args.command == "config":
        if args.config_command == "list":
            return cli.list_configs()
        elif args.config_command == "edit":
            return cli.edit_config(args.name)
        elif args.config_command == "use":
            return cli.use_config(args.name)
        elif args.config_command == "validate":
            return cli.validate_config(args.name)
        else:
            parser.print_help()
            return 1

    elif args.command == "enable":
        return cli.enable_service()

    elif args.command == "disable":
        return cli.disable_service()

    else:
        # No command specified, show help
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
