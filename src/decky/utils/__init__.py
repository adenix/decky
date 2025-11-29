"""
Utility modules for Decky.
"""

from .errors import (
    ActionExecutionError,
    ConfigurationError,
    DeckyError,
    DeviceError,
    PlatformError,
    error_boundary,
    safe_execute,
)

__all__ = [
    "DeckyError",
    "DeviceError",
    "ConfigurationError",
    "ActionExecutionError",
    "PlatformError",
    "error_boundary",
    "safe_execute",
]
