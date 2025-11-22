"""
Tests for platform abstraction - ensuring cross-distro compatibility
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from decky.platforms.base import Platform
from decky.platforms.kde import KDEPlatform


class TestKDEPlatform:
    """Test KDE platform implementation"""

    def test_detect_kde_via_environment(self):
        """Test KDE detection via environment variables"""
        platform = KDEPlatform()

        # Test XDG_CURRENT_DESKTOP
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE'}):
            assert platform.detect() is True

        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'plasma'}):
            assert platform.detect() is True

        # Test XDG_SESSION_DESKTOP
        with patch.dict(os.environ, {'XDG_SESSION_DESKTOP': 'kde-plasma'}, clear=True):
            assert platform.detect() is True

    def test_detect_kde_via_process(self):
        """Test KDE detection via running processes"""
        platform = KDEPlatform()

        with patch.dict(os.environ, {}, clear=True):
            with patch('subprocess.run') as mock_run:
                # Simulate plasmashell running
                mock_run.return_value.returncode = 0
                assert platform.detect() is True

                # Simulate plasmashell not running
                mock_run.return_value.returncode = 1
                assert platform.detect() is False

    def test_launch_application_kioclient(self):
        """Test application launching - prefers gtk-launch first"""
        platform = KDEPlatform()

        with patch('subprocess.Popen') as mock_popen:
            result = platform.launch_application('test-app')
            assert result is True
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[0][0]
            # New implementation tries gtk-launch first
            assert 'gtk-launch' in call_args[0]
            assert 'test-app' in call_args

    def test_launch_application_fallback_chain(self):
        """Test fallback chain for application launching"""
        platform = KDEPlatform()

        with patch('subprocess.Popen') as mock_popen:
            # Multiple attempts fail until one succeeds
            # New order: gtk-launch, gtk-launch with .desktop, then others
            mock_popen.side_effect = [
                FileNotFoundError(),  # gtk-launch fails
                FileNotFoundError(),  # gtk-launch with .desktop fails
                Mock()  # fallback succeeds
            ]

            result = platform.launch_application('test-app')
            assert result is True
            assert mock_popen.call_count >= 2  # At least 2 attempts

    def test_screen_lock_detection_qdbus6(self):
        """Test screen lock detection using qdbus6"""
        platform = KDEPlatform()

        with patch('subprocess.run') as mock_run:
            # Simulate locked screen
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'true\n'
            assert platform.is_screen_locked() is True

            # Simulate unlocked screen
            mock_run.return_value.stdout = 'false\n'
            assert platform.is_screen_locked() is False

    def test_screen_lock_detection_fallback_loginctl(self):
        """Test fallback to loginctl for screen lock detection"""
        platform = KDEPlatform()

        with patch('subprocess.run') as mock_run:
            # First attempts fail, loginctl succeeds
            mock_run.side_effect = [
                Exception(),  # qdbus6 fails
                Exception(),  # qdbus fails
                Exception(),  # qdbus screensaver fails
                Mock(returncode=0, stdout='LockedHint=yes')  # loginctl succeeds
            ]

            assert platform.is_screen_locked() is True

    def test_media_commands(self):
        """Test media player command generation"""
        platform = KDEPlatform()

        play_cmd = platform.get_media_player_command('play-pause')
        assert 'PlayPause' in play_cmd
        assert 'org.mpris.MediaPlayer2' in play_cmd

        next_cmd = platform.get_media_player_command('next')
        assert 'Next' in next_cmd

        invalid_cmd = platform.get_media_player_command('invalid')
        assert invalid_cmd is None

    def test_volume_commands(self):
        """Test volume control command generation"""
        platform = KDEPlatform()

        inc_cmd = platform.get_volume_command('increase')
        assert 'pactl' in inc_cmd
        assert '+5%' in inc_cmd

        mute_cmd = platform.get_volume_command('mute')
        assert 'toggle' in mute_cmd

        set_cmd = platform.get_volume_command('set', 50)
        assert '50%' in set_cmd


class TestPlatformCompatibility:
    """Test cross-platform compatibility"""

    def test_platform_interface_consistency(self):
        """Ensure all platforms implement required methods"""
        platform = KDEPlatform()

        # All required methods should be present
        assert hasattr(platform, 'detect')
        assert hasattr(platform, 'launch_application')
        assert hasattr(platform, 'is_screen_locked')
        assert hasattr(platform, 'get_media_player_command')
        assert hasattr(platform, 'get_volume_command')

        # Methods should be callable
        assert callable(platform.detect)
        assert callable(platform.launch_application)
        assert callable(platform.is_screen_locked)

    def test_platform_graceful_failure(self):
        """Test platforms handle failures gracefully"""
        platform = KDEPlatform()

        # Should not raise exceptions on failures
        with patch('subprocess.Popen', side_effect=Exception("Failed")):
            result = platform.launch_application('failing-app')
            assert result is False  # Should return False, not raise

        with patch('subprocess.run', side_effect=Exception("Failed")):
            result = platform.is_screen_locked()
            assert result is False  # Should default to unlocked