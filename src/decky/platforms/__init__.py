"""
Platform abstraction for cross-distribution support
"""

from typing import Optional

from .base import Platform
from .kde import KDEPlatform


def detect_platform() -> Optional[Platform]:
    """Auto-detect the current platform"""
    platforms = [
        KDEPlatform(),
        # Add more platforms here as they're implemented
        # GNOMEPlatform(),
        # GenericLinuxPlatform(),
    ]

    for platform in platforms:
        if platform.detect():
            return platform

    # Return None if no specific platform detected
    # Controller will handle this gracefully
    return None


__all__ = [
    "Platform",
    "KDEPlatform",
    "detect_platform",
]
