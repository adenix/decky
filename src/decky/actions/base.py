"""
Base action class for all Stream Deck button actions
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ActionContext:
    """Context passed to actions during execution"""

    def __init__(self, controller, button_config: Dict[str, Any], key_index: int):
        self.controller = controller
        self.button_config = button_config
        self.key_index = key_index
        self.platform = controller.platform if hasattr(controller, "platform") else None


class BaseAction(ABC):
    """Base class for all action types"""

    # Action type identifier (must be unique)
    action_type: str = None

    # Platform requirements (None means all platforms)
    supported_platforms: Optional[list] = None

    def __init__(self):
        if not self.action_type:
            raise ValueError(f"{self.__class__.__name__} must define action_type")

    @abstractmethod
    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """
        Execute the action

        Args:
            context: Action execution context
            config: Action configuration from YAML

        Returns:
            True if successful, False otherwise
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate action configuration

        Override this to add custom validation

        Args:
            config: Action configuration from YAML

        Returns:
            True if valid, False otherwise
        """
        return True

    def is_platform_supported(self, platform_name: str) -> bool:
        """Check if this action supports the given platform"""
        if self.supported_platforms is None:
            return True
        return platform_name in self.supported_platforms

    def get_required_params(self) -> list:
        """
        Return list of required parameters for this action

        Override this to specify requirements
        """
        return []

    def get_optional_params(self) -> list:
        """
        Return list of optional parameters for this action

        Override this to specify optional params
        """
        return []
