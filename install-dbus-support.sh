#!/bin/bash
# Install optional D-Bus support for real-time screen lock monitoring

echo "Installing D-Bus support for enhanced screen lock monitoring..."
echo "This will enable real-time lock detection instead of polling."
echo ""
echo "You'll need to enter your sudo password to install system packages."
echo ""

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    libdbus-1-dev \
    libglib2.0-dev \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0

# Install Python packages in virtual environment
echo ""
echo "Installing Python D-Bus bindings..."
.venv/bin/pip install dbus-python PyGObject

echo ""
echo "D-Bus support installation complete!"
echo "Please restart the Decky service with: ./deckyctl restart"
echo ""
echo "With D-Bus support, screen lock detection will be instant instead of polling every second."
