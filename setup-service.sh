#!/bin/bash
# Setup script for fx-open-range systemd service

set -e

SERVICE_NAME="fx-open-range"
SERVICE_FILE="/opt/fx-open-range/${SERVICE_NAME}.service"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Setting up ${SERVICE_NAME} systemd service..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "This script needs sudo privileges to install the systemd service."
    echo "Please run: sudo $0"
    exit 1
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

# Copy service file to systemd directory
echo "Installing service file..."
cp "$SERVICE_FILE" "$SYSTEMD_PATH"

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "Enabling service to start on boot..."
systemctl enable "${SERVICE_NAME}.service"

echo ""
echo "✓ Service installed successfully!"
echo ""
echo "To start the service now:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "To check service status:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop ${SERVICE_NAME}"
echo ""
echo "To disable auto-start on boot:"
echo "  sudo systemctl disable ${SERVICE_NAME}"


