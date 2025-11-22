"""
Tests for KDE platform implementation.
"""

import pytest
import os
from unittest.mock import Mock, patch, call
from decky.platforms.kde import KDEPlatform


class TestKDEPlatform:
    """Test suite for KDE platform implementation."""

    @pytest.fixture
    def platform(self):
        """Create a KDE platform instance."""
        return KDEPlatform()

    def test_launch_application_with_gtk_launch(self, platform):
        """Test that gtk-launch is tried first for application launching."""
        with patch('subprocess.Popen') as mock_popen:
            # gtk-launch succeeds
            result = platform.launch_application('firefox')

        # Should call gtk-launch
        mock_popen.assert_called_once_with(
            ['gtk-launch', 'firefox'],
            stdout=mock_popen.call_args[1]['stdout'],
            stderr=mock_popen.call_args[1]['stderr']
        )
        assert result is True

    def test_launch_application_fallback_to_desktop_extension(self, platform):
        """Test fallback to .desktop extension if app ID fails."""
        with patch('subprocess.Popen') as mock_popen:
            # First call (gtk-launch without .desktop) fails
            # Second call (gtk-launch with .desktop) succeeds
            mock_popen.side_effect = [
                Exception("Command not found"),
                None  # Success
            ]

            result = platform.launch_application('firefox')

        # Should try both variants
        assert mock_popen.call_count == 2
        calls = mock_popen.call_args_list
        assert calls[0][0][0] == ['gtk-launch', 'firefox']
        assert calls[1][0][0] == ['gtk-launch', 'firefox.desktop']
        assert result is True

    def test_launch_application_with_desktop_file_path(self, platform):
        """Test launching with full .desktop file path."""
        desktop_path = '/usr/share/applications/firefox.desktop'

        with patch('subprocess.Popen') as mock_popen, \
             patch('os.path.exists') as mock_exists:
            # First two gtk-launch attempts fail
            # kioclient with desktop path succeeds
            mock_popen.side_effect = [
                Exception("Not found"),  # gtk-launch firefox
                Exception("Not found"),  # gtk-launch firefox.desktop
                None  # kioclient success
            ]
            mock_exists.return_value = True

            result = platform.launch_application('firefox')

        # Should fall back to kioclient with desktop path
        assert mock_popen.call_count == 3
        last_call = mock_popen.call_args_list[2]
        assert last_call[0][0] == ['kioclient', 'exec', desktop_path]
        assert result is True

    def test_launch_application_checks_multiple_desktop_locations(self, platform):
        """Test that multiple desktop file locations are checked."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('os.path.exists') as mock_exists, \
             patch('os.path.expanduser') as mock_expand:

            mock_expand.side_effect = lambda x: x.replace('~', '/home/user')

            # Only the flatpak location exists
            def exists_check(path):
                return 'flatpak' in path

            mock_exists.side_effect = exists_check

            # First two gtk-launch attempts fail
            mock_popen.side_effect = [
                Exception("Not found"),
                Exception("Not found"),
                None  # kioclient succeeds
            ]

            result = platform.launch_application('org.mozilla.firefox')

        # Verify flatpak path was used
        last_call = mock_popen.call_args_list[2]
        assert 'flatpak' in last_call[0][0][2]
        assert result is True

    def test_launch_application_direct_execution_fallback(self, platform):
        """Test fallback to direct command execution."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('os.path.exists', return_value=False):
            # All methods fail except direct execution
            mock_popen.side_effect = [
                Exception("gtk-launch failed"),  # gtk-launch
                Exception("gtk-launch failed"),  # gtk-launch with .desktop
                # No kioclient calls (no desktop files exist)
                Exception("xdg-open failed"),    # xdg-open with application://
                None  # Direct execution succeeds
            ]

            result = platform.launch_application('code')

        # Should try direct execution as last resort
        last_call = mock_popen.call_args_list[-1]
        assert last_call[0][0] == ['code']
        assert result is True

    def test_launch_application_all_methods_fail(self, platform):
        """Test that False is returned when all launch methods fail."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('os.path.exists', return_value=False):
            # All methods fail
            mock_popen.side_effect = Exception("All methods failed")

            result = platform.launch_application('nonexistent')

        assert result is False

    def test_is_screen_locked_with_qdbus6(self, platform):
        """Test screen lock detection with qdbus6."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = 'true'
            mock_run.return_value = mock_result

            locked = platform.is_screen_locked()

        # Should use qdbus6
        mock_run.assert_called_once()
        assert 'qdbus6' in mock_run.call_args[0][0][0]
        assert locked is True

    def test_is_screen_locked_fallback_to_loginctl(self, platform):
        """Test fallback to loginctl for screen lock detection."""
        with patch('subprocess.run') as mock_run:
            # All qdbus commands fail, loginctl succeeds
            mock_run.side_effect = [
                Exception("qdbus6 not found"),
                Exception("qdbus not found"),
                Exception("qdbus not found"),
                Mock(returncode=0, stdout='LockedHint=yes')
            ]

            locked = platform.is_screen_locked()

        assert mock_run.call_count == 4
        assert 'loginctl' in mock_run.call_args_list[3][0][0][0]
        assert locked is True