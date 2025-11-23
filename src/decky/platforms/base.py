"""
Base platform abstraction for cross-distribution support
"""

import logging
import subprocess
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class Platform(ABC):
    """Base platform class for distribution/DE specific implementations"""

    name: str = "base"
    desktop_environment: Optional[str] = None

    @abstractmethod
    def detect(self) -> bool:
        """
        Detect if this platform is currently running

        Returns:
            True if this platform is detected
        """
        pass

    @abstractmethod
    def launch_application(self, app_id: str) -> bool:
        """
        Launch an application using platform-specific methods

        Args:
            app_id: Application identifier or command

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def is_screen_locked(self) -> bool:
        """
        Check if screen is currently locked

        Returns:
            True if locked
        """
        pass

    def get_media_player_command(self, action: str) -> Optional[str]:
        """
        Get media player control command

        Args:
            action: play-pause, next, previous, stop

        Returns:
            Command string or None if not supported
        """
        return None

    def get_volume_command(self, action: str, value: Optional[int] = None) -> Optional[str]:
        """
        Get volume control command

        Args:
            action: increase, decrease, mute, set
            value: Volume value for set action

        Returns:
            Command string or None if not supported
        """
        return None

    def execute_command(self, command: str) -> bool:
        """
        Execute a shell command

        Args:
            command: Command to execute

        Returns:
            True if successful
        """
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False
