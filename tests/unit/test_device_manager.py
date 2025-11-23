"""
Tests for Stream Deck device connection management.

These tests verify the robustness of USB device connection, disconnection,
and reconnection handling.
"""

from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest

from decky.device.manager import DeviceManager


class TestDeviceManager:
    """Test suite for DeviceManager class."""

    def test_init_creates_stream_deck_manager(self):
        """Test that initialization creates the internal StreamDeckManager."""
        manager = DeviceManager()
        assert hasattr(manager, "_stream_deck_manager")

    @patch("decky.device.manager.StreamDeckManager")
    def test_connect_success(self, mock_sdm_class):
        """Test successful device connection."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.deck_type.return_value = "Stream Deck Original"
        mock_deck.key_count.return_value = 15

        mock_sdm = Mock()
        mock_sdm.enumerate.return_value = [mock_deck]
        mock_sdm_class.return_value = mock_sdm

        # Test connection
        manager = DeviceManager()
        result = manager.connect()

        # Verify behavior
        assert result == mock_deck
        mock_sdm.enumerate.assert_called_once()
        mock_deck.open.assert_called_once()
        mock_deck.reset.assert_called_once()

    @patch("decky.device.manager.StreamDeckManager")
    def test_connect_no_devices(self, mock_sdm_class):
        """Test connection when no devices are available."""
        # Setup mocks
        mock_sdm = Mock()
        mock_sdm.enumerate.return_value = []
        mock_sdm_class.return_value = mock_sdm

        # Test connection
        manager = DeviceManager()
        result = manager.connect()

        # Verify behavior
        assert result is None
        mock_sdm.enumerate.assert_called_once()

    @patch("decky.device.manager.StreamDeckManager")
    def test_connect_handles_usb_error(self, mock_sdm_class):
        """Test that USB errors during connection are handled gracefully."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.open.side_effect = OSError("USB device not accessible")

        mock_sdm = Mock()
        mock_sdm.enumerate.return_value = [mock_deck]
        mock_sdm_class.return_value = mock_sdm

        # Test connection
        manager = DeviceManager()
        result = manager.connect()

        # Verify error handling
        assert result is None
        mock_deck.open.assert_called_once()

    @patch("decky.device.manager.StreamDeckManager")
    def test_connect_reenumerates_each_time(self, mock_sdm_class):
        """Test that connect() re-enumerates devices on each call (for hot-plug support)."""
        # Setup mocks
        mock_deck1 = Mock()
        mock_deck1.deck_type.return_value = "Stream Deck Original"
        mock_deck1.key_count.return_value = 15

        mock_deck2 = Mock()
        mock_deck2.deck_type.return_value = "Stream Deck XL"
        mock_deck2.key_count.return_value = 32

        mock_sdm = Mock()
        # First call returns no devices, second returns deck1, third returns deck2
        mock_sdm.enumerate.side_effect = [[], [mock_deck1], [mock_deck2]]
        mock_sdm_class.return_value = mock_sdm

        # Test multiple connections
        manager = DeviceManager()

        result1 = manager.connect()
        assert result1 is None

        result2 = manager.connect()
        assert result2 == mock_deck1

        result3 = manager.connect()
        assert result3 == mock_deck2

        # Verify enumerate was called each time
        assert mock_sdm.enumerate.call_count == 3

    def test_disconnect_with_valid_deck(self):
        """Test clean disconnection from a valid device."""
        # Setup mock deck
        mock_deck = Mock()

        # Test disconnection
        manager = DeviceManager()
        result = manager.disconnect(mock_deck)

        # Verify behavior
        assert result is True
        mock_deck.reset.assert_called_once()
        mock_deck.close.assert_called_once()

    def test_disconnect_with_none(self):
        """Test that disconnect handles None gracefully."""
        manager = DeviceManager()
        result = manager.disconnect(None)

        # Should return True and not crash
        assert result is True

    def test_disconnect_with_already_disconnected_device(self):
        """Test disconnection when device is already unplugged."""
        # Setup mock deck that throws errors (device unplugged)
        mock_deck = Mock()
        mock_deck.reset.side_effect = Exception("No HID device")
        mock_deck.close.side_effect = Exception("No HID device")

        # Test disconnection
        manager = DeviceManager()
        result = manager.disconnect(mock_deck)

        # Should handle errors gracefully
        assert result is False
        mock_deck.reset.assert_called_once()
        mock_deck.close.assert_called_once()

    def test_disconnect_partial_failure(self):
        """Test disconnection when only reset fails but close works."""
        # Setup mock deck
        mock_deck = Mock()
        mock_deck.reset.side_effect = Exception("Reset failed")
        # close() succeeds

        # Test disconnection
        manager = DeviceManager()
        result = manager.disconnect(mock_deck)

        # Should return False but still attempt close
        assert result is False
        mock_deck.reset.assert_called_once()
        mock_deck.close.assert_called_once()

    def test_is_connected_with_valid_deck(self):
        """Test connection check with a connected device."""
        # Setup mock deck
        mock_deck = Mock()
        mock_deck.is_visual.return_value = True

        # Test connection check
        manager = DeviceManager()
        result = manager.is_connected(mock_deck)

        # Should detect as connected
        assert result is True
        mock_deck.is_visual.assert_called_once()

    def test_is_connected_with_none(self):
        """Test that is_connected handles None gracefully."""
        manager = DeviceManager()
        result = manager.is_connected(None)

        # Should return False for None
        assert result is False

    def test_is_connected_detects_unplugged(self):
        """Test that is_connected detects when device is unplugged."""
        # Setup mock deck that throws USB error
        mock_deck = Mock()
        mock_deck.is_visual.side_effect = OSError("USB device not found")

        # Test connection check
        manager = DeviceManager()
        result = manager.is_connected(mock_deck)

        # Should detect as disconnected
        assert result is False
        mock_deck.is_visual.assert_called_once()

    def test_is_connected_handles_io_errors(self):
        """Test that is_connected handles IOError (another USB disconnect indicator)."""
        # Setup mock deck that throws IOError
        mock_deck = Mock()
        mock_deck.is_visual.side_effect = IOError("Device not responding")

        # Test connection check
        manager = DeviceManager()
        result = manager.is_connected(mock_deck)

        # Should detect as disconnected
        assert result is False
        mock_deck.is_visual.assert_called_once()

    def test_is_connected_handles_unexpected_errors(self):
        """Test that is_connected handles unexpected errors gracefully."""
        # Setup mock deck that throws unexpected error
        mock_deck = Mock()
        mock_deck.is_visual.side_effect = ValueError("Unexpected error")

        # Test connection check
        manager = DeviceManager()
        result = manager.is_connected(mock_deck)

        # Should detect as disconnected for any error
        assert result is False
        mock_deck.is_visual.assert_called_once()


class TestDeviceManagerIntegration:
    """Integration tests for device connection lifecycle."""

    @patch("decky.device.manager.StreamDeckManager")
    def test_connect_disconnect_cycle(self, mock_sdm_class):
        """Test a complete connect and disconnect cycle."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.deck_type.return_value = "Stream Deck Original"
        mock_deck.key_count.return_value = 15
        mock_deck.is_visual.return_value = True

        mock_sdm = Mock()
        mock_sdm.enumerate.return_value = [mock_deck]
        mock_sdm_class.return_value = mock_sdm

        # Test full cycle
        manager = DeviceManager()

        # Connect
        deck = manager.connect()
        assert deck is not None
        assert manager.is_connected(deck) is True

        # Disconnect
        result = manager.disconnect(deck)
        assert result is True

        # Verify calls
        mock_deck.open.assert_called_once()
        mock_deck.reset.assert_called()  # Called during connect and disconnect
        mock_deck.close.assert_called_once()

    @patch("decky.device.manager.StreamDeckManager")
    def test_reconnection_after_unplug(self, mock_sdm_class):
        """Test reconnection scenario after device is unplugged."""
        # Setup mocks
        mock_deck1 = Mock()
        mock_deck1.deck_type.return_value = "Stream Deck Original"
        mock_deck1.key_count.return_value = 15

        mock_deck2 = Mock()
        mock_deck2.deck_type.return_value = "Stream Deck Original"
        mock_deck2.key_count.return_value = 15

        mock_sdm = Mock()
        mock_sdm_class.return_value = mock_sdm

        # Test reconnection scenario
        manager = DeviceManager()

        # Initial connection
        mock_sdm.enumerate.return_value = [mock_deck1]
        mock_deck1.is_visual.return_value = True

        deck1 = manager.connect()
        assert deck1 == mock_deck1
        assert manager.is_connected(deck1) is True

        # Device gets unplugged (is_connected starts failing)
        mock_deck1.is_visual.side_effect = OSError("Device not found")
        assert manager.is_connected(deck1) is False

        # Try to disconnect the unplugged device (should handle errors)
        mock_deck1.reset.side_effect = Exception("No HID device")
        mock_deck1.close.side_effect = Exception("No HID device")
        result = manager.disconnect(deck1)
        assert result is False  # Disconnect not clean due to errors

        # Device is plugged back in (new device object)
        mock_sdm.enumerate.return_value = [mock_deck2]
        deck2 = manager.connect()
        assert deck2 == mock_deck2
        assert deck2 != deck1  # Different device instance after replug

        # New device should work normally
        mock_deck2.is_visual.return_value = True
        assert manager.is_connected(deck2) is True

    @patch("decky.device.manager.StreamDeckManager")
    def test_multiple_connection_attempts_no_device(self, mock_sdm_class):
        """Test multiple connection attempts when no device is available."""
        # Setup mocks
        mock_sdm = Mock()
        mock_sdm.enumerate.return_value = []  # No devices
        mock_sdm_class.return_value = mock_sdm

        # Test multiple attempts
        manager = DeviceManager()

        for _ in range(3):
            result = manager.connect()
            assert result is None

        # Should enumerate each time (for hot-plug detection)
        assert mock_sdm.enumerate.call_count == 3
