# Decky - Simple YAML-Driven Stream Deck for Linux

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
- Python 3.7+
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

### Service Management with deckyctl

When installed as a service, use `deckyctl` to manage Decky:

```bash
# Control commands
deckyctl start          # Start the service
deckyctl stop           # Stop the service
deckyctl restart        # Restart the service
deckyctl status         # Check service status
deckyctl logs           # View live logs

# Configuration management
deckyctl edit           # Edit current config (auto-reloads)
deckyctl list           # List available configs
deckyctl use kde        # Switch to different config
deckyctl validate       # Validate current config

# Create and use custom configs
cp ~/.decky/configs/default.yaml ~/.decky/configs/work.yaml
deckyctl edit work
deckyctl use work
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
Place images in the `images/` folder and reference by name:
```yaml
buttons:
  1:
    icon: "firefox"  # Looks for firefox.png, firefox.jpg, etc.
    label: "Browser"  # Optional text below icon
```

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

| Feature | Decky | streamdeck-ui | OpenDeck |
|---------|-------|---------------|----------|
| Configuration | YAML files | GUI | GUI + Plugins |
| Resource Usage | Minimal | Moderate | Heavy |
| Version Control | ✅ Excellent | ❌ Database | ❌ Complex |
| Setup Complexity | Simple | Moderate | Complex |
| Plugin System | ❌ No | ✅ Python | ✅ Stream Deck SDK |
| Hot Reload | ✅ Yes | ❌ No | ❌ No |
| Dependencies | Minimal | Qt Framework | Electron |

## Tips and Tricks

### Multiple Configurations

With the service setup, switching between configs is easy:

```bash
# List available configs
deckyctl list

# Switch between configs instantly
deckyctl use work      # Work setup
deckyctl use gaming    # Gaming setup
deckyctl use streaming  # Streaming setup

# Edit any config
deckyctl edit work
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

# Or use deckyctl
deckyctl enable   # Enable auto-start
deckyctl disable  # Disable auto-start
```

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