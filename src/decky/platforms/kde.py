"""
KDE Plasma specific platform implementation
"""

import os
import subprocess
import logging
from typing import Optional
from .base import Platform

logger = logging.getLogger(__name__)


class KDEPlatform(Platform):
    """KDE Plasma desktop environment support"""

    name = "kde"
    desktop_environment = "plasma"

    def detect(self) -> bool:
        """Detect if running KDE Plasma"""
        # Check XDG_CURRENT_DESKTOP
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if 'kde' in desktop or 'plasma' in desktop:
            return True

        # Check for KDE session
        session = os.environ.get('XDG_SESSION_DESKTOP', '').lower()
        if 'kde' in session or 'plasma' in session:
            return True

        # Check if plasmashell is running
        try:
            result = subprocess.run(
                ['pgrep', '-x', 'plasmashell'],
                capture_output=True
            )
            return result.returncode == 0
        except:
            pass

        return False

    def launch_application(self, app_id: str) -> bool:
        """Launch application using KDE tools"""
        # Try gtk-launch first (works for desktop application IDs)
        try:
            subprocess.Popen(
                ['gtk-launch', app_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug(f"Launched {app_id} via gtk-launch")
            return True
        except Exception as e:
            logger.debug(f"gtk-launch failed for {app_id}: {e}")
            pass  # Try next method

        # Try with .desktop extension
        try:
            subprocess.Popen(
                ['gtk-launch', f'{app_id}.desktop'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug(f"Launched {app_id}.desktop via gtk-launch")
            return True
        except Exception as e:
            logger.debug(f"gtk-launch with .desktop failed for {app_id}: {e}")
            pass  # Try next method

        # Try kioclient with full .desktop path
        desktop_paths = [
            f'/usr/share/applications/{app_id}.desktop',
            f'/usr/local/share/applications/{app_id}.desktop',
            os.path.expanduser(f'~/.local/share/applications/{app_id}.desktop'),
            # Flatpak applications
            f'/var/lib/flatpak/exports/share/applications/{app_id}.desktop',
            os.path.expanduser(f'~/.local/share/flatpak/exports/share/applications/{app_id}.desktop')
        ]

        for desktop_path in desktop_paths:
            if os.path.exists(desktop_path):
                try:
                    subprocess.Popen(
                        ['kioclient', 'exec', desktop_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    logger.debug(f"Launched {app_id} via kioclient with {desktop_path}")
                    return True
                except Exception as e:
                    logger.debug(f"kioclient failed for {desktop_path}: {e}")
                    continue

        # Fallback to xdg-open with .desktop extension
        try:
            subprocess.Popen(
                ['xdg-open', f'application://{app_id}.desktop'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug(f"Launched {app_id} via xdg-open with application:// URL")
            return True
        except Exception as e:
            logger.debug(f"xdg-open with application:// failed for {app_id}: {e}")
            pass

        # Last resort - try direct execution if it's a command name
        try:
            subprocess.Popen(
                [app_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.debug(f"Launched {app_id} directly as command")
            return True
        except Exception as e:
            logger.debug(f"Direct execution failed for {app_id}: {e}")
            pass

        # All launch methods failed
        logger.error(f"Failed to launch {app_id}: all methods failed")
        return False

    def is_screen_locked(self) -> bool:
        """Check if screen is locked using KDE methods"""
        # Try qdbus6 first (KDE 6)
        commands = [
            ['qdbus6', 'org.freedesktop.ScreenSaver', '/ScreenSaver', 'GetActive'],
            ['qdbus', 'org.freedesktop.ScreenSaver', '/ScreenSaver', 'GetActive'],
            ['qdbus', 'org.kde.screensaver', '/ScreenSaver', 'GetActive']
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    return result.stdout.strip().lower() == 'true'
            except:
                continue

        # Fallback to loginctl
        try:
            result = subprocess.run(
                ['loginctl', 'show-session', '-p', 'LockedHint'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and 'LockedHint=yes' in result.stdout:
                return True
        except:
            pass

        return False

    def get_media_player_command(self, action: str) -> Optional[str]:
        """Get KDE media player control commands"""
        commands = {
            'play-pause': 'qdbus org.mpris.MediaPlayer2.* /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause',
            'next': 'qdbus org.mpris.MediaPlayer2.* /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next',
            'previous': 'qdbus org.mpris.MediaPlayer2.* /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous',
            'stop': 'qdbus org.mpris.MediaPlayer2.* /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Stop'
        }
        return commands.get(action)

    def get_volume_command(self, action: str, value: Optional[int] = None) -> Optional[str]:
        """Get KDE volume control commands"""
        # Using pactl which works across most Linux systems
        commands = {
            'increase': 'pactl set-sink-volume @DEFAULT_SINK@ +5%',
            'decrease': 'pactl set-sink-volume @DEFAULT_SINK@ -5%',
            'mute': 'pactl set-sink-mute @DEFAULT_SINK@ toggle'
        }

        if action == 'set' and value is not None:
            return f'pactl set-sink-volume @DEFAULT_SINK@ {value}%'

        return commands.get(action)