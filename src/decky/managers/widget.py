"""
Widget management for dynamic button content.

This module manages the lifecycle of widget buttons including setup,
update scheduling, and rendering coordination.
"""

import copy
import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WidgetManager:
    """
    Manages dynamic widget buttons.

    Responsibilities:
    - Widget lifecycle management
    - Scheduled updates based on intervals
    - Render coordination with ButtonRenderer
    - Widget state caching with memory limits
    """

    # Maximum cache size per widget in bytes (100KB default)
    MAX_CACHE_SIZE = 100 * 1024
    
    # Maximum total cache size for all widgets (5MB default)
    MAX_TOTAL_CACHE_SIZE = 5 * 1024 * 1024

    def __init__(self, button_renderer, animation_manager=None):
        """
        Initialize the widget manager.

        Args:
            button_renderer: ButtonRenderer instance for rendering frames
            animation_manager: AnimationManager instance for animated backgrounds (optional)
        """
        self.button_renderer = button_renderer
        self.animation_manager = animation_manager
        self.widget_registry = WidgetRegistry()
        self.active_widgets: Dict[int, Dict[str, Any]] = {}  # {key_index: widget_data}
        self._last_check = 0.0
        self._widget_lock = threading.Lock()  # Prevent concurrent widget updates/page switches
        self._total_cache_size = 0  # Track total memory usage

    def setup_widget_button(
        self, key_index: int, button_config: Dict[str, Any], styles: Dict[str, Any]
    ) -> bool:
        """
        Set up a widget for a button.

        Args:
            key_index: Zero-based button index
            button_config: Button config with 'widget' section
            styles: Style configuration

        Returns:
            True if widget was set up successfully, False otherwise
        """
        widget_config = button_config.get("widget")
        if not widget_config:
            return False

        widget_type = widget_config.get("type")
        if not widget_type:
            logger.error(f"Widget missing 'type' for button {key_index + 1}")
            return False

        # Get widget class from registry
        widget_class = self.widget_registry.get_widget_class(widget_type)
        if not widget_class:
            logger.error(f"Unknown widget type: {widget_type}")
            return False

        try:
            # Instantiate widget
            widget = widget_class(widget_config)

            # Validate configuration
            if not widget.validate_config():
                logger.error(f"Invalid config for {widget_type} widget on button {key_index + 1}")
                return False

            # Store widget data (thread-safe)
            with self._widget_lock:
                self.active_widgets[key_index] = {
                    "widget": widget,
                    "button_config": button_config,
                    "last_render": 0.0,
                    "cached_image": None,
                    "cached_text": None,  # Cache rendered text separately
                }

            logger.info(f"Initialized {widget_type} widget for button {key_index + 1}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize widget: {e}", exc_info=True)
            return False

    def render_widget(
        self,
        key_index: int,
        styles: Dict[str, Any],
        deck: Any,
        force: bool = False,
    ) -> Optional[bytes]:
        """
        Render a widget button.

        Args:
            key_index: Zero-based button index
            styles: Style configuration
            deck: Stream Deck device
            force: Force re-render even if not time to update

        Returns:
            Rendered button image as bytes, or None
        """
        if key_index not in self.active_widgets:
            return None

        widget_data = self.active_widgets[key_index]
        widget = widget_data["widget"]
        current_time = time.time()

        # Check if update is needed
        if not force and not widget.should_update(current_time):
            # Return cached image if available
            return widget_data.get("cached_image")

        try:
            # Fetch fresh data
            data = widget.fetch_data()
            widget._last_update = current_time
            widget._cached_data = data

            # Render text
            text = widget.render_text(data)
            
            # Cache the text separately (for compositor to use)
            widget_data["cached_text"] = text

            # Create modified button config with rendered text (deep copy to avoid mutations)
            button_config = copy.deepcopy(widget_data["button_config"])
            button_config["text"] = text

            # Check if this widget has an animated GIF background
            # If so, use the current animation frame instead of static icon
            if self.animation_manager and key_index in self.animation_manager.animated_buttons:
                anim_data = self.animation_manager.animated_buttons[key_index]
                current_frame = anim_data["frames"][anim_data["current_frame"]]
                image = self.button_renderer.render_button_with_icon(
                    button_config, styles, deck, current_frame
                )
            else:
                # Check for dynamic icon from widget
                icon = widget.render_icon(data)
                if icon:
                    image = self.button_renderer.render_button_with_icon(
                        button_config, styles, deck, icon
                    )
                else:
                    image = self.button_renderer.render_button(button_config, styles, deck)

            # Cache rendered image with size tracking
            old_image = widget_data.get("cached_image")
            if old_image:
                self._total_cache_size -= len(old_image)
            
            if image:
                image_size = len(image)
                # Only cache if within reasonable size limits
                if image_size <= self.MAX_CACHE_SIZE:
                    widget_data["cached_image"] = image
                    self._total_cache_size += image_size
                    
                    # If total cache too large, clear oldest caches
                    if self._total_cache_size > self.MAX_TOTAL_CACHE_SIZE:
                        self._evict_cache()
                else:
                    logger.warning(f"Widget image too large to cache: {image_size} bytes")
                    widget_data["cached_image"] = None
            
            widget_data["last_render"] = current_time

            return image

        except Exception as e:
            logger.error(f"Error rendering widget on button {key_index + 1}: {e}", exc_info=True)
            return widget_data.get("cached_image")  # Return cached on error

    def update_widgets(self, deck: Any, styles: Dict[str, Any]) -> Dict[int, bytes]:
        """
        Update all widgets that need refreshing.

        Args:
            deck: Stream Deck device instance
            styles: Style configuration dictionary

        Returns:
            Dictionary of {key_index: rendered_image} for buttons needing update
        """
        with self._widget_lock:  # Thread-safe widget updates
            if not self.active_widgets:
                return {}

            current_time = time.time()
            updates = {}

            for key_index, widget_data in self.active_widgets.items():
                widget = widget_data["widget"]

                # Check if update needed
                if widget.should_update(current_time):
                    image = self.render_widget(key_index, styles, deck)
                    if image:
                        updates[key_index] = image

            return updates

    def clear_widgets(self) -> None:
        """Clear all widgets (called on page switch)."""
        with self._widget_lock:  # Thread-safe widget clearing
            self.active_widgets.clear()
            self._total_cache_size = 0  # Reset cache size tracking
            logger.debug("Cleared all widgets")

    def has_widgets(self) -> bool:
        """Check if any widgets are active."""
        return len(self.active_widgets) > 0

    def get_widget_count(self) -> int:
        """Get the count of active widgets."""
        return len(self.active_widgets)

    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        return self._total_cache_size

    def get_widget_text(self, key_index: int) -> Optional[str]:
        """
        Get cached text for a widget without triggering a re-render.
        
        Used by the compositor to overlay text on animated backgrounds.
        
        Args:
            key_index: Zero-based button index
            
        Returns:
            Cached widget text or None
        """
        if key_index not in self.active_widgets:
            return None
        return self.active_widgets[key_index].get("cached_text")

    def _evict_cache(self) -> None:
        """Evict oldest cached images when memory limit exceeded."""
        logger.debug(f"Cache size exceeded ({self._total_cache_size} bytes), evicting old entries")
        
        # Sort widgets by last render time
        sorted_widgets = sorted(
            self.active_widgets.items(),
            key=lambda x: x[1].get("last_render", 0)
        )
        
        # Clear caches until we're under limit
        for key_index, widget_data in sorted_widgets:
            cached_image = widget_data.get("cached_image")
            if cached_image:
                self._total_cache_size -= len(cached_image)
                widget_data["cached_image"] = None
                logger.debug(f"Evicted cache for widget on button {key_index + 1}")
                
                if self._total_cache_size <= self.MAX_TOTAL_CACHE_SIZE * 0.8:  # 80% threshold
                    break


class WidgetRegistry:
    """
    Registry for auto-discovering widget types.

    Uses the same pattern as ActionRegistry for consistency.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._widgets: Dict[str, type] = {}

    def register(self, widget_class: type) -> None:
        """
        Register a widget class.

        Args:
            widget_class: Widget class to register

        Raises:
            TypeError: If widget_class doesn't inherit from BaseWidget
            ValueError: If widget_type is not defined
        """
        from decky.widgets.base import BaseWidget

        if not issubclass(widget_class, BaseWidget):
            raise TypeError(f"{widget_class} must inherit from BaseWidget")

        # Get widget_type from class attribute (no need to instantiate)
        widget_type = widget_class.widget_type
        
        if not widget_type:
            raise ValueError(f"{widget_class.__name__} must define widget_type class attribute")

        if widget_type in self._widgets:
            logger.warning(f"Overwriting existing widget type: {widget_type}")

        self._widgets[widget_type] = widget_class
        logger.debug(f"Registered widget type: {widget_type}")

    def get_widget_class(self, widget_type: str):
        """
        Get widget class by type.

        Args:
            widget_type: Widget type identifier

        Returns:
            Widget class or None if not found
        """
        return self._widgets.get(widget_type)

    def list_widgets(self) -> list:
        """
        List all registered widget types.

        Returns:
            List of widget type identifiers
        """
        return list(self._widgets.keys())

    def auto_discover(self) -> None:
        """Auto-discover and register all widget modules."""
        import importlib
        import pkgutil

        from decky.widgets.base import BaseWidget

        try:
            import decky.widgets as widgets_pkg
        except ImportError:
            logger.warning("Widgets package not found, skipping auto-discovery")
            return

        # Discover all modules in the widgets package
        for _importer, modname, _ispkg in pkgutil.iter_modules(widgets_pkg.__path__):
            if modname in ["base", "__init__"]:
                continue

            try:
                module = importlib.import_module(f"decky.widgets.{modname}")

                # Find all BaseWidget subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseWidget)
                        and attr is not BaseWidget
                        and hasattr(attr, "widget_type")
                    ):
                        self.register(attr)
                        logger.info(f"Auto-registered widget: {attr.widget_type}")

            except Exception as e:
                logger.error(f"Failed to load widget module {modname}: {e}")

