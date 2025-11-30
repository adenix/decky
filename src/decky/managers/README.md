# Managers Module

Specialized managers for handling specific aspects of Stream Deck control.

## Overview

The managers module provides a clean separation of concerns for the DeckyController:

- **ConnectionManager**: Device connection lifecycle and monitoring
- **AnimationManager**: GIF animation handling
- **PageManager**: Page rendering and button updates

## Architecture

```
DeckyController (Orchestrator)
    ├── ConnectionManager
    │   ├── Device connection/disconnection
    │   ├── Health monitoring (hot-plug detection)
    │   └── Screen lock integration
    │
    ├── AnimationManager
    │   ├── GIF frame loading
    │   ├── Frame timing and advancement
    │   └── Animation synchronization
    │
    └── PageManager
        ├── Page rendering
        ├── Button rendering
        └── Page navigation
```

## Modules

### ConnectionManager (`connection.py`)

Manages the Stream Deck device connection lifecycle.

**Responsibilities**:

- Connecting to and disconnecting from devices
- Monitoring connection health (detects device unplugging)
- Automatic reconnection when device becomes available
- Screen lock/unlock integration

**Key Methods**:

- `connect()` - Connect to first available Stream Deck
- `disconnect()` - Cleanly disconnect from device
- `start_monitoring()` - Start background connection monitoring
- `stop_monitoring()` - Stop monitoring and cleanup

**Configuration**:

- `RECONNECT_INTERVAL = 2.0` - Seconds between reconnection attempts
- `CONNECTION_CHECK_INTERVAL = 0.5` - Connection health check frequency

### AnimationManager (`animation.py`)

Handles GIF animation playback on buttons.

**Responsibilities**:

- Loading GIF files and extracting frames
- Tracking frame timing for each animated button
- Advancing frames at appropriate intervals
- Synchronizing animations across multiple buttons

**Key Methods**:

- `setup_animated_button()` - Load GIF and set up animation
- `render_current_frame()` - Get current frame for rendering
- `update_animations()` - Advance frames based on timing
- `synchronize_animations()` - Sync all animations to start together

**Configuration**:

- `UPDATE_INTERVAL = 0.05` - Animation update interval (20 FPS)

### PageManager (`page.py`)

Manages page layouts and button rendering.

**Responsibilities**:

- Rendering complete pages with all buttons
- Handling static and animated buttons
- Icon file resolution
- Page navigation

**Key Methods**:

- `switch_page()` - Navigate to different page
- `update_page()` - Render all buttons for current page
- `update_animated_buttons()` - Update animation frames on deck

## Usage Example

```python
from decky.managers import ConnectionManager, AnimationManager, PageManager
from decky.device.manager import DeviceManager
from decky.device.renderer import ButtonRenderer

# Initialize components
device_manager = DeviceManager()
button_renderer = ButtonRenderer()

# Create managers
animation_manager = AnimationManager(button_renderer)
connection_manager = ConnectionManager(
    device_manager=device_manager,
    on_connected=lambda deck: print(f"Connected to {deck.deck_type()}"),
    on_disconnected=lambda: print("Disconnected"),
)
page_manager = PageManager(button_renderer, animation_manager)

# Connect to device
if connection_manager.connect():
    # Render page
    page_manager.update_page(connection_manager.deck, config)

    # Start monitoring
    connection_manager.start_monitoring()
```

## Benefits of This Design

1. **Separation of Concerns**: Each manager has a single, well-defined responsibility
1. **Easier Testing**: Can test each manager independently
1. **Better Maintainability**: Smaller, focused classes are easier to understand
1. **Reusability**: Managers can be reused in different contexts
1. **Clearer Dependencies**: Explicit dependencies through constructor injection

## Backwards Compatibility

The refactored `DeckyController` maintains full backwards compatibility:

- All existing tests pass without modification
- Public API remains unchanged
- Property accessors provide access to manager state
- Configuration format unchanged

## Performance Impact

**Negligible**: The refactoring adds minimal overhead (one extra function call layer).

**Benefits**:

- More maintainable code
- Easier to optimize individual managers
- Better separation makes profiling easier
