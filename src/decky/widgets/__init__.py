"""
Widget system for dynamic, auto-updating Stream Deck buttons.

Widgets are buttons that automatically update their display based on:
- Time/date
- System metrics (CPU, memory, disk)
- External APIs (weather, calendar, etc.)
- Custom data sources

This module provides the base widget infrastructure and auto-discovery system.
"""

from .base import BaseWidget, WidgetContext

__all__ = ["BaseWidget", "WidgetContext"]

