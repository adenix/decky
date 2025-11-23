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
        """Execute a shell command"""
        command = config.get("command")
        if not command:
            logger.error("Command action requires 'command' parameter")
            return False

        logger.info(f"Executing command: {command}")
        try:
            # Use Popen for non-blocking execution
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
