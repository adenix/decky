"""
Page switching action
"""

import logging
from typing import Any, Dict

from .base import ActionContext, BaseAction

logger = logging.getLogger(__name__)


class PageAction(BaseAction):
    """Switch between Stream Deck pages"""

    action_type = "page"

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """Switch to a different page"""
        page = config.get("page")
        if not page:
            logger.error("Page action requires 'page' parameter")
            return False

        # Page switching is handled directly in the controller
        # This action just validates the configuration
        return True

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate page configuration"""
        if "page" not in config:
            logger.error("Page action requires 'page' parameter")
            return False
        return True

    def get_required_params(self) -> list:
        return ["page"]
