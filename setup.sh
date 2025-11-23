#!/bin/bash

echo "Decky Stream Deck Setup Script"
echo "=============================="
echo

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo for system package installation"
    echo "Usage: sudo ./setup.sh"
    exit 1
fi

# Detect distro
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
elif [ -f /etc/fedora-release ]; then
    DISTRO="fedora"
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
else
    echo "Unsupported distribution. Please install dependencies manually."
    exit 1
fi

echo "Detected distribution: $DISTRO"
echo

# Install system dependencies
echo "Installing system dependencies..."
case $DISTRO in
    debian)
        apt-get update
        apt-get install -y python3-pip python3-dev python3-venv python3-full
        apt-get install -y libhidapi-libusb0 libusb-1.0-0-dev libudev-dev
        apt-get install -y xdotool  # For key simulation
        apt-get install -y fonts-dejavu  # Default font
        # Try to install Python packages via apt first
        apt-get install -y python3-pil python3-yaml || true
        ;;
    fedora)
        dnf install -y python3-pip python3-devel
        dnf install -y hidapi libusb1-devel libudev-devel
        dnf install -y xdotool
        dnf install -y dejavu-sans-fonts
        ;;
    arch)
        pacman -Sy --noconfirm python-pip python
        pacman -Sy --noconfirm hidapi libusb udev
        pacman -Sy --noconfirm xdotool
        pacman -Sy --noconfirm ttf-dejavu
        ;;
esac

echo
echo "Creating udev rules for Stream Deck access..."

# Create udev rules
cat > /etc/udev/rules.d/70-streamdeck.rules << 'EOF'
# Stream Deck Original
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0060", TAG+="uaccess"

# Stream Deck Original V2
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="006d", TAG+="uaccess"

# Stream Deck Mini
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0063", TAG+="uaccess"

# Stream Deck Mini V2
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0090", TAG+="uaccess"

# Stream Deck XL
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="006c", TAG+="uaccess"

# Stream Deck XL V2
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="008f", TAG+="uaccess"

# Stream Deck MK2
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0080", TAG+="uaccess"

# Stream Deck Pedal
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0086", TAG+="uaccess"

# Stream Deck Plus
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", ATTRS{idProduct}=="0084", TAG+="uaccess"
EOF

# Reload udev rules
udevadm control --reload-rules
udevadm trigger

echo "Udev rules created and reloaded"
echo

# Get the actual user (not root)
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

# Create virtual environment and install Python dependencies
echo "Creating Python virtual environment..."
VENV_PATH="$(pwd)/.venv"

# Create venv as the real user
su - "$REAL_USER" -c "cd $(pwd) && python3 -m venv $VENV_PATH"

echo "Installing Python dependencies in virtual environment..."
su - "$REAL_USER" -c "cd $(pwd) && $VENV_PATH/bin/pip install --upgrade pip"
su - "$REAL_USER" -c "cd $(pwd) && $VENV_PATH/bin/pip install -r requirements.txt"

echo
echo "Creating launcher script..."

# Create launcher script
cat > /usr/local/bin/decky << EOF
#!/bin/bash
cd $(pwd)
exec $VENV_PATH/bin/python src/decky.py "\$@"
EOF

chmod +x /usr/local/bin/decky

echo
echo "Setup complete!"
echo
echo "To use Decky:"
echo "1. Unplug and replug your Stream Deck"
echo "2. Run: decky"
echo "   or: decky /path/to/your/config.yaml"
echo
echo "The example configuration is at: $(pwd)/configs/example.yaml"
echo
echo "Note: You may need to log out and back in for udev rules to take effect."
