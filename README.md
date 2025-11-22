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

- Linux (tested on Ubuntu, Fedora, Arch)
- Python 3.7+
- Stream Deck device

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/decky.git
cd decky

# Run setup script (requires sudo)
chmod +x setup.sh
sudo ./setup.sh

# Start Decky
decky
```

### Manual Installation

If you prefer manual installation:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-pip libhidapi-libusb0 xdotool

# Install Python packages
pip3 install streamdeck pyyaml pillow

# Add udev rules for Stream Deck access (see setup.sh for rules)
sudo cp udev/70-streamdeck.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

## Usage

### Basic Usage

```bash
# Run with example config
decky

# Run with custom config
decky ~/my-streamdeck-config.yaml

# Run with debug logging
decky --log-level DEBUG
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
```bash
# Work setup
decky configs/work.yaml

# Gaming setup
decky configs/gaming.yaml

# Streaming setup
decky configs/streaming.yaml
```

### Git Integration
```yaml
# Add to your dotfiles repo
cd ~/dotfiles
cp -r /path/to/decky/configs/example.yaml streamdeck.yaml
git add streamdeck.yaml
git commit -m "Add Stream Deck configuration"
```

### Systemd Service
Create a service to run Decky at startup:
```bash
# Create service file
sudo nano /etc/systemd/system/decky.service

# Add:
[Unit]
Description=Decky Stream Deck Controller
After=graphical.target

[Service]
Type=simple
User=yourusername
ExecStart=/usr/local/bin/decky /home/yourusername/decky-config.yaml
Restart=on-failure

[Install]
WantedBy=default.target

# Enable service
sudo systemctl enable decky
sudo systemctl start decky
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