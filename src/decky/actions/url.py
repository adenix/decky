"""
URL opening action
"""

import subprocess
import logging
from typing import Dict, Any
from .base import BaseAction, ActionContext

logger = logging.getLogger(__name__)


class URLAction(BaseAction):
    """Open URLs in the default browser"""

    action_type = "url"

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """Open a URL"""
        url = config.get("url")
        if not url:
            logger.error("URL action requires 'url' parameter")
            return False

        logger.info(f"Opening URL: {url}")
        try:
            # Use xdg-open for cross-desktop compatibility
            subprocess.Popen(["xdg-open", url])
            return True
        except Exception as e:
            logger.error(f"Failed to open URL: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate URL configuration"""
        if "url" not in config:
            logger.error("URL action requires 'url' parameter")
            return False
        return True

    def get_required_params(self) -> list:
        return ["url"]