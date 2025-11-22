"""
Application launcher action with platform-specific implementations
"""

import subprocess
import os
import logging
from typing import Dict, Any
from .base import BaseAction, ActionContext

logger = logging.getLogger(__name__)


class ApplicationAction(BaseAction):
    """Launch desktop applications"""

    action_type = "application"

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """Launch an application"""
        app = config.get("app")
        if not app:
            logger.error("Application action requires 'app' parameter")
            return False

        logger.info(f"Launching application: {app}")

        # Use platform-specific launcher if available
        if context.platform:
            return context.platform.launch_application(app)

        # Fallback to generic launcher
        return self._generic_launch(app)

    def _generic_launch(self, app: str) -> bool:
        """Generic application launcher"""
        launcher_script = os.path.expanduser("~/.decky/scripts/launch-application.sh")

        if os.path.exists(launcher_script):
            try:
                subprocess.Popen(
                    [launcher_script, app],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except Exception as e:
                logger.error(f"Failed to launch via script: {e}")

        # Fallback to direct execution
        try:
            subprocess.Popen(app, shell=True)
            return True
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate application configuration"""
        if "app" not in config:
            logger.error("Application action requires 'app' parameter")
            return False
        return True

    def get_required_params(self) -> list:
        return ["app"]