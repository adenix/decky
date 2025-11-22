# Actions Plugin System

This directory implements the plugin-based action system for Stream Deck button presses. Each action type defines what happens when a button is pressed.

## Architecture

The action system follows a self-registering plugin pattern where each action class automatically registers itself with the central registry when imported.

## Core Components

### `base.py` - Base Classes
- **`Action`**: Abstract base class that all actions inherit from
- **`ActionContext`**: Context object passed to actions containing:
  - Reference to the controller
  - Button configuration
  - Key index

### `registry.py` - Action Registry
Central registry that manages all available actions:
- Auto-discovers action classes via `__init_subclass__`
- Maintains mapping of action types to implementations
- Validates platform support

### Built-in Actions

#### `command.py` - Command Action
Executes shell commands:
```yaml
action:
  type: command
  command: "notify-send 'Hello World'"
```

#### `application.py` - Application Action
Launches desktop applications with platform-specific support:
```yaml
action:
  type: application
  app: firefox  # or firefox.desktop, or /usr/bin/firefox
```

#### `script.py` - Script Action
Runs executable scripts from `~/.decky/scripts/`:
```yaml
action:
  type: script
  script: my-automation.sh
  args: ["arg1", "arg2"]
```

#### `page.py` - Page Action
Switches between Stream Deck pages:
```yaml
action:
  type: page
  page: settings  # name of target page
```

#### `media.py` - Media Control Action
Controls media playback (play/pause, next, previous):
```yaml
action:
  type: media
  control: play_pause  # or next, previous
```

#### `volume.py` - Volume Control Action
Adjusts system volume:
```yaml
action:
  type: volume
  direction: up    # or down, mute
  amount: 5        # percentage (optional)
```

## Creating Custom Actions

To create a new action type:

1. Create a new file in this directory
2. Import and extend the `Action` base class
3. Implement required methods:

```python
from .base import Action, ActionContext
from typing import Dict, Any

class MyCustomAction(Action):
    """Description of what this action does."""

    action_type = "my_custom"  # Unique identifier

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """Execute the action.

        Args:
            context: Action context with controller reference
            config: Action configuration from YAML

        Returns:
            True if successful, False otherwise
        """
        # Your implementation here
        return True

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate action configuration.

        Args:
            config: Action configuration to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required parameters
        return "required_param" in config
```

4. The action will auto-register and be available immediately

## Platform Support

Actions can specify platform requirements:

```python
class PlatformSpecificAction(Action):
    supported_platforms = ["kde", "gnome"]  # Only works on these platforms
```

The registry checks platform compatibility before executing actions.

## Error Handling

- Actions should return `False` on failure (not raise exceptions)
- Exceptions are caught by the controller and logged
- Actions should validate their config before execution
- Missing required parameters should be handled gracefully

## Testing

Each action should have corresponding tests in `tests/unit/test_actions.py` that verify:
- Configuration validation
- Successful execution
- Failure handling
- Platform compatibility