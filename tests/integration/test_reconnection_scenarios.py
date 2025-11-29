"""
Integration tests for USB hot-plug and reconnection scenarios.

These tests verify the controller correctly handles:
- Device hot-plugging (device connected after startup)
- Device hot-unplugging (device removed during operation)
- Multiple disconnect/reconnect cycles
- Reconnection timing and throttling
"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from decky.controller import DeckyController


class TestUSBHotPlug:
    """Test USB hot-plug scenarios"""

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

    def test_device_plugged_in_after_startup(self, mock_config, mock_deck):
        """
        Test scenario: Decky starts with no device, then device is plugged in.
        Expected: Controller detects and connects to the device.
        """
        call_count = 0

        def enumerate_side_effect():
            nonlocal call_count
            call_count += 1
            # Return empty list for first 2 calls, then return device
            if call_count <= 2:
                return []
            return [mock_deck]

        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.side_effect = enumerate_side_effect

            controller = DeckyController(mock_config)

            # Start without device
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Initially no device
            time.sleep(0.3)
            assert controller.deck is None

            # Wait for reconnection cycle (2 second interval)
            time.sleep(5.0)

            # Device should now be connected
            assert controller.deck is not None
            assert controller.deck == mock_deck

            # Verify device was initialized
            mock_deck.set_brightness.assert_called()
            mock_deck.set_key_callback.assert_called()

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_device_unplugged_during_operation(self, mock_config, mock_deck):
        """
        Test scenario: Device is running normally, then gets unplugged.
        Expected: Controller detects disconnection and cleans up.
        """
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            controller = DeckyController(mock_config)
            controller.load_config()
            controller.connect()

            # Device is connected
            assert controller.deck is not None
            mock_deck.reset.reset_mock()

            # Start running
            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Give it time to start running
            time.sleep(0.3)

            # Simulate device being unplugged:
            # 1. is_visual raises OSError (device no longer responding)
            # 2. enumerate returns empty (device no longer available for reconnection)
            mock_deck.is_visual.side_effect = OSError("Device not found")
            mock_manager.return_value.enumerate.return_value = []

            # Wait for disconnection detection (checks every 0.5s, wait for 2-3 checks)
            time.sleep(1.5)

            # Controller should detect and handle disconnection
            assert controller.deck is None

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_multiple_unplug_replug_cycles(self, mock_config, mock_deck):
        """
        Test scenario: Device is unplugged and re-plugged multiple times.
        Expected: Controller handles each cycle correctly.
        """
        is_connected = [True]  # Mutable container for state
        enumerate_call_count = [0]

        def enumerate_side_effect():
            enumerate_call_count[0] += 1
            # Alternate between connected and disconnected
            if is_connected[0]:
                return [mock_deck]
            return []

        def is_visual_side_effect():
            if not is_connected[0]:
                raise OSError("Device disconnected")
            return True

        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.side_effect = enumerate_side_effect
            mock_deck.is_visual.side_effect = is_visual_side_effect

            controller = DeckyController(mock_config)
            controller.load_config()
            controller.connect()

            # Initially connected
            assert controller.deck is not None

            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            time.sleep(0.5)

            # Cycle 1: Unplug
            is_connected[0] = False
            time.sleep(1.5)
            assert controller.deck is None

            # Cycle 1: Replug
            is_connected[0] = True
            mock_deck.is_visual.side_effect = is_visual_side_effect  # Reset
            time.sleep(2.5)
            assert controller.deck is not None

            # Cycle 2: Unplug again
            is_connected[0] = False
            mock_deck.is_visual.side_effect = is_visual_side_effect  # Reset
            time.sleep(1.5)
            assert controller.deck is None

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_reconnection_throttling(self, mock_config):
        """
        Test that reconnection attempts are throttled to avoid USB spam.
        Expected: Reconnection attempts limited to every 2 seconds.
        """
        enumerate_count = [0]

        def count_enumerate():
            enumerate_count[0] += 1
            return []  # No device available

        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.side_effect = count_enumerate

            controller = DeckyController(mock_config)

            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Run for 5 seconds
            time.sleep(5.0)

            # Should have attempted reconnection ~2-3 times (every 2 seconds)
            # Allow some variance for timing
            assert 1 <= enumerate_count[0] <= 4

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)


class TestReconnectionWithScreenLock:
    """Test reconnection behavior with screen locking"""

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
        return deck

    def test_no_reconnection_while_screen_locked(self, mock_config, mock_deck):
        """
        Test scenario: Screen is locked, device becomes available.
        Expected: Controller does NOT reconnect while locked.
        """
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            with patch("decky.controller.detect_platform") as mock_platform_detect:
                mock_platform = MagicMock()
                mock_platform.name = "test"
                mock_platform.is_screen_locked.return_value = True  # Locked!
                mock_platform_detect.return_value = mock_platform

                controller = DeckyController(mock_config)

                run_thread = threading.Thread(target=controller.run, daemon=True)
                run_thread.start()

                # Wait for lock detection
                time.sleep(2.0)

                # Should NOT connect while locked
                assert controller.deck is None
                assert controller.is_locked is True

                # Cleanup
                controller.running = False
                controller.shutting_down = True
                run_thread.join(timeout=2)

    def test_reconnection_after_unlock(self, mock_config, mock_deck):
        """
        Test scenario: Screen locked, then unlocked.
        Expected: Controller reconnects after unlock.
        """
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            with patch("decky.controller.detect_platform") as mock_platform_detect:
                mock_platform = MagicMock()
                mock_platform.name = "test"
                is_locked = [True]  # Mutable container

                def check_lock():
                    return is_locked[0]

                mock_platform.is_screen_locked.side_effect = check_lock
                mock_platform_detect.return_value = mock_platform

                controller = DeckyController(mock_config)

                run_thread = threading.Thread(target=controller.run, daemon=True)
                run_thread.start()

                # Initially locked
                time.sleep(1.5)
                assert controller.is_locked is True
                assert controller.deck is None

                # Unlock screen
                is_locked[0] = False

                # Wait for unlock detection and reconnection
                time.sleep(2.0)

                # Should reconnect after unlock
                assert controller.is_locked is False
                assert controller.deck is not None

                # Cleanup
                controller.running = False
                controller.shutting_down = True
                run_thread.join(timeout=2)

    def test_lock_unlock_multiple_cycles(self, mock_config, mock_deck):
        """
        Test scenario: Multiple lock/unlock cycles.
        Expected: Controller disconnects on lock, reconnects on unlock.
        """
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.return_value = [mock_deck]

            with patch("decky.controller.detect_platform") as mock_platform_detect:
                mock_platform = MagicMock()
                mock_platform.name = "test"
                is_locked = [False]

                def check_lock():
                    return is_locked[0]

                mock_platform.is_screen_locked.side_effect = check_lock
                mock_platform_detect.return_value = mock_platform

                controller = DeckyController(mock_config)
                controller.load_config()

                run_thread = threading.Thread(target=controller.run, daemon=True)
                run_thread.start()

                # Start unlocked - should connect
                time.sleep(1.0)
                assert controller.deck is not None

                # Lock screen
                is_locked[0] = True
                time.sleep(1.5)
                assert controller.deck is None

                # Unlock
                is_locked[0] = False
                time.sleep(2.0)
                assert controller.deck is not None

                # Lock again
                is_locked[0] = True
                time.sleep(1.5)
                assert controller.deck is None

                # Cleanup
                controller.running = False
                controller.shutting_down = True
                run_thread.join(timeout=2)


class TestReconnectionErrorHandling:
    """Test error handling during reconnection"""

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

    def test_handles_intermittent_usb_errors(self, mock_config):
        """
        Test scenario: USB enumeration occasionally fails.
        Expected: Controller retries and eventually succeeds.
        """
        call_count = [0]

        def failing_enumerate():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise OSError("USB error")

            # Success on 3rd try
            deck = MagicMock()
            deck.deck_type.return_value = "Stream Deck"
            deck.key_count.return_value = 15
            deck.key_image_format.return_value = {
                "size": (72, 72),
                "format": "JPEG",
                "rotation": 0,
                "mirror": (False, False),
            }
            deck.is_visual.return_value = True
            deck.set_brightness = MagicMock()
            deck.set_key_callback = MagicMock()
            deck.set_key_image = MagicMock()
            return [deck]

        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            mock_manager.return_value.enumerate.side_effect = failing_enumerate

            controller = DeckyController(mock_config)

            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Wait for retries
            time.sleep(6.0)

            # Should eventually succeed
            assert controller.deck is not None

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)

    def test_continues_running_despite_device_errors(self, mock_config):
        """
        Test scenario: Device repeatedly fails to connect.
        Expected: Controller keeps running and retrying.
        """
        with patch("decky.device.manager.StreamDeckManager") as mock_manager:
            # Always fail
            mock_manager.return_value.enumerate.return_value = []

            controller = DeckyController(mock_config)

            run_thread = threading.Thread(target=controller.run, daemon=True)
            run_thread.start()

            # Let it retry several times
            time.sleep(5.0)

            # Should still be running
            assert controller.running is True
            assert run_thread.is_alive()

            # Cleanup
            controller.running = False
            controller.shutting_down = True
            run_thread.join(timeout=2)
