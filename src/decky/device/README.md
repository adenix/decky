# Device Management Layer

This directory handles all Stream Deck hardware interactions, including USB communication, button rendering, and device lifecycle management.

## Components

### `manager.py` - Device Manager

Manages Stream Deck hardware connections with robust error handling:

**Key Features:**

- **USB Hot-plug Support**: Automatically detects device connection/disconnection
- **Connection Health Monitoring**: Verifies device is still responsive
- **Graceful Disconnection**: Handles both voluntary and involuntary disconnects
- **Thread-safe Operations**: Safe for concurrent access

**Main Methods:**

- `connect()`: Enumerate and connect to first available Stream Deck
- `disconnect(deck)`: Safely disconnect and clean up resources
- `is_connected(deck)`: Check if device is still connected and responsive

**Error Handling:**

- USB permission errors are logged with helpful instructions
- Device disconnection (unplug) is detected via IOError/OSError
- All exceptions are caught to prevent crashes

### `renderer.py` - Button Renderer

Handles visual rendering of buttons on the Stream Deck:

**Capabilities:**

- **Text Rendering**: Multi-line text with word wrapping
- **Icon Support**: Static images (PNG, JPG) and animated GIFs
- **Style System**: Configurable fonts, colors, and sizes
- **Composite Rendering**: Combines icons and text

**Key Methods:**

- `render_button()`: Main entry point for button rendering
- `render_button_with_icon()`: Renders button with pre-loaded icon image
- `render_blank()`: Creates blank/black button image
- `render_text()`: Handles text rendering with word wrap

**Image Processing:**

- Automatic resizing to match device requirements
- Maintains aspect ratio with padding
- Supports transparency (RGBA)
- Optimized for Stream Deck's specific format

## USB Communication

The device layer uses the `StreamDeck` library for USB HID communication:

1. **Enumeration**: Scans USB bus for Stream Deck devices
1. **Connection**: Opens HID interface to device
1. **Configuration**: Sets brightness, registers callbacks
1. **Communication**: Sends image data, receives button events
1. **Disconnection**: Closes HID interface, releases resources

## Connection Lifecycle

```
Connect Flow:
enumerate_devices() → open_device() → configure() → ready

Disconnect Flow:
detect_disconnect → close_device() → cleanup → reconnect_wait

Hot-plug Flow:
device_unplugged → IOError → is_connected=False → close → wait → enumerate → reconnect
```

## Error Recovery

The device layer implements multiple levels of error recovery:

1. **Connection Failures**: Return None, don't crash
1. **USB Errors**: Log and retry with backoff
1. **Render Errors**: Fall back to text-only display
1. **Disconnection**: Clean up and signal for reconnection

## Thread Safety

- Device manager creates new StreamDeck manager for each connection attempt
- Connection state checks are atomic
- Image updates are thread-safe (handled by StreamDeck library)

## Performance Considerations

- **Image Caching**: Rendered buttons can be cached (not currently implemented)
- **Batch Updates**: Multiple buttons updated in sequence
- **Animation Timing**: GIF frames updated at ~20 FPS (50ms intervals)
- **USB Bandwidth**: Image data compressed by StreamDeck library

## Testing

The device layer is extensively tested with mocks:

- `test_device_manager.py`: Connection lifecycle tests
- `test_controller_connection.py`: Integration with controller
- Mocked StreamDeck devices for CI/CD compatibility

## Hardware Support

Currently supports all Stream Deck models via the `streamdeck` library:

- Stream Deck (Original)
- Stream Deck Mini
- Stream Deck XL
- Stream Deck MK.2

Device-specific parameters (button count, image size) are queried dynamically.
