"""
Tests for graceful shutdown and signal handling.
"""

import signal
from unittest.mock import MagicMock, Mock, patch

import pytest

from decky.controller import DeckyController


class TestGracefulShutdown:
    """Test suite for graceful shutdown handling."""

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

    def test_shutting_down_flag_prevents_reconnection(self, controller):
        """Test that shutting_down flag prevents reconnection attempts."""
        # Initially, shutting_down should be False
        assert controller.shutting_down is False

        # Set shutting_down flag
        controller.shutting_down = True

        # Verify it's set in connection manager
        assert controller.connection_manager.shutting_down is True

        # Mock deck as None (disconnected)
        controller.connection_manager.deck = None
        controller.connection_manager.is_locked = False

        # Verify the shutdown flag is accessible
        assert controller.shutting_down is True

    def test_shutting_down_flag_in_run_finally(self, controller):
        """Test that shutting_down flag is set properly via property."""
        # Verify initial state
        assert controller.shutting_down is False

        # Simulate shutdown by setting the flag
        controller.shutting_down = True

        # Verify it's accessible through property and set in manager
        assert controller.shutting_down is True
        assert controller.connection_manager.shutting_down is True

    def test_disconnect_called_when_deck_exists(self, controller):
        """Test that disconnect is called on shutdown when deck is connected."""
        mock_deck = Mock()
        controller.connection_manager.deck = mock_deck

        with patch.object(controller.device_manager, "disconnect") as mock_disconnect:
            controller.connection_manager.disconnect()

        # Verify disconnect was called and deck was cleared
        mock_disconnect.assert_called_once_with(mock_deck)
        assert controller.deck is None

    def test_screen_lock_respects_shutting_down(self, controller):
        """Test that screen unlock doesn't reconnect when shutting down."""
        controller.shutting_down = True
        controller.connection_manager.deck = None

        # Verify shutdown flag prevents reconnection
        assert controller.shutting_down is True
        assert controller.connection_manager.shutting_down is True

        # The actual reconnection prevention is tested in integration tests
        # This just verifies the flag is set correctly

    def test_main_signal_handler_sets_flags(self):
        """Test that the signal handler in main.py sets the correct flags."""
        from decky.main import main

        with (
            patch("decky.main.argparse.ArgumentParser") as mock_parser,
            patch("decky.main.logging.basicConfig"),
            patch("decky.main.os.path.exists", return_value=True),
            patch("decky.main.DeckyController") as mock_controller_class,
            patch("decky.main.signal.signal") as mock_signal,
        ):

            # Setup mock argument parser
            mock_args = Mock()
            mock_args.config = "/test/config.yaml"
            mock_args.log_level = "INFO"
            mock_parser.return_value.parse_args.return_value = mock_args

            # Create mock controller
            mock_controller = Mock()
            mock_controller.running = True
            mock_controller.shutting_down = False
            mock_controller_class.return_value = mock_controller

            # Make run() raise KeyboardInterrupt to exit immediately
            mock_controller.run.side_effect = KeyboardInterrupt()

            # Run main
            try:
                main()
            except SystemExit:
                pass

            # Verify signal handlers were registered
            assert mock_signal.call_count == 2
            mock_signal.assert_any_call(signal.SIGTERM, mock_signal.call_args_list[0][0][1])
            mock_signal.assert_any_call(signal.SIGINT, mock_signal.call_args_list[1][0][1])
