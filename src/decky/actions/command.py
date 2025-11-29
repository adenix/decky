"""
Command execution action
"""

import logging
import subprocess
from typing import Any, Dict

from .base import ActionContext, BaseAction

logger = logging.getLogger(__name__)


class CommandAction(BaseAction):
    """Execute shell commands"""

    action_type = "command"

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """
        Execute a shell command.

        Security Note:
        ---------------
        This executes commands with shell=True, allowing full shell syntax and
        features (pipes, redirects, variable expansion, etc.). This is INTENTIONAL
        and part of Decky's design as a personal automation tool.

        ⚠️  Configuration files can execute arbitrary commands with your user permissions.
            Only load configs from trusted sources. See SECURITY.md for details.

        Args:
            context: Action execution context
            config: Must contain 'command' key with the shell command to execute

        Returns:
            True if command was launched successfully, False otherwise
        """
        command = config.get("command")
        if not command:
            logger.error("Command action requires 'command' parameter")
            return False

        logger.info(f"Executing command: {command}")
        try:
            # Use Popen for non-blocking execution with full shell capabilities
            # shell=True is intentional - enables pipes, redirects, variable expansion
            subprocess.Popen(command, shell=True)
            return True
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate command configuration"""
        if "command" not in config:
            logger.error("Command action requires 'command' parameter")
            return False
        return True

    def get_required_params(self) -> list:
        return ["command"]
