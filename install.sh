#!/bin/bash
# Decky installation script

set -e

echo "🎮 Decky Installation Script"
echo "============================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DECKY_DIR="$SCRIPT_DIR"

# Check if running with sudo for system-wide installation
if [ "$EUID" -eq 0 ]; then
    INSTALL_MODE="system"
    INSTALL_DIR="/opt/decky"
    BIN_DIR="/usr/local/bin"
    SERVICE_MODE="system"
else
    INSTALL_MODE="user"
    INSTALL_DIR="$HOME/.local/share/decky"
    BIN_DIR="$HOME/.local/bin"
    SERVICE_MODE="user"
fi

echo "📍 Installation mode: $INSTALL_MODE"
echo "📂 Installation directory: $INSTALL_DIR"
echo "🔧 Binary directory: $BIN_DIR"
echo ""

# Ask for confirmation
read -p "Continue with installation? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]] && [ -n "$REPLY" ]; then
    echo "Installation cancelled."
    exit 1
fi

echo ""

# Development installation (symlink)
if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
    echo "🔗 Creating development installation (symlink)..."

    # Ensure bin directory exists
    mkdir -p "$BIN_DIR"

    # Create symlink to the decky script
    ln -sf "$DECKY_DIR/bin/decky" "$BIN_DIR/decky"

    echo -e "${GREEN}✓${NC} Development installation complete"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Add $BIN_DIR to your PATH if not already there"
    echo "  2. Set DECKY_HOME if needed: export DECKY_HOME=$DECKY_DIR"
    echo "  3. Install systemd service: decky install-service"
    echo "  4. Start Decky: decky start"

else
    # Full installation (copy files)
    echo "📦 Installing Decky to $INSTALL_DIR..."

    # Create installation directory
    if [ "$INSTALL_MODE" = "system" ]; then
        mkdir -p "$INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR"
    fi

    # Copy necessary files
    echo "  Copying source files..."
    cp -r "$DECKY_DIR/src" "$INSTALL_DIR/"

    echo "  Copying configuration..."
    mkdir -p "$INSTALL_DIR/configs"

    # Copy virtual environment if it exists
    if [ -d "$DECKY_DIR/.venv" ]; then
        echo "  Copying virtual environment..."
        cp -r "$DECKY_DIR/.venv" "$INSTALL_DIR/"
    else
        echo -e "${YELLOW}⚠${NC}  No virtual environment found. You'll need to install dependencies manually."
    fi

    # Copy the decky script
    echo "  Installing decky command..."
    mkdir -p "$BIN_DIR"
    cp "$DECKY_DIR/bin/decky" "$BIN_DIR/decky"
    chmod +x "$BIN_DIR/decky"

    # Update the systemd service file path if needed
    if [ -f "$HOME/.config/systemd/user/decky.service" ]; then
        echo "  Updating systemd service..."
        systemctl --user stop decky 2>/dev/null || true
        systemctl --user daemon-reload
    fi

    echo -e "${GREEN}✓${NC} Installation complete!"
    echo ""
    echo "📝 Next steps:"
    if [ "$INSTALL_MODE" = "user" ]; then
        echo "  1. Add $BIN_DIR to your PATH:"
        echo "     echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc"
        echo "  2. Reload your shell or run: source ~/.bashrc"
    fi
    echo "  3. Copy your configurations to ~/.decky/configs/"
    echo "  4. Start Decky: decky start"
fi

echo ""
echo "🎮 Decky installation finished!"
echo "Run 'decky --help' for usage information"
