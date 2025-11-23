"""
Stream Deck device management.

This module handles the low-level connection lifecycle for Stream Deck devices,
including enumeration, connection, disconnection, and connection monitoring.
"""

import logging
from typing import Any, Optional

from StreamDeck.DeviceManager import DeviceManager as StreamDeckManager

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages Stream Deck device connections.

    This class provides a clean interface for connecting to and monitoring
    Stream Deck devices. It handles USB device enumeration and provides
    robust connection state detection.
    """

    def __init__(self):
        """Initialize the device manager."""
        self._stream_deck_manager = StreamDeckManager()

    def connect(self) -> Optional[Any]:
        """
        Connect to the first available Stream Deck device.

        This method enumerates all connected Stream Deck devices and
        connects to the first one found. Device enumeration is performed
        on each call to support USB hot-plugging.

        Returns:
            StreamDeck object if connection successful, None otherwise.
        """
        try:
            # Re-enumerate devices on each connection attempt to detect
            # newly connected devices (USB hot-plug support)
            available_decks = self._stream_deck_manager.enumerate()

            if not available_decks:
                logger.debug("No Stream Deck devices detected during enumeration")
                return None

            # Connect to the first available device
            deck = available_decks[0]
            deck.open()

            # Reset device to clear any previous state
            deck.reset()

            # Log device information for debugging
            device_info = f"{deck.deck_type()} ({deck.key_count()} keys)"
            logger.info(f"Successfully connected to Stream Deck: {device_info}")

            return deck

        except OSError as e:
            # USB/HID communication errors
            logger.error(f"USB communication error during Stream Deck connection: {e}")
            return None
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error connecting to Stream Deck: {e}")
            return None

    def disconnect(self, deck) -> bool:
        """
        Disconnect from a Stream Deck device.

        Attempts to cleanly disconnect from the device by resetting it
        and closing the connection. Errors during disconnection are
        logged but don't prevent the method from completing.

        Args:
            deck: The Stream Deck device to disconnect from.

        Returns:
            True if disconnection was clean, False if errors occurred.
        """
        if not deck:
            logger.debug("Disconnect called with None deck reference")
            return True

        disconnect_clean = True

        try:
            # Reset device to clear display and state
            deck.reset()
            logger.debug("Stream Deck reset successful")
        except Exception as e:
            # Device may already be disconnected
            logger.debug(f"Could not reset Stream Deck (may be unplugged): {e}")
            disconnect_clean = False

        try:
            # Close the device connection
            deck.close()
            logger.debug("Stream Deck connection closed")
        except Exception as e:
            # Device may already be disconnected
            logger.debug(f"Could not close Stream Deck connection: {e}")
            disconnect_clean = False

        if disconnect_clean:
            logger.info("Stream Deck disconnected cleanly")
        else:
            logger.info("Stream Deck disconnected (device was already unavailable)")

        return disconnect_clean

    def is_connected(self, deck) -> bool:
        """
        Check if a Stream Deck device is still connected and responsive.

        This method attempts to communicate with the device to verify
        it's still connected. This is used for detecting USB disconnection
        events (device unplugged).

        Args:
            deck: The Stream Deck device to check.

        Returns:
            True if device is connected and responsive, False otherwise.
        """
        if not deck:
            return False

        try:
            # Attempt to query device state to verify connection
            # The is_visual() method is lightweight and reliable for this purpose
            _ = deck.is_visual()
            return True

        except (OSError, IOError) as e:
            # USB device has been disconnected
            logger.debug(f"Stream Deck connection lost (USB disconnected): {type(e).__name__}")
            return False
        except Exception as e:
            # Any other error indicates device is not accessible
            logger.debug(f"Stream Deck not responsive: {type(e).__name__}: {e}")
            return False
