# Configuration Management

This directory handles loading and validation of YAML configuration files that define Stream Deck layouts, buttons, and behaviors.

## Components

### `loader.py` - Configuration Loader

Loads and validates YAML configuration files:

**Key Features:**

- YAML parsing with error handling
- Schema validation
- Default value injection
- Environment variable expansion
- Configuration merging

## Configuration Structure

Decky uses YAML files with the following structure:

```yaml
# Device settings
device:
  brightness: 75  # 0-100

# Global style definitions
styles:
  default:
    font: "DejaVu Sans"
    font_size: 14
    text_color: "#FFFFFF"
    bg_color: "#000000"

  title:
    font_size: 16
    text_color: "#00FF00"

# Page definitions
pages:
  main:
    buttons:
      1:  # Button position (1-based)
        text: "Firefox"
        icon: "firefox.png"
        style: "default"
        action:
          type: application
          app: firefox

      2:
        text: "Terminal"
        icon: "terminal.png"
        action:
          type: command
          command: "gnome-terminal"

      # Row 2
      6:
        text: "Settings"
        icon: "settings.png"
        action:
          type: page
          page: settings

  settings:
    buttons:
      1:
        text: "Back"
        icon: "back.png"
        action:
          type: page
          page: main

      2:
        text: "Volume Up"
        icon: "volume-up.png"
        action:
          type: volume
          direction: up
          amount: 5
```

## Configuration Elements

### Device Configuration

```yaml
device:
  brightness: 75      # Screen brightness (0-100)
  rotation: 0        # Screen rotation (0, 90, 180, 270)
  screensaver: 300   # Screensaver timeout in seconds
```

### Style System

Styles cascade and merge:

1. Built-in defaults
1. Global style definitions
1. Button-specific overrides

```yaml
styles:
  custom_style:
    font: "Ubuntu"           # Font family
    font_size: 14           # Font size in points
    text_color: "#FFFFFF"   # Text color (hex or name)
    bg_color: "#000000"     # Background color
    text_align: "center"    # left, center, right
    vertical_align: "middle" # top, middle, bottom
    padding: 5              # Padding in pixels
```

### Button Configuration

```yaml
buttons:
  1:  # Position on Stream Deck (1-based)
    text: "Label"           # Button text (supports multiline)
    icon: "icon.png"        # Icon path (relative or absolute)
    style: "style_name"     # Reference to style definition
    action:                 # Action configuration
      type: "action_type"
      # Action-specific parameters
```

### Page System

Pages allow multiple layouts:

- Each page has its own button configuration
- Pages can link to each other via page actions
- Main page is shown on startup

## Path Resolution

Icon paths are resolved in the following order:

1. Absolute paths (starting with `/`)
1. Relative to `~/.decky/icons/`
1. Relative to config file directory

## Environment Variables

Configuration supports environment variable expansion:

```yaml
action:
  type: command
  command: "${HOME}/scripts/my-script.sh"
```

## Validation

The loader performs validation:

- Required fields are present
- Action types are valid
- Referenced pages exist
- Button numbers are within device range

## Error Handling

Configuration errors are handled gracefully:

- Syntax errors show line number and context
- Missing files return None (controller won't start)
- Invalid values use defaults where possible
- Validation errors are logged with details

## Best Practices

1. **Organize by Function**: Group related buttons on the same page
1. **Use Styles**: Define reusable styles for consistency
1. **Icon Naming**: Use descriptive icon filenames
1. **Page Navigation**: Always provide a way back to main page
1. **Comments**: Document complex configurations

## Examples

See the `examples/` directory in the repository root for:

- `basic.yaml`: Minimal working configuration
- `kde.yaml`: Full KDE desktop integration
- `development.yaml`: Developer tools setup
- `media.yaml`: Media control focus
