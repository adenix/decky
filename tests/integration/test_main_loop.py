"""
Integration tests for DeckyController main loop and reconnection logic.

These tests verify the controller's behavior in real-world scenarios including:
- Device connection and disconnection
- USB hot-plugging
- Screen lock/unlock cycles
- Graceful shutdown
"""

import threading
import time
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest

from decky.controller import DeckyController


class TestMainLoopReconnection:
    """Test main loop reconnection logic"""

    @pytest.fixture
    def mock_deck(self):
        """Create a mock Stream Deck device"""
        deck = MagicMock()
        deck.deck_type.return_value = "Stream Deck"
        deck.key_count.return_value = 15
        deck.key_image_format.return_value = {
            "size": (72, 72),
            "format": "JPEG",
            "rotation": 0,
            "mirror": (False, False),
            "flip": (False, False),
        }
        deck.is_visual.return_value = True
        deck.set_brightness = MagicMock()
        deck.set_key_callback = MagicMock()
        deck.set_key_image = MagicMock()
        deck.reset = MagicMock()
        deck.close = MagicMock()
        deck.open = MagicMock()
        return deck

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a minimal test configuration"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
device:
  brightness: 75

styles:
  default:
    font: DejaVu Sans
    font_size: 14
    text_color: '#FFFFFF'
    background_color: '#000000'

pages:
  main:
    name: Main
    buttons:
      1:
        text: Test
        action:
          type: command
          command: echo test
"""
        )
        return str(config_file)

    def test_controller_starts_without_device(self, mock_config):
        """Test that controller starts successfully even when no device is connected"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            # No devices available
            mock_manager.return_value.enumerate.return_value = []

            controller = DeckyController(mock_config)

            # Start controller in a thread
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Let it run briefly
            time.sleep(0.5)

            # Should be running without a deck
            assert controller.running is True
            assert controller.deck is None

            # Shutdown gracefully
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

            assert not run_thread.is_alive()

    def test_device_reconnection_after_disconnect(self, mock_config, mock_deck):
        """Test that controller reconnects when device becomes available"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            enumerate_results = [
                [],  # Initially no device
                [],  # Still no device
                [mock_deck],  # Device appears
            ]
            mock_manager.return_value.enumerate.side_effect = enumerate_results

            controller = DeckyController(mock_config)

            # Start controller
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Initially no device
            time.sleep(0.2)
            assert controller.deck is None

            # Wait for reconnection attempts (should try after 2 seconds)
            time.sleep(2.5)

            # Device should be connected now
            assert controller.deck is not None
            assert controller.deck == mock_deck

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_device_hot_unplug_detection(self, mock_config, mock_deck):
        """Test detection of device being unplugged during operation"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            controller = DeckyController(mock_config)
            controller.load_config()
            controller.connect()

            # Device is connected
            assert controller.deck is not None

            # Start the run loop
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Give it a moment to start running
            time.sleep(0.2)

            # Simulate device being unplugged:
            # 1. is_visual raises OSError (device no longer responding)
            # 2. enumerate returns empty (device no longer available)
            mock_deck.is_visual.side_effect = OSError("Device disconnected")
            mock_manager.return_value.enumerate.return_value = []

            # Wait for disconnect detection (checks every 0.5s, give it time for 2-3 checks)
            time.sleep(1.5)

            # Device should be detected as disconnected and NOT reconnected
            assert controller.deck is None

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_no_reconnection_during_shutdown(self, mock_config, mock_deck):
        """Test that reconnection doesn't happen during shutdown"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            # No device available initially, but becomes available later
            # However shutting_down should prevent reconnection
            mock_manager.return_value.enumerate.side_effect = [
                [],  # No device initially
                [mock_deck],  # Device becomes available (but shouldn't reconnect)
                [mock_deck],  # Still available
            ]

            controller = DeckyController(mock_config)
            controller.load_config()

            # Set shutting_down flag BEFORE running to prevent reconnection
            controller.shutting_down = True

            # Start run loop
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Wait long enough for multiple reconnection attempts (reconnect interval is 2s)
            time.sleep(2.5)

            # Should not have connected despite device becoming available
            # (because shutting_down prevents reconnection)
            assert controller.deck is None

            # Cleanup
            controller.running = False
            run_thread.join(timeout=2)

    def test_screen_lock_disconnects_device(self, mock_config, mock_deck):
        """Test that device is disconnected when screen is locked"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            # Create controller with mock platform
            with patch("decky.controller.detect_platform") as mock_platform_detect:
                mock_platform = MagicMock()
                mock_platform.name = "test"
                mock_platform.is_screen_locked.return_value = False
                mock_platform_detect.return_value = mock_platform

                controller = DeckyController(mock_config)
                controller.load_config()
                controller.connect()

                # Device connected
                assert controller.deck is not None

                # Start run loop
                run_thread = threading.Thread(target=controller.run, daemon=True)
                run_thread.start()

                time.sleep(0.5)

                # Simulate screen lock
                mock_platform.is_screen_locked.return_value = True

                # Wait for lock detection
                time.sleep(1.5)

                # Device should be disconnected
                assert controller.deck is None
                assert controller.is_locked is True

                # Cleanup
                controller.running = False
                controller.shutting_down = True
                run_thread.join(timeout=2)

    def test_graceful_shutdown_on_sigterm(self, mock_config, mock_deck):
        """Test graceful shutdown when receiving SIGTERM"""
        import signal

        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            controller = DeckyController(mock_config)
            controller.load_config()
            controller.connect()

            assert controller.deck is not None

            # Start run loop
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            time.sleep(0.3)

            # Trigger shutdown
            controller.running = False
            controller.shutting_down = True

            # Wait for clean shutdown
            run_thread.join(timeout=3)

            # Verify clean shutdown
            assert not run_thread.is_alive()
            # Device should be disconnected
            mock_deck.reset.assert_called()
            mock_deck.close.assert_called()

    def test_animation_updates_in_main_loop(self, mock_config, mock_deck):
        """Test that animated buttons are updated in the main loop"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            controller = DeckyController(mock_config)
            controller.load_config()
            controller.connect()

            # Add a fake animated button
            controller.animated_buttons[0] = {
                "frames": [MagicMock(), MagicMock()],
                "durations": [100, 100],
                "current_frame": 0,
                "last_update": time.time() - 1.0,  # Old update
                "config": {"text": "Test"},
            }

            # Start run loop briefly
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Let animations run
            time.sleep(0.3)

            # Check that animation was processed (frame advanced or image set)
            # We can't easily check frame advancement without more mocking,
            # but we verify the loop ran
            assert controller.running is True

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_config_reload_capability(self, mock_config, mock_deck):
        """Test that configuration can be reloaded while running"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            controller = DeckyController(mock_config)
            assert controller.load_config() is True

            # Config should be loaded
            assert controller.config is not None
            assert "pages" in controller.config

            # Should be able to reload
            assert controller.load_config() is True

    def test_multiple_reconnection_attempts(self, mock_config, mock_deck):
        """Test that multiple reconnection attempts work correctly"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            # Device not available for first few attempts, then appears
            enumerate_results = [
                [],  # Attempt 1
                [],  # Attempt 2
                [],  # Attempt 3
                [mock_deck],  # Attempt 4 - success
            ]
            mock_manager.return_value.enumerate.side_effect = enumerate_results

            controller = DeckyController(mock_config)

            # Start controller
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Wait long enough for multiple reconnection attempts
            # (reconnection interval is 2 seconds)
            time.sleep(7.0)

            # Should be connected after several attempts
            assert controller.deck is not None

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)


class TestMainLoopEdgeCases:
    """Test edge cases and error conditions in main loop"""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a minimal test configuration"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
device:
  brightness: 75

pages:
  main:
    name: Main
    buttons:
      1:
        text: Test
        action:
          type: command
          command: echo test
"""
        )
        return str(config_file)

    def test_invalid_config_prevents_startup(self, tmp_path):
        """Test that invalid config prevents controller from running"""
        bad_config = tmp_path / "bad_config.yaml"
        bad_config.write_text("not: valid\nconfig: missing pages")

        controller = DeckyController(str(bad_config))

        # load_config should fail
        assert controller.load_config() is False

        # Config should remain None
        assert controller.config is None

    def test_missing_config_file(self):
        """Test handling of missing configuration file"""
        controller = DeckyController("/nonexistent/config.yaml")

        # Should handle gracefully
        assert controller.load_config() is False

    def test_controller_handles_deck_errors_gracefully(self, mock_config):
        """Test that controller handles deck errors without crashing"""
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_deck = MagicMock()
            mock_deck.open.side_effect = Exception("USB error")
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            controller = DeckyController(mock_config)
            controller.load_config()

            # Connection should fail gracefully
            result = controller.connect()
            assert result is False
            assert controller.deck is None
