"""
Date/time widget for displaying time and date information.
"""

import logging
from datetime import datetime
from typing import Any

from .base import BaseWidget

logger = logging.getLogger(__name__)


class DateTimeWidget(BaseWidget):
    """
    Display current date and/or time with configurable format and update interval.

    Configuration:
        format: strftime format string (required)
        update_interval: Update frequency in seconds (optional, auto-detected if not set)
        timezone: Timezone name (future enhancement)

    The widget automatically detects the optimal update interval based on format:
    - Contains seconds (%S) → 1 second updates
    - Contains minutes (%M) → 10 second updates  
    - Date only → 60 second updates

    Examples:
        # Clock with seconds
        widget:
          type: datetime
          format: "%H:%M:%S"
          # Auto-detects: update_interval = 1.0

        # Clock without seconds
        widget:
          type: datetime
          format: "%I:%M %p"
          # Auto-detects: update_interval = 10.0

        # Date only
        widget:
          type: datetime
          format: "%a\\n%b %d"
          # Auto-detects: update_interval = 60.0

        # Custom update interval
        widget:
          type: datetime
          format: "%H:%M:%S"
          update_interval: 0.5  # Update twice per second
    """

    widget_type = "datetime"
    update_interval = None  # Will be set in __init__ based on format

    def __init__(self, config):
        """Initialize with auto-detected update interval."""
        super().__init__(config)
        
        # Auto-detect update interval if not specified
        if self.update_interval is None:
            format_str = config.get("format", "%H:%M:%S")
            
            # Check if format includes seconds
            if "%S" in format_str:
                self.update_interval = 1.0  # Update every second
            # Check if format includes minutes/hours but not seconds
            elif any(x in format_str for x in ["%M", "%H", "%I", "%p"]):
                self.update_interval = 10.0  # Update every 10 seconds (catches minute changes)
            # Date-only format
            else:
                self.update_interval = 60.0  # Update every minute
            
            # Allow manual override
            if "update_interval" in config:
                self.update_interval = config["update_interval"]
                
            logger.debug(
                f"DateTimeWidget auto-detected update_interval={self.update_interval}s "
                f"for format '{format_str}'"
            )

    def fetch_data(self) -> datetime:
        """Get current date/time."""
        return datetime.now()

    def render_text(self, data: datetime) -> str:
        """Format date/time as text."""
        if data is None:
            return "---"
        
        format_str = self.config.get("format", "%H:%M:%S")
        try:
            return data.strftime(format_str)
        except Exception as e:
            logger.error(f"Invalid datetime format '{format_str}': {e}")
            return data.strftime("%H:%M:%S")  # Fallback to default

    def get_fallback_data(self) -> datetime:
        """Return current datetime as fallback."""
        return datetime.now()

