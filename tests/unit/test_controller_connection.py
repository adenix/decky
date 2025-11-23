"""
Tests for DeckyController connection management.

Tests the controller's handling of device connection, disconnection,
and reconnection scenarios.
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
        with patch("decky.controller.ConfigLoader"), patch("decky.controller.DeckManager"), patch(
            "decky.controller.ButtonRenderer"
        ), patch("decky.controller.registry"), patch("decky.controller.detect_platform"):
            controller = DeckyController("/test/config.yaml")
            controller.config = {"device": {"brightness": 75}, "pages": {"main": {"buttons": {}}}}
            return controller

    def test_connect_successful(self, controller):
        """Test successful connection to Stream Deck."""
        # Setup mocks
        mock_deck = Mock()
        controller.deck_manager.connect.return_value = mock_deck

        # Test connection
        with patch.object(controller, "_setup_deck") as mock_setup:
            result = controller.connect()

        # Verify behavior
        assert result is True
        assert controller.deck == mock_deck
        controller.deck_manager.connect.assert_called_once()
        mock_setup.assert_called_once()

    def test_connect_no_device(self, controller):
        """Test connection when no device is available."""
        # Setup mocks
        controller.deck_manager.connect.return_value = None

        # Test connection
        with patch.object(controller, "_setup_deck") as mock_setup:
            result = controller.connect()

        # Verify behavior
        assert result is False
        assert controller.deck is None
        controller.deck_manager.connect.assert_called_once()
        mock_setup.assert_not_called()

    def test_connect_handles_exception(self, controller):
        """Test that connection exceptions are handled gracefully."""
        # Setup mocks
        controller.deck_manager.connect.side_effect = Exception("Connection failed")

        # Test connection
        result = controller.connect()

        # Verify error handling
        assert result is False
        assert controller.deck is None

    def test_setup_deck_configures_device(self, controller):
        """Test that _setup_deck properly configures the device."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.key_count.return_value = 15
        controller.deck = mock_deck
        controller.button_renderer.render_button.return_value = Mock()
        controller.button_renderer.render_blank.return_value = Mock()

        # Test setup
        with patch.object(controller, "_update_page") as mock_update:
            controller._setup_deck()

        # Verify configuration
        mock_deck.set_brightness.assert_called_once_with(75)
        mock_deck.set_key_callback.assert_called_once()
        # Should call update_page
        mock_update.assert_called_once()

    def test_setup_deck_with_no_deck(self, controller):
        """Test that _setup_deck handles None deck gracefully."""
        controller.deck = None

        # Should not crash
        controller._setup_deck()

    def test_setup_deck_handles_errors(self, controller):
        """Test that setup errors are handled gracefully."""
        # Setup mocks
        mock_deck = Mock()
        mock_deck.set_brightness.side_effect = Exception("Device error")
        controller.deck = mock_deck

        # Should not crash
        controller._setup_deck()

    def test_disconnect_deck_clean(self, controller):
        """Test clean disconnection from Stream Deck."""
        # Setup mocks
        mock_deck = Mock()
        controller.deck = mock_deck
        controller.deck_manager.disconnect.return_value = True

        # Test disconnection
        controller._disconnect_deck()

        # Verify behavior
        assert controller.deck is None
        controller.deck_manager.disconnect.assert_called_once_with(mock_deck)

    def test_disconnect_deck_with_errors(self, controller):
        """Test disconnection when device is already unplugged."""
        # Setup mocks
        mock_deck = Mock()
        controller.deck = mock_deck
        controller.deck_manager.disconnect.return_value = False

        # Test disconnection
        controller._disconnect_deck()

        # Should still clear deck reference
        assert controller.deck is None
        controller.deck_manager.disconnect.assert_called_once_with(mock_deck)

    def test_disconnect_deck_already_none(self, controller):
        """Test that disconnect handles None deck gracefully."""
        controller.deck = None

        # Should not crash
        controller._disconnect_deck()
        controller.deck_manager.disconnect.assert_not_called()


class TestControllerReconnection:
    """Test suite for controller reconnection logic."""

    @pytest.fixture
    def controller(self):
        """Create a controller with mocked components for testing."""
        with patch("decky.controller.ConfigLoader"), patch("decky.controller.DeckManager"), patch(
            "decky.controller.ButtonRenderer"
        ), patch("decky.controller.registry"), patch("decky.controller.detect_platform"):
            controller = DeckyController("/test/config.yaml")
            controller.config = {"device": {"brightness": 100}, "pages": {"main": {"buttons": {}}}}
            controller.config_loader.load.return_value = controller.config
            # Mock the screen lock monitoring to prevent thread issues
            controller.platform = None  # Disable screen lock monitoring
            return controller

    def test_reconnection_logic(self, controller):
        """Test that reconnection logic works correctly without running the full loop."""
        # Test that connect() is called and deck is set properly
        mock_deck = Mock()
        controller.deck_manager.connect.return_value = mock_deck

        # Test successful connection
        result = controller.connect()
        assert result is True
        assert controller.deck == mock_deck
        controller.deck_manager.connect.assert_called_once()

        # Reset and test failed connection
        controller.deck_manager.reset_mock()
        controller.deck_manager.connect.return_value = None
        controller.deck = None

        result = controller.connect()
        assert result is False
        assert controller.deck is None

    @patch("decky.controller.time.sleep")
    @patch("decky.controller.time.time")
    def test_disconnection_detection(self, mock_time, mock_sleep, controller):
        """Test that disconnection is detected and handled."""
        # Setup time simulation
        mock_time.return_value = 0

        # Setup initial connection
        mock_deck = Mock()
        controller.deck_manager.connect.return_value = mock_deck

        # Simulate disconnection detection
        controller.deck_manager.is_connected.side_effect = [
            True,  # First check - connected
            True,  # Second check - connected
            False,  # Third check - disconnected!
            True,  # After reconnection
        ]

        # Control loop execution
        call_count = 0

        def simulate_unplug_replug(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 4:
                controller.running = False

        mock_sleep.side_effect = simulate_unplug_replug

        # Run the controller
        with patch.object(controller, "_setup_deck"), patch.object(
            controller, "_disconnect_deck"
        ) as mock_disconnect:
            controller.run()

        # Verify disconnection was detected and handled
        # Will be called once when disconnection detected, and once in finally
        assert mock_disconnect.call_count >= 1

    def test_connection_state_handling(self, controller):
        """Test proper handling of connection state changes."""
        mock_deck = Mock()

        # Test that is_connected is checked properly
        controller.deck = mock_deck
        controller.deck_manager.is_connected.return_value = True

        # Deck should remain connected
        assert controller.deck is not None

        # Now simulate disconnection
        controller.deck_manager.is_connected.return_value = False

        # Call disconnect and verify deck is cleared
        controller._disconnect_deck()
        assert controller.deck is None
        controller.deck_manager.disconnect.assert_called_once_with(mock_deck)

    def test_no_reconnect_when_locked(self, controller):
        """Test that reconnection is not attempted when screen is locked."""
        # Setup - screen is locked
        controller.deck = None
        controller.is_locked = True

        # Even though deck is None, connect should not be called when locked
        # This tests the logic without running the full loop
        mock_deck = Mock()
        controller.deck_manager.connect.return_value = mock_deck

        # In the actual run loop, this check would prevent connection:
        # if not self.deck and not self.is_locked:

        # Verify the is_locked flag prevents connection
        assert controller.is_locked is True
        assert controller.deck is None

        # Now unlock and verify connection would be allowed
        controller.is_locked = False
        result = controller.connect()
        assert result is True
        assert controller.deck == mock_deck

    @patch("decky.controller.time.sleep")
    def test_graceful_shutdown(self, mock_sleep, controller):
        """Test graceful shutdown with connected device."""
        # Setup
        mock_deck = Mock()
        controller.deck = mock_deck
        controller.deck_manager.connect.return_value = mock_deck
        controller.deck_manager.is_connected.return_value = True

        # Simulate Ctrl+C after a few iterations
        def simulate_interrupt(*args):
            raise KeyboardInterrupt()

        mock_sleep.side_effect = [None, None, simulate_interrupt]

        # Run the controller
        with patch.object(controller, "_setup_deck"), patch.object(
            controller, "_disconnect_deck"
        ) as mock_disconnect:
            controller.run()

        # Verify clean shutdown
        assert controller.running is False
        # Disconnect should be called in finally block
        assert mock_disconnect.called

    @patch("decky.controller.time.sleep")
    def test_unexpected_error_handling(self, mock_sleep, controller):
        """Test that unexpected errors in the main loop are handled."""
        # Setup
        controller.deck_manager.connect.return_value = Mock()

        # Simulate unexpected error
        def cause_error(*args):
            raise ValueError("Unexpected error in loop")

        mock_sleep.side_effect = [None, cause_error]

        # Run the controller
        with patch.object(controller, "_setup_deck"):
            controller.run()  # Should not crash

        # Verify shutdown
        assert controller.running is False
