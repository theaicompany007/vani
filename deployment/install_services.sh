#!/bin/bash
# Install systemd service files for VANI
# Run this script on the VM after deploying the application

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo ""
echo "========================================="
echo "VANI Systemd Services Installation"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as a normal user, not root"
    exit 1
fi

# Get current user
CURRENT_USER=$(whoami)

# Check if service files exist
if [ ! -f "vani-flask.service" ] || [ ! -f "vani-ngrok.service" ]; then
    print_error "Service files not found in current directory"
    print_error "Make sure you're in the deployment/ directory"
    exit 1
fi

echo "Installing services for user: $CURRENT_USER"
echo ""

# Create temporary copies with username replaced
print_warning "Preparing service files..."

cp vani-flask.service /tmp/vani-flask.service.tmp
cp vani-ngrok.service /tmp/vani-ngrok.service.tmp

sed -i "s/YOUR_USERNAME/$CURRENT_USER/g" /tmp/vani-flask.service.tmp
sed -i "s/YOUR_USERNAME/$CURRENT_USER/g" /tmp/vani-ngrok.service.tmp

# Install Flask service
print_warning "Installing Flask service..."
sudo cp /tmp/vani-flask.service.tmp /etc/systemd/system/vani-flask.service
sudo chmod 644 /etc/systemd/system/vani-flask.service
print_success "Flask service installed"

# Install ngrok service
print_warning "Installing ngrok service..."
sudo cp /tmp/vani-ngrok.service.tmp /etc/systemd/system/vani-ngrok.service
sudo chmod 644 /etc/systemd/system/vani-ngrok.service
print_success "Ngrok service installed"

# Cleanup temp files
rm /tmp/vani-flask.service.tmp /tmp/vani-ngrok.service.tmp

# Reload systemd
print_warning "Reloading systemd..."
sudo systemctl daemon-reload
print_success "Systemd reloaded"

# Enable services
print_warning "Enabling services to start on boot..."
sudo systemctl enable vani-flask
sudo systemctl enable vani-ngrok
print_success "Services enabled"

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Service files installed:"
echo "  ✓ /etc/systemd/system/vani-flask.service"
echo "  ✓ /etc/systemd/system/vani-ngrok.service"
echo ""
echo "Services are configured for user: $CURRENT_USER"
echo ""
echo "Next steps:"
echo ""
echo "1. Verify .env.local exists and is configured:"
echo "   cat /opt/vani/.env.local"
echo ""
echo "2. Start Flask service:"
echo "   sudo systemctl start vani-flask"
echo ""
echo "3. Check Flask status:"
echo "   sudo systemctl status vani-flask"
echo ""
echo "4. Start ngrok service:"
echo "   sudo systemctl start vani-ngrok"
echo ""
echo "5. Check ngrok status:"
echo "   sudo systemctl status vani-ngrok"
echo ""
echo "6. View logs:"
echo "   sudo journalctl -u vani-flask -f"
echo "   sudo journalctl -u vani-ngrok -f"
echo ""
echo "To start both services now:"
echo "   sudo systemctl start vani-flask vani-ngrok"
echo ""

print_success "Installation completed successfully! 🚀"

