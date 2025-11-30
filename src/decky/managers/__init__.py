"""
Managers for handling specific aspects of Stream Deck control.

This module provides specialized managers for different responsibilities:
- ConnectionManager: Device connection lifecycle
- AnimationManager: GIF animation handling
- PageManager: Page rendering and button updates
- WidgetManager: Dynamic widget buttons
"""

from .animation import AnimationManager
from .connection import ConnectionManager
from .page import PageManager
from .widget import WidgetManager

__all__ = [
    "ConnectionManager",
    "AnimationManager",
    "PageManager",
    "WidgetManager",
]
