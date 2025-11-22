"""
Action registry for managing and discovering action types
"""

import logging
from typing import Dict, Type, Optional
from .base import BaseAction

logger = logging.getLogger(__name__)


class ActionRegistry:
    """Registry for all available action types"""

    def __init__(self):
        self._actions: Dict[str, Type[BaseAction]] = {}
        self._instances: Dict[str, BaseAction] = {}

    def register(self, action_class: Type[BaseAction]) -> None:
        """Register an action class"""
        if not issubclass(action_class, BaseAction):
            raise TypeError(f"{action_class} must inherit from BaseAction")

        action = action_class()
        if action.action_type in self._actions:
            logger.warning(f"Overwriting existing action type: {action.action_type}")

        self._actions[action.action_type] = action_class
        self._instances[action.action_type] = action
        logger.debug(f"Registered action type: {action.action_type}")

    def get_action(self, action_type: str) -> Optional[BaseAction]:
        """Get an action instance by type"""
        return self._instances.get(action_type)

    def get_action_class(self, action_type: str) -> Optional[Type[BaseAction]]:
        """Get an action class by type"""
        return self._actions.get(action_type)

    def list_actions(self) -> list:
        """List all registered action types"""
        return list(self._actions.keys())

    def is_supported(self, action_type: str, platform: str) -> bool:
        """Check if an action is supported on a platform"""
        action = self.get_action(action_type)
        if not action:
            return False
        return action.is_platform_supported(platform)

    def auto_discover(self):
        """Auto-discover and register all action modules"""
        import importlib
        import pkgutil
        import sys

        # Import the actions package
        import decky.actions as actions_pkg

        # Discover all modules in the actions package
        for importer, modname, ispkg in pkgutil.iter_modules(actions_pkg.__path__):
            if modname in ['base', 'registry', '__init__']:
                continue

            try:
                module = importlib.import_module(f'decky.actions.{modname}')

                # Find all BaseAction subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                            issubclass(attr, BaseAction) and
                            attr is not BaseAction and
                            hasattr(attr, 'action_type')):
                        self.register(attr)
                        logger.info(f"Auto-registered action: {attr.action_type}")

            except Exception as e:
                logger.error(f"Failed to load action module {modname}: {e}")


# Global registry instance
registry = ActionRegistry()