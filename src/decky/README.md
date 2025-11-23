# Decky Core Module

This directory contains the core implementation of the Decky Stream Deck controller for Linux, organized in a modular architecture.

## Architecture Overview

Decky follows a clean, modular architecture with clear separation of concerns:

```
decky/
├── controller.py      # Main orchestrator
├── main.py           # Entry point & signal handling
├── actions/          # Plugin system for button actions
├── config/           # Configuration management
├── device/           # Stream Deck hardware interface
└── platforms/        # OS-specific integrations
```

## Core Components

### Controller (`controller.py`)

The main orchestrator that coordinates all components:

- Manages Stream Deck connection lifecycle
- Handles button press events and page navigation
- Coordinates animated GIF rendering
- Monitors screen lock status
- Implements graceful shutdown with signal handling

Key features:

- **Hot-plug support**: Automatically reconnects when device is plugged/unplugged
- **Animation support**: Handles multi-frame GIF animations with synchronization
- **Screen lock awareness**: Disconnects on lock, reconnects on unlock
- **Graceful shutdown**: Properly disconnects device on service stop

### Entry Point (`main.py`)

Application entry point with:

- Command-line argument parsing
- Logging configuration
- Signal handlers for SIGTERM and SIGINT
- Clean shutdown orchestration

## Module Interaction

```
main.py
    ↓
controller.py ←→ config/loader.py
    ↓               ↓
device/manager.py   actions/registry.py
    ↓                   ↓
StreamDeck HW      action plugins

platforms/kde.py (or other platforms)
    ↑
controller.py (for screen lock & app launching)
```

## Key Design Patterns

1. **Plugin Architecture**: Actions are self-registering plugins
1. **Factory Pattern**: Platform detection and instantiation
1. **Observer Pattern**: Button press callbacks
1. **Singleton-like**: One controller instance manages the device

## Thread Safety

The controller uses threading for:

- Screen lock monitoring (background thread)
- Animation updates (main loop with timing)

Critical sections are protected, and the `shutting_down` flag prevents race conditions during shutdown.

## Error Handling

- USB disconnection is handled gracefully with automatic reconnection
- Configuration errors are logged but don't crash the application
- Action failures are isolated and logged
- Platform-specific features degrade gracefully if unavailable
