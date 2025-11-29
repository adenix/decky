"""
Base action class for all Stream Deck button actions
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ActionContext:
    """
    Context passed to actions during execution.

    Provides actions with access to the controller, button configuration,
    and platform-specific capabilities.

    Attributes:
        controller: Reference to DeckyController instance
        button_config: Full configuration dictionary for the button
        key_index: Zero-based index of the button that was pressed
        platform: Platform instance for platform-specific operations (may be None)

    Example:
        >>> context = ActionContext(
        ...     controller=my_controller,
        ...     button_config={"label": "Test", "action": {"type": "command"}},
        ...     key_index=0
        ... )
        >>> context.platform.launch_application("firefox")
    """

    def __init__(self, controller, button_config: Dict[str, Any], key_index: int):
        """
        Initialize action context.

        Args:
            controller: DeckyController instance
            button_config: Button configuration from YAML
            key_index: Zero-based button index
        """
        self.controller = controller
        self.button_config = button_config
        self.key_index = key_index
        self.platform = controller.platform if hasattr(controller, "platform") else None


class BaseAction(ABC):
    """
    Base class for all Stream Deck button action types.

    All action types must inherit from this class and implement the execute() method.
    The action system uses a registry pattern to discover and register actions.

    Class Attributes:
        action_type: Unique identifier for this action (e.g., "command", "url")
        supported_platforms: List of platform names this action supports,
                           or None for all platforms

    Example:
        >>> class MyAction(BaseAction):
        ...     action_type = "my_action"
        ...
        ...     def execute(self, context, config):
        ...         # Do something
        ...         return True
        ...
        ...     def get_required_params(self):
        ...         return ["my_param"]

    See Also:
        - ActionContext: Context passed to execute()
        - ActionRegistry: Auto-discovers and registers actions
    """

    # Action type identifier (must be unique)
    action_type: str = None

    # Platform requirements (None means all platforms)
    supported_platforms: Optional[list] = None

    def __init__(self):
        """
        Initialize the action.

        Raises:
            ValueError: If action_type is not defined
        """
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
