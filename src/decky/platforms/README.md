# Platform Integration Layer

This directory provides OS and desktop environment specific integrations, allowing Decky to work seamlessly across different Linux distributions and desktop environments.

## Architecture

Platform support follows a strategy pattern where the appropriate platform implementation is selected at runtime based on the detected environment.

## Components

### `__init__.py` - Platform Detection
Auto-detects the current desktop environment and returns appropriate platform implementation:
- Checks environment variables (`XDG_CURRENT_DESKTOP`, `DESKTOP_SESSION`)
- Falls back to process detection (checking for running DE processes)
- Returns None if no supported platform detected (graceful degradation)

### `base.py` - Platform Interface
Abstract base class defining the platform interface:

```python
class Platform(ABC):
    """Base platform interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform identifier."""
        pass

    @abstractmethod
    def detect(self) -> bool:
        """Check if this platform is active."""
        pass

    @abstractmethod
    def launch_application(self, app_id: str) -> bool:
        """Launch a desktop application."""
        pass

    @abstractmethod
    def is_screen_locked(self) -> bool:
        """Check if screen is locked."""
        pass

    # Optional media/volume control methods
    def get_media_player_command(self, action: str) -> List[str]:
        pass

    def get_volume_command(self, direction: str, amount: int) -> List[str]:
        pass
```

### `kde.py` - KDE/Plasma Platform
Full implementation for KDE Plasma desktop:

**Application Launching:**
1. `gtk-launch` (preferred, works with .desktop files)
2. `gtk-launch` with .desktop extension
3. `kioclient exec` with full .desktop path
4. `xdg-open` with application:// URI
5. Direct command execution (fallback)

**Desktop File Resolution:**
Searches multiple locations:
- `/usr/share/applications/`
- `/usr/local/share/applications/`
- `~/.local/share/applications/`
- `/var/lib/flatpak/exports/share/applications/`
- `/var/lib/snapd/desktop/applications/`

**Screen Lock Detection:**
1. `qdbus6` (KDE 6)
2. `qdbus` (KDE 5)
3. `loginctl show-session` (systemd fallback)

**Media Control:**
Uses `qdbus` to control media players via MPRIS2 interface

**Volume Control:**
Uses `qdbus` to control KDE's audio system

## Adding Platform Support

To add support for a new desktop environment:

1. Create a new file (e.g., `gnome.py`)
2. Import and extend the `Platform` base class
3. Implement all required methods:

```python
from .base import Platform

class GnomePlatform(Platform):
    """GNOME desktop environment support."""

    name = "gnome"

    def detect(self) -> bool:
        """Check if running on GNOME."""
        # Check XDG_CURRENT_DESKTOP
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if 'gnome' in desktop:
            return True

        # Check for gnome-shell process
        try:
            result = subprocess.run(['pgrep', 'gnome-shell'],
                                  capture_output=True)
            return result.returncode == 0
        except:
            return False

    def launch_application(self, app_id: str) -> bool:
        """Launch application using GNOME tools."""
        # Implementation using gio, gtk-launch, etc.
        pass

    def is_screen_locked(self) -> bool:
        """Check GNOME screen lock status."""
        # Use dbus to check screensaver status
        pass
```

4. Update `__init__.py` to include the new platform in detection

## Platform Features Matrix

| Platform | App Launch | Screen Lock | Media Control | Volume Control |
|----------|------------|-------------|---------------|----------------|
| KDE      | ✅         | ✅          | ✅            | ✅             |
| GNOME    | 🔄         | 🔄          | 🔄            | 🔄             |
| XFCE     | 🔄         | 🔄          | 🔄            | 🔄             |

✅ = Implemented
🔄 = Planned
❌ = Not supported

## Error Handling

- All platform methods return boolean success/failure
- Exceptions are caught and logged, not propagated
- Missing tools/commands fail gracefully
- Platform features degrade gracefully if unavailable

## Testing

Platform implementations are tested with mocks:
- `test_platform.py`: Platform detection and interface
- `test_kde_platform.py`: KDE-specific functionality
- Mock subprocess calls to avoid dependency on actual DE

## Dependencies

Platform integrations may require:
- **KDE**: qdbus/qdbus6, kioclient, gtk-launch
- **GNOME**: gio, gdbus, gnome-screensaver-command
- **General**: xdg-open, loginctl (systemd)