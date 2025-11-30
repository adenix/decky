"""
Connection management for Stream Deck devices.

Handles device connection lifecycle, health monitoring, and reconnection logic.
"""

import logging
import threading
import time
from typing import Any, Callable, Optional

from ..device.manager import DeviceManager
from ..platforms.base import Platform

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages Stream Deck device connection lifecycle.

    Responsibilities:
    - Device connection and disconnection
    - Connection health monitoring
    - Automatic reconnection on device hot-plug
    - Screen lock/unlock integration
    """

    # Timing constants
    RECONNECT_INTERVAL = 2.0  # Seconds between reconnection attempts
    CONNECTION_CHECK_INTERVAL = 0.5  # How often to check connection status

    def __init__(
        self,
        device_manager: DeviceManager,
        platform: Optional[Platform] = None,
        on_connected: Optional[Callable[[Any], None]] = None,
        on_disconnected: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the connection manager.

        Args:
            device_manager: Device manager for low-level operations
            platform: Platform instance for screen lock detection
            on_connected: Callback when device connects (receives deck object)
            on_disconnected: Callback when device disconnects
        """
        self.device_manager = device_manager
        self.platform = platform
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected

        self.deck: Optional[Any] = None
        self.running = False
        self.shutting_down = False
        self.is_locked = False

        self._monitor_thread: Optional[threading.Thread] = None
        self._last_reconnect_attempt = 0.0
        self._last_connection_check = 0.0

    def connect(self) -> bool:
        """
        Establish connection to a Stream Deck device.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            logger.debug("Attempting to connect to Stream Deck...")
            self.deck = self.device_manager.connect()

            if not self.deck:
                logger.debug("No Stream Deck device available")
                return False

            logger.info(f"Connected to {self.deck.deck_type()} ({self.deck.key_count()} keys)")

            # Notify callback
            if self.on_connected:
                self.on_connected(self.deck)

            return True

        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}", exc_info=True)
            self.deck = None
            return False

    def disconnect(self) -> None:
        """
        Safely disconnect from the Stream Deck device.

        Handles both voluntary and involuntary disconnection.
        Always clears the deck reference regardless of errors.
        """
        if not self.deck:
            return

        logger.debug("Disconnecting from Stream Deck...")

        # Use device manager for clean disconnection
        clean_disconnect = self.device_manager.disconnect(self.deck)

        # Always clear our reference
        self.deck = None

        # Notify callback
        if self.on_disconnected:
            self.on_disconnected()

        if clean_disconnect:
            logger.info("Stream Deck disconnected")
        else:
            logger.info("Stream Deck disconnected (device was already unavailable)")

    def is_connected(self) -> bool:
        """
        Check if currently connected to a device.

        Returns:
            True if connected and responsive, False otherwise.
        """
        if not self.deck:
            return False

        return self.device_manager.is_connected(self.deck)

    def start_monitoring(self) -> None:
        """
        Start background thread for connection and lock monitoring.

        Monitors:
        - Device connection health (hot-unplug detection)
        - Screen lock status (auto-disconnect on lock)
        - Automatic reconnection when needed
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Connection monitoring already running")
            return

        self.running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="ConnectionMonitor"
        )
        self._monitor_thread.start()
        logger.debug("Connection monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the connection monitoring thread."""
        self.running = False
        self.shutting_down = True

        if self._monitor_thread:
            self._monitor_thread.join(timeout=3)
            self._monitor_thread = None

        logger.debug("Connection monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in background thread)."""
        while self.running:
            try:
                current_time = time.time()

                # Check connection health periodically
                if current_time - self._last_connection_check >= self.CONNECTION_CHECK_INTERVAL:
                    self._check_connection_health(current_time)
                    self._last_connection_check = current_time

                # Monitor screen lock status
                self._check_screen_lock()

                # Short sleep to prevent CPU spinning
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in connection monitor: {e}", exc_info=True)
                time.sleep(1)

    def _check_connection_health(self, current_time: float) -> None:
        """
        Check if device is still connected and attempt reconnection if needed.

        Args:
            current_time: Current timestamp for throttling reconnection
        """
        # Monitor existing connection health
        if self.deck:
            if not self.is_connected():
                logger.info("Stream Deck disconnected (device removed)")
                self.disconnect()
                # Reset timer to attempt immediate reconnection
                self._last_reconnect_attempt = 0

        # Attempt reconnection if needed (but not if locked or shutting down)
        if not self.deck and not self.is_locked and not self.shutting_down:
            # Throttle reconnection attempts to avoid USB enumeration spam
            time_since_last_attempt = current_time - self._last_reconnect_attempt
            if time_since_last_attempt >= self.RECONNECT_INTERVAL:
                logger.debug("Checking for Stream Deck devices...")
                if self.connect():
                    logger.info("Stream Deck connected and configured")
                self._last_reconnect_attempt = current_time

    def _check_screen_lock(self) -> None:
        """Monitor screen lock status and disconnect/reconnect as needed."""
        if not self.platform:
            return

        try:
            locked = self.platform.is_screen_locked()

            if locked != self.is_locked:
                self.is_locked = locked
                if locked:
                    logger.info("Screen locked - disconnecting Stream Deck")
                    self.disconnect()
                elif not self.shutting_down:
                    logger.info("Screen unlocked - reconnecting Stream Deck")
                    if self.connect():
                        logger.info("Stream Deck reconnected after unlock")

        except Exception as e:
            logger.error(f"Error checking screen lock: {e}")
