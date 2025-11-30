"""
System monitoring widgets for CPU, memory, disk, etc.
"""

import logging
import threading
from typing import Any, Dict

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .base import BaseWidget

logger = logging.getLogger(__name__)


class CPUWidget(BaseWidget):
    """
    Display CPU usage percentage.

    Configuration:
        interval: Measurement interval in seconds (default: 0.5)

    Example:
        widget:
          type: cpu
    """

    widget_type = "cpu"
    update_interval = 2.0  # Update every 2 seconds

    def validate_config(self) -> bool:
        """Check if psutil is available."""
        if not PSUTIL_AVAILABLE:
            logger.error("CPU widget requires 'psutil' package. Install with: pip install psutil")
            return False
        return True

    def fetch_data(self) -> float:
        """Get CPU percentage."""
        if not PSUTIL_AVAILABLE:
            return 0.0

        try:
            # Use non-blocking call (returns percentage since last call)
            # This prevents blocking the main event loop
            return psutil.cpu_percent(interval=None)
        except Exception as e:
            logger.error(f"Failed to fetch CPU data: {e}")
            return self._cached_data if self._cached_data is not None else 0.0

    def render_text(self, data: float) -> str:
        """Format CPU usage as text."""
        icon = self.config.get("icon", "💻")
        if data is None:
            return f"{icon}\nCPU\nN/A"
        return f"{icon}\nCPU\n{data:.1f}%"

    def get_fallback_data(self) -> float:
        """Return 0.0 as fallback."""
        return 0.0


class MemoryWidget(BaseWidget):
    """
    Display memory usage.

    Configuration:
        show_details: Show used/total GB (default: False)

    Example:
        widget:
          type: memory
          show_details: true
    """

    widget_type = "memory"
    update_interval = 5.0  # Update every 5 seconds

    def validate_config(self) -> bool:
        """Check if psutil is available."""
        if not PSUTIL_AVAILABLE:
            logger.error(
                "Memory widget requires 'psutil' package. Install with: pip install psutil"
            )
            return False
        return True

    def fetch_data(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not PSUTIL_AVAILABLE:
            return {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0}

        try:
            mem = psutil.virtual_memory()
            return {
                "percent": mem.percent,
                "used_gb": mem.used / (1024**3),
                "total_gb": mem.total / (1024**3),
            }
        except Exception as e:
            logger.error(f"Failed to fetch memory data: {e}")
            return self._cached_data if self._cached_data else {"percent": 0.0}

    def render_text(self, data: Dict[str, Any]) -> str:
        """Format memory usage as text."""
        icon = self.config.get("icon", "💾")
        show_details = self.config.get("show_details", False)

        if data is None or "percent" not in data:
            return f"{icon}\nRAM\nN/A"

        if show_details and "used_gb" in data:
            return f"{icon}\nRAM\n{data['used_gb']:.1f}/{data['total_gb']:.1f}GB"
        else:
            return f"{icon}\nRAM\n{data['percent']:.1f}%"

    def get_fallback_data(self) -> Dict[str, Any]:
        """Return zero values as fallback."""
        return {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0}


class DiskWidget(BaseWidget):
    """
    Display disk usage.

    Configuration:
        path: Disk path to monitor (default: "/")
        show_free: Show free space instead of used (default: False)

    Example:
        widget:
          type: disk
          path: "/home"
          show_free: true
    """

    widget_type = "disk"
    update_interval = 30.0  # Update every 30 seconds (disk changes slowly)

    def validate_config(self) -> bool:
        """Check if psutil is available."""
        if not PSUTIL_AVAILABLE:
            logger.error("Disk widget requires 'psutil' package. Install with: pip install psutil")
            return False
        return True

    def fetch_data(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        if not PSUTIL_AVAILABLE:
            return {"percent": 0.0, "free_gb": 0.0}

        path = self.config.get("path", "/")

        try:
            disk = psutil.disk_usage(path)
            return {
                "percent": disk.percent,
                "free_gb": disk.free / (1024**3),
                "used_gb": disk.used / (1024**3),
                "total_gb": disk.total / (1024**3),
            }
        except Exception as e:
            logger.error(f"Failed to fetch disk data for {path}: {e}")
            return self._cached_data if self._cached_data else {"percent": 0.0}

    def render_text(self, data: Dict[str, Any]) -> str:
        """Format disk usage as text."""
        icon = self.config.get("icon", "💿")
        show_free = self.config.get("show_free", False)

        if data is None or "percent" not in data:
            return f"{icon}\nDisk\nN/A"

        if show_free and "free_gb" in data:
            return f"{icon}\nDisk\n{data['free_gb']:.1f}GB free"
        else:
            return f"{icon}\nDisk\n{data['percent']:.1f}%"

    def get_fallback_data(self) -> Dict[str, Any]:
        """Return zero values as fallback."""
        return {"percent": 0.0, "free_gb": 0.0, "used_gb": 0.0, "total_gb": 0.0}


class NetworkWidget(BaseWidget):
    """
    Display network statistics.

    Shows upload/download speeds.

    Example:
        widget:
          type: network
    """

    widget_type = "network"
    update_interval = 2.0  # Update every 2 seconds

    def __init__(self, config: Dict[str, Any]):
        """Initialize network widget with baseline counters."""
        super().__init__(config)
        self._last_bytes_sent = 0
        self._last_bytes_recv = 0
        self._last_time = 0.0
        self._lock = threading.Lock()  # Protect state from concurrent access

    def validate_config(self) -> bool:
        """Check if psutil is available."""
        if not PSUTIL_AVAILABLE:
            logger.error(
                "Network widget requires 'psutil' package. Install with: pip install psutil"
            )
            return False
        return True

    def fetch_data(self) -> Dict[str, Any]:
        """Get network speed in KB/s."""
        if not PSUTIL_AVAILABLE:
            return {"upload_kbps": 0.0, "download_kbps": 0.0}

        try:
            import time

            with self._lock:  # Thread-safe access to instance variables
                net_io = psutil.net_io_counters()
                current_time = time.time()

                # Calculate speed since last update
                if self._last_time > 0:
                    time_delta = current_time - self._last_time
                    bytes_sent = net_io.bytes_sent - self._last_bytes_sent
                    bytes_recv = net_io.bytes_recv - self._last_bytes_recv

                    upload_kbps = (bytes_sent / time_delta) / 1024 if time_delta > 0 else 0
                    download_kbps = (bytes_recv / time_delta) / 1024 if time_delta > 0 else 0
                else:
                    upload_kbps = 0.0
                    download_kbps = 0.0

                # Store current values for next calculation
                self._last_bytes_sent = net_io.bytes_sent
                self._last_bytes_recv = net_io.bytes_recv
                self._last_time = current_time

                return {"upload_kbps": upload_kbps, "download_kbps": download_kbps}

        except Exception as e:
            logger.error(f"Failed to fetch network data: {e}")
            return self._cached_data if self._cached_data else {"upload_kbps": 0.0, "download_kbps": 0.0}

    def render_text(self, data: Dict[str, Any]) -> str:
        """Format network speed as text."""
        icon = self.config.get("icon", "🌐")
        
        if data is None or "upload_kbps" not in data:
            return f"{icon}\nNet\nN/A"
        
        up = data["upload_kbps"]
        down = data["download_kbps"]

        # Format with appropriate units
        if down > 1024:
            down_str = f"{down/1024:.1f}MB/s"
        else:
            down_str = f"{down:.0f}KB/s"

        if up > 1024:
            up_str = f"{up/1024:.1f}MB/s"
        else:
            up_str = f"{up:.0f}KB/s"

        return f"{icon}\n↓{down_str}\n↑{up_str}"

    def get_fallback_data(self) -> Dict[str, Any]:
        """Return zero values as fallback."""
        return {"upload_kbps": 0.0, "download_kbps": 0.0}

