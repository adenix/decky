"""
Base classes for all widget types.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from PIL import Image

logger = logging.getLogger(__name__)


class WidgetContext:
    """
    Context provided to widgets during rendering.

    Attributes:
        button_config: Full button configuration from YAML
        deck: Stream Deck device instance
        style: Resolved style dictionary for this button
        image_size: Button image dimensions (width, height)
    """

    def __init__(self, button_config: Dict[str, Any], deck: Any, style: Dict[str, Any]):
        """
        Initialize widget context.

        Args:
            button_config: Button configuration from YAML
            deck: Stream Deck device instance
            style: Style configuration for this button
        """
        self.button_config = button_config
        self.deck = deck
        self.style = style
        self.image_size = deck.key_image_format()["size"]


class BaseWidget(ABC):
    """
    Base class for all Stream Deck widgets.

    Widgets are auto-updating buttons that display dynamic content
    like time, weather, system stats, etc.

    Class Attributes:
        widget_type: Unique identifier for this widget type (e.g., "clock", "weather")
        update_interval: How often to update in seconds (None = update every frame)

    Example:
        >>> class MyWidget(BaseWidget):
        ...     widget_type = "my_widget"
        ...     update_interval = 5.0  # Update every 5 seconds
        ...
        ...     def fetch_data(self):
        ...         return {"value": 42}
        ...
        ...     def render_text(self, data):
        ...         return f"Value: {data['value']}"
    """

    # Widget type identifier (must be unique)
    widget_type: str = None

    # Update interval in seconds (None = update every frame)
    update_interval: float = 1.0

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize widget with configuration.

        Args:
            config: Widget configuration from YAML

        Raises:
            ValueError: If widget_type is not defined
        """
        if not self.widget_type:
            raise ValueError(f"{self.__class__.__name__} must define widget_type")

        self.config = config
        self._last_update = 0.0
        self._cached_data: Optional[Any] = None

    @abstractmethod
    def fetch_data(self) -> Any:
        """
        Fetch fresh data for the widget.

        Called at intervals defined by update_interval.
        Should be fast and non-blocking.

        Returns:
            Data to be rendered (string, dict, number, etc.)

        Note:
            This method should handle errors gracefully and return
            cached data or a fallback value on failure.
        """
        pass

    @abstractmethod
    def render_text(self, data: Any) -> str:
        """
        Convert fetched data to display text.

        Args:
            data: Data from fetch_data()

        Returns:
            Formatted text string (supports multiline with \\n)

        Example:
            >>> def render_text(self, data):
            ...     return f"CPU\\n{data['percent']:.1f}%"
        """
        pass

    def render_icon(self, data: Any) -> Optional[Image.Image]:
        """
        Optionally render a dynamic icon.

        Override this to generate custom icons (e.g., weather icons,
        gauges, progress bars).

        Args:
            data: Data from fetch_data()

        Returns:
            PIL Image or None to use text only

        Example:
            >>> def render_icon(self, data):
            ...     # Create a simple gauge
            ...     img = Image.new('RGB', (72, 72), 'black')
            ...     draw = ImageDraw.Draw(img)
            ...     draw.arc([(10, 10), (62, 62)], 0, int(data['percent'] * 3.6), fill='green')
            ...     return img
        """
        return None

    def validate_config(self) -> bool:
        """
        Validate widget configuration.

        Override this to add custom validation logic.

        Returns:
            True if configuration is valid, False otherwise

        Example:
            >>> def validate_config(self):
            ...     if not self.config.get('api_key'):
            ...         logger.error("Widget requires 'api_key'")
            ...         return False
            ...     return True
        """
        return True

    def get_required_params(self) -> list:
        """
        Return list of required configuration parameters.

        Returns:
            List of required parameter names

        Example:
            >>> def get_required_params(self):
            ...     return ["location", "api_key"]
        """
        return []

    def should_update(self, current_time: float) -> bool:
        """
        Check if widget should update based on interval.

        Args:
            current_time: Current timestamp from time.time()

        Returns:
            True if widget should update, False otherwise
        """
        if self.update_interval is None:
            return True  # Always update

        return current_time - self._last_update >= self.update_interval

    def safe_fetch_data(self) -> Any:
        """
        Safely fetch data with standardized error handling.

        This is a wrapper around fetch_data() that ensures consistent
        error handling across all widgets.

        Returns:
            Fetched data on success, cached data on failure
        """
        try:
            data = self.fetch_data()
            self._cached_data = data  # Update cache on success
            return data
        except Exception as e:
            logger.error(
                f"Error fetching data for {self.widget_type} widget: {e}",
                exc_info=True
            )
            # Return cached data if available, otherwise return safe fallback
            if self._cached_data is not None:
                logger.debug(f"Using cached data for {self.widget_type} widget")
                return self._cached_data
            return self.get_fallback_data()

    def get_fallback_data(self) -> Any:
        """
        Get fallback data when fetch fails and no cache is available.

        Override this to provide widget-specific fallback values.

        Returns:
            Safe fallback data (default: None)
        """
        return None

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<{self.__class__.__name__}(type={self.widget_type}, interval={self.update_interval})>"

