# Test Suite

Comprehensive test coverage for the Decky Stream Deck controller, ensuring reliability and maintainability.

## Test Structure

```
tests/
├── unit/                  # Unit tests for individual components
│   ├── test_actions.py           # Action system tests
│   ├── test_controller_connection.py  # Controller lifecycle tests
│   ├── test_device_manager.py    # Device management tests
│   ├── test_platform.py          # Platform detection tests
│   ├── test_kde_platform.py      # KDE-specific tests
│   ├── test_gif_animation.py     # GIF animation tests
│   └── test_graceful_shutdown.py # Shutdown handling tests
└── integration/          # Integration tests (planned)
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run with Coverage

```bash
pytest tests/ --cov=src/decky --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/unit/test_device_manager.py -v
```

### Run with Verbose Output

```bash
pytest tests/ -v --tb=short
```

## Test Categories

### Device Management (`test_device_manager.py`)

Tests the USB device connection lifecycle:

- Connection establishment
- Disconnection handling (voluntary and involuntary)
- Connection health monitoring
- USB error recovery
- Hot-plug detection

**Key Test Cases:**

- Successful connection to Stream Deck
- Handling no devices available
- Detecting unplugged devices
- Reconnection after disconnection

### Controller Connection (`test_controller_connection.py`)

Integration tests for controller's connection management:

- Initial connection on startup
- Reconnection logic with timing
- Screen lock/unlock behavior
- Graceful shutdown
- Error handling in main loop

**Key Test Cases:**

- Auto-reconnect after device unplug
- No reconnect during screen lock
- Proper cleanup on shutdown
- Connection state transitions

### Action System (`test_actions.py`)

Tests the plugin-based action system:

- Action registration and discovery
- Configuration validation
- Execution success/failure
- Platform compatibility checks

**Key Test Cases:**

- Command execution
- Application launching
- Script running
- Page switching
- Media/volume controls

### Platform Support (`test_platform.py`, `test_kde_platform.py`)

Platform-specific functionality:

- Desktop environment detection
- Application launching methods
- Screen lock detection
- Media player control

**Key Test Cases:**

- KDE detection via environment/process
- Application launch fallback chain
- Screen lock status checking
- Command generation

### Animation Support (`test_gif_animation.py`)

Animated GIF handling:

- Frame loading from GIF files
- Animation advancement and looping
- Multi-button synchronization
- Page switching behavior

**Key Test Cases:**

- Loading multi-frame GIFs
- Frame timing and advancement
- Synchronizing multiple animations
- Cleanup on page change

### Graceful Shutdown (`test_graceful_shutdown.py`)

Shutdown and signal handling:

- SIGTERM/SIGINT handling
- Prevention of reconnection during shutdown
- Proper device disconnection
- Thread cleanup

**Key Test Cases:**

- Shutting_down flag prevents reconnection
- Signal handlers set flags correctly
- Device disconnected on shutdown
- Screen unlock respects shutdown state

## Mocking Strategy

Tests use extensive mocking to avoid hardware dependencies:

### Hardware Mocks

- `StreamDeck`: Mocked USB device interface
- `DeviceManager`: Mocked enumeration and connection

### System Mocks

- `subprocess`: Command execution
- `threading`: Background threads
- `time`: Sleep and timing functions

### File System Mocks

- `os.path.exists`: File existence checks
- `Image.open`: Image loading

## Test Fixtures

Common fixtures in test files:

```python
@pytest.fixture
def controller(self):
    """Create a controller with mocked dependencies."""
    with patch("decky.controller.ConfigLoader"), patch(
        "decky.controller.DeckManager"
    ), patch("decky.controller.ButtonRenderer"):
        controller = DeckyController("/test/config.yaml")
        # Configure for testing
        return controller
```

## Coverage Goals

Target: >80% code coverage

Current coverage areas:

- ✅ Core controller logic
- ✅ Device management
- ✅ Action system
- ✅ Platform detection
- ✅ Configuration loading
- ⚠️ Rendering (partial - visual output hard to test)

## Writing New Tests

### Test Structure Template

```python
class TestFeatureName:
    """Test suite for specific feature."""

    @pytest.fixture
    def setup(self):
        """Setup test dependencies."""
        # Create mocks and test objects
        pass

    def test_successful_operation(self, setup):
        """Test normal successful case."""
        # Arrange
        # Act
        # Assert
        pass

    def test_error_handling(self, setup):
        """Test error conditions."""
        # Arrange error condition
        # Act
        # Assert proper handling
        pass
```

### Best Practices

1. **Isolation**: Each test should be independent
1. **Mocking**: Mock external dependencies
1. **Descriptive Names**: Test names should describe what's being tested
1. **Single Assertion**: Focus on testing one behavior per test
1. **Cleanup**: Use fixtures for setup/teardown

## Continuous Integration

Tests run automatically on:

- Pull requests
- Commits to main branch
- Pre-commit hooks (optional)

CI configuration in `.github/workflows/test.yml` (if using GitHub Actions)

## Known Issues

- Thread timing in tests can be flaky - use mocked time where possible
- Some platform tests require specific desktop environment
- Coverage reporting may miss dynamic imports
