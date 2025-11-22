#!/bin/bash

# Decky Service Installation Script
# Sets up Decky to run as a systemd user service with configs in ~/.decky

set -e

echo "Installing Decky as a user service..."
echo "======================================="
echo

# Get the current directory (where Decky is installed)
DECKY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create ~/.decky directory structure
echo "Creating ~/.decky directory..."
mkdir -p ~/.decky/{configs,images}

# Copy example configs if they don't exist
if [ ! -f ~/.decky/configs/default.yaml ]; then
    echo "Copying example configurations..."
    cp "$DECKY_DIR/configs/minimal.yaml" ~/.decky/configs/default.yaml
    cp "$DECKY_DIR/configs/kde.yaml" ~/.decky/configs/kde.yaml 2>/dev/null || true
    cp "$DECKY_DIR/configs/example.yaml" ~/.decky/configs/example.yaml 2>/dev/null || true
    echo "Default config created at: ~/.decky/configs/default.yaml"
else
    echo "Configs already exist in ~/.decky/configs/"
fi

# Create the systemd user service
echo "Creating systemd user service..."
mkdir -p ~/.config/systemd/user/

cat > ~/.config/systemd/user/decky.service << EOF
[Unit]
Description=Decky Stream Deck Controller
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Restart=on-failure
RestartSec=5

# Environment
Environment="DISPLAY=:0"
Environment="XAUTHORITY=%h/.Xauthority"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

# Use the virtual environment Python
ExecStart=$DECKY_DIR/.venv/bin/python $DECKY_DIR/src/decky.py %h/.decky/configs/default.yaml

# Logging
StandardOutput=journal
StandardError=journal

# Give it time to shutdown gracefully
TimeoutStopSec=10

[Install]
WantedBy=default.target
EOF

echo "Service file created at: ~/.config/systemd/user/decky.service"
echo

# Reload systemd user daemon
echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

# Enable the service
echo "Enabling Decky service..."
systemctl --user enable decky.service

echo
echo "Installation complete!"
echo "======================================"
echo
echo "Decky has been installed as a user service."
echo
echo "Configuration location: ~/.decky/configs/"
echo "Default config: ~/.decky/configs/default.yaml"
echo
echo "Service commands:"
echo "  Start now:    systemctl --user start decky"
echo "  Stop:         systemctl --user stop decky"
echo "  Restart:      systemctl --user restart decky"
echo "  Status:       systemctl --user status decky"
echo "  View logs:    journalctl --user -u decky -f"
echo "  Disable:      systemctl --user disable decky"
echo
echo "The service will start automatically on your next login."
echo "To start it now, run: systemctl --user start decky"
echo
echo "To edit your config:"
echo "  \$EDITOR ~/.decky/configs/default.yaml"
echo "  systemctl --user restart decky  # Apply changes"