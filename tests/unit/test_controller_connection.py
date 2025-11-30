"""
Tests for DeckyController connection management.

Tests the controller's handling of device connection, disconnection,
and reconnection scenarios with the manager-based architecture.
"""

import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from decky.controller import DeckyController


class TestControllerConnection:
    """Test suite for controller connection management."""

    @pytest.fixture
    def controller(self):
        """Create a controller instance with mocked dependencies."""
        with (
            patch("decky.controller.ConfigLoader"),
            patch("decky.controller.DeviceManager"),
            patch("decky.controller.ButtonRenderer"),
            patch("decky.controller.registry"),
            patch("decky.controller.detect_platform"),
        ):
            controller = DeckyController("/test/config.yaml")
            controller.config = {
                "device": {"brightness": 75},
                "styles": {},
                "pages": {"main": {"buttons": {}}},
            }
            return controller

    def test_connect_successful(self, controller):
        """Test successful connection to Stream Deck."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.deck_type.return_value = "Stream Deck"
        mock_deck.key_count.return_value = 15
        controller.device_manager.connect.return_value = mock_deck

        # Test connection
        result = controller.connect()

        # Verify behavior
        assert result is True
        assert controller.deck == mock_deck
        controller.device_manager.connect.assert_called_once()

    def test_connect_no_device(self, controller):
        """Test connection when no device is available."""
        # Setup mocks
        controller.device_manager.connect.return_value = None

        # Test connection
        result = controller.connect()

        # Verify behavior
        assert result is False
        assert controller.deck is None
        controller.device_manager.connect.assert_called_once()

    def test_connect_handles_exception(self, controller):
        """Test that connection exceptions are handled gracefully."""
        # Setup mocks
        controller.device_manager.connect.side_effect = Exception("Connection failed")

        # Test connection
        result = controller.connect()

        # Verify error handling
        assert result is False
        assert controller.deck is None

    def test_setup_deck_configures_device(self, controller):
        """Test that device setup callback properly configures the device."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.key_count.return_value = 15
        mock_deck.key_image_format.return_value = {
            "size": (72, 72),
            "format": "JPEG",
            "rotation": 0,
            "mirror": (False, False),
            "flip": (False, False),
        }
        controller.button_renderer.render_blank.return_value = b"blank"

        # Test setup callback (called when device connects)
        controller._on_device_connected(mock_deck)

        # Verify configuration
        mock_deck.set_brightness.assert_called_once_with(75)
        mock_deck.set_key_callback.assert_called_once()

    def test_setup_deck_with_no_deck(self, controller):
        """Test that device setup callback handles None deck gracefully."""
        # Should not crash when called with None
        controller._on_device_connected(None)

    def test_setup_deck_handles_errors(self, controller):
        """Test that setup errors are handled gracefully."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.set_brightness.side_effect = Exception("Device error")

        # Should not crash even if setup fails
        controller._on_device_connected(mock_deck)

    def test_disconnect_deck_clean(self, controller):
        """Test clean disconnection from Stream Deck."""
        # Setup mocks
        mock_deck = Mock()
        controller.connection_manager.deck = mock_deck
        controller.device_manager.disconnect.return_value = True

        # Test disconnection through connection manager
        controller.connection_manager.disconnect()

        # Verify behavior
        assert controller.deck is None
        controller.device_manager.disconnect.assert_called_once_with(mock_deck)

    def test_disconnect_deck_with_errors(self, controller):
        """Test disconnection when device is already unplugged."""
        # Setup mocks
        mock_deck = Mock()
        controller.connection_manager.deck = mock_deck
        controller.device_manager.disconnect.return_value = False

        # Test disconnection
        controller.connection_manager.disconnect()

        # Should still clear deck reference
        assert controller.deck is None
        controller.device_manager.disconnect.assert_called_once_with(mock_deck)

    def test_disconnect_deck_already_none(self, controller):
        """Test that disconnect handles None deck gracefully."""
        controller.connection_manager.deck = None

        # Should not crash
        controller.connection_manager.disconnect()
        controller.device_manager.disconnect.assert_not_called()


class TestControllerReconnection:
    """Test suite for controller reconnection logic."""

    @pytest.fixture
    def controller(self):
        """Create a controller with mocked components for testing."""
        with (
            patch("decky.controller.ConfigLoader"),
            patch("decky.controller.DeviceManager"),
            patch("decky.controller.ButtonRenderer"),
            patch("decky.controller.registry"),
            patch("decky.controller.detect_platform"),
        ):
            controller = DeckyController("/test/config.yaml")
            controller.config = {
                "device": {"brightness": 100},
                "styles": {},
                "pages": {"main": {"buttons": {}}},
            }
            controller.config_loader.load.return_value = controller.config
            # Mock the screen lock monitoring to prevent thread issues
            controller.platform = None  # Disable screen lock monitoring
            return controller

    def test_reconnection_logic(self, controller):
        """Test that reconnection logic works correctly without running the full loop."""
        # Test that connect() is called and deck is set properly
        mock_deck = Mock()
        mock_deck.deck_type.return_value = "Stream Deck"
        mock_deck.key_count.return_value = 15
        controller.device_manager.connect.return_value = mock_deck

        # Test successful connection
        result = controller.connect()
        assert result is True
        assert controller.deck == mock_deck
        controller.device_manager.connect.assert_called_once()

        # Reset and test failed connection
        controller.device_manager.reset_mock()
        controller.device_manager.connect.return_value = None
        controller.connection_manager.deck = None

        result = controller.connect()
        assert result is False
        assert controller.deck is None

    def test_disconnection_detection(self, controller):
        """Test that disconnection is detected through ConnectionManager."""
        # Setup initial connection
        mock_deck = Mock()
        controller.connection_manager.deck = mock_deck
        controller.device_manager.is_connected.return_value = False

        # Check connection health (this is what the monitor loop does)
        is_connected = controller.connection_manager.is_connected()

        # Verify disconnection is detected
        assert is_connected is False

    def test_connection_state_handling(self, controller):
        """Test proper handling of connection state changes."""
        mock_deck = Mock()

        # Test that is_connected is checked properly
        controller.connection_manager.deck = mock_deck
        controller.device_manager.is_connected.return_value = True

        # Deck should remain connected
        assert controller.deck is not None
        assert controller.connection_manager.is_connected() is True

        # Now simulate disconnection
        controller.device_manager.is_connected.return_value = False

        # Verify disconnection is detected
        assert controller.connection_manager.is_connected() is False

        # Call disconnect and verify deck is cleared
        controller.connection_manager.disconnect()
        assert controller.deck is None
        controller.device_manager.disconnect.assert_called_once_with(mock_deck)

    def test_no_reconnect_when_locked(self, controller):
        """Test that reconnection is not attempted when screen is locked."""
        # Setup - screen is locked
        controller.connection_manager.deck = None
        controller.connection_manager.is_locked = True

        # Verify the is_locked flag is accessible
        assert controller.is_locked is True
        assert controller.deck is None

        # The actual reconnection prevention is tested in integration tests
        # This test just verifies the flag is accessible through the property

        # Now unlock and verify connection would be allowed
        controller.connection_manager.is_locked = False
        # Connection logic is tested in integration tests

    def test_graceful_shutdown(self, controller):
        """Test graceful shutdown flag behavior."""
        # Test shutting_down property accessor
        assert controller.shutting_down is False

        # Set shutting down flag
        controller.shutting_down = True

        # Verify it's set in connection manager
        assert controller.connection_manager.shutting_down is True
        assert controller.shutting_down is True

    def test_unexpected_error_handling(self, controller):
        """Test that connection errors are handled gracefully."""
        # Setup - connection raises unexpected error
        controller.device_manager.connect.side_effect = ValueError("Unexpected error")

        # Should handle error gracefully
        result = controller.connect()

        # Verify error handling
        assert result is False
        assert controller.deck is None
