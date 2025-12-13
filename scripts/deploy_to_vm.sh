#!/bin/bash
# VANI Deployment Script for Google VM
# This script deploys VANI from local machine to chroma-vm
# Usage: ./deploy_to_vm.sh VM_IP [VM_USER] [SSH_KEY]
# Modified to use /home/postgres/vani

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() { echo ""; echo -e "${BLUE}========================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}========================================${NC}"; echo ""; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Configuration
VM_IP="$1"
VM_USER="${2:-postgres}"
SSH_KEY="${3}"
DEPLOY_DIR="/home/postgres/vani"

# Validate arguments
if [ -z "$VM_IP" ]; then
    print_error "VM IP address is required!"
    echo ""
    echo "Usage: ./deploy_to_vm.sh VM_IP [VM_USER] [SSH_KEY]"
    echo ""
    echo "Examples:"
    echo "  ./deploy_to_vm.sh 34.100.169.186"
    echo "  ./deploy_to_vm.sh 34.100.169.186 postgres"
    echo ""
    exit 1
fi

print_header "VANI Deployment to chroma-vm"

echo "Configuration:"
echo "  VM IP:    $VM_IP"
echo "  User:     $VM_USER"
echo "  Deploy:   $DEPLOY_DIR"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelled"
    exit 0
fi

# Step 1: Test SSH connection
print_header "[1/7] Testing SSH Connection"

if [ -n "$SSH_KEY" ]; then
    SSH_CMD="ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
    SCP_CMD="scp -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
else
    SSH_CMD="ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
    SCP_CMD="scp -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
fi

if $SSH_CMD "$VM_USER@$VM_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    print_success "SSH connection established"
else
    print_error "Cannot connect to VM. Check IP, user, and SSH key."
    exit 1
fi

# Step 2: Create deployment package
print_header "[2/7] Creating Deployment Package"

print_info "Packaging application files..."

TEMP_DIR=$(mktemp -d)
PACKAGE_NAME="vani-deploy-$(date +%Y%m%d_%H%M%S).tar.gz"

tar czf "$TEMP_DIR/$PACKAGE_NAME" \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env.local' \
    --exclude='node_modules' \
    --exclude='logs/*' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='terminals' \
    --exclude='*.tar.gz' \
    . 2>/dev/null

PACKAGE_SIZE=$(du -h "$TEMP_DIR/$PACKAGE_NAME" | cut -f1)
print_success "Package created: $PACKAGE_NAME ($PACKAGE_SIZE)"

# Step 3: Copy to VM
print_header "[3/7] Uploading to VM"

print_info "Uploading package to VM..."
$SCP_CMD "$TEMP_DIR/$PACKAGE_NAME" "$VM_USER@$VM_IP:/tmp/" || {
    print_error "Failed to upload package"
    rm -rf "$TEMP_DIR"
    exit 1
}

print_success "Package uploaded"

# Cleanup local temp
rm -rf "$TEMP_DIR"

# Step 4: Extract and setup on VM
print_header "[4/7] Setting Up Application"

$SSH_CMD "$VM_USER@$VM_IP" bash << ENDSSH
set -e

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p $DEPLOY_DIR

# Backup existing .env.local if exists
if [ -f "$DEPLOY_DIR/.env.local" ]; then
    echo "Backing up existing .env.local..."
    cp $DEPLOY_DIR/.env.local /tmp/vani-env-backup-\$(date +%Y%m%d_%H%M%S).local
fi

# Extract package
echo "Extracting files..."
cd $DEPLOY_DIR
tar xzf /tmp/$PACKAGE_NAME

# Restore .env.local if backed up
if [ -f /tmp/vani-env-backup-*.local ]; then
    echo "Restoring .env.local..."
    cp /tmp/vani-env-backup-*.local $DEPLOY_DIR/.env.local 2>/dev/null || true
fi

# Cleanup
rm /tmp/$PACKAGE_NAME

echo "✅ Application files extracted"
ENDSSH

print_success "Application setup complete"

# Step 5: Install dependencies
print_header "[5/7] Installing Dependencies"

$SSH_CMD "$VM_USER@$VM_IP" bash << 'ENDSSH'
set -e
cd /home/postgres/vani

echo "Setting up Python virtual environment..."

# Create venv if not exists
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

# Activate and install
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel -q

echo "Installing requirements..."
pip install -r requirements.txt -q

# Verify installation
python -c "import flask; print('✅ Flask:', flask.__version__)"
python -c "import supabase; print('✅ Supabase installed')"

echo "✅ Dependencies installed"
ENDSSH

print_success "Dependencies installed"

# Step 6: Restart services
print_header "[6/7] Restarting Services"

$SSH_CMD "$VM_USER@$VM_IP" bash << 'ENDSSH'
set -e

# Check if systemd services exist
if systemctl list-unit-files | grep -q vani-flask; then
    echo "Restarting Flask service..."
    sudo systemctl restart vani-flask
    sleep 3
    
    if sudo systemctl is-active --quiet vani-flask; then
        echo "✅ Flask service running"
    else
        echo "❌ Flask service failed to start"
        sudo journalctl -u vani-flask -n 20 --no-pager
        exit 1
    fi
else
    echo "⚠️  Flask service not configured. Run setup script first."
fi

if systemctl list-unit-files | grep -q vani-ngrok; then
    echo "Restarting ngrok service..."
    sudo systemctl restart vani-ngrok
    sleep 5
    
    if sudo systemctl is-active --quiet vani-ngrok; then
        echo "✅ Ngrok service running"
    else
        echo "⚠️  Ngrok service failed to start"
        sudo journalctl -u vani-ngrok -n 20 --no-pager
    fi
else
    echo "⚠️  Ngrok service not configured. Run setup script first."
fi
ENDSSH

print_success "Services restarted"

# Step 7: Verify deployment
print_header "[7/7] Verifying Deployment"

$SSH_CMD "$VM_USER@$VM_IP" bash << 'ENDSSH'
set -e

echo "Checking Flask service..."
if sudo systemctl is-active --quiet vani-flask; then
    echo "✅ Flask: Running"
    
    # Test Flask endpoint
    if curl -f http://127.0.0.1:5000 -o /dev/null -s; then
        echo "✅ Flask: Responding"
    else
        echo "⚠️  Flask: Not responding on port 5000"
    fi
else
    echo "❌ Flask: Not running"
fi

echo ""
echo "Checking ngrok service..."
if sudo systemctl is-active --quiet vani-ngrok; then
    echo "✅ Ngrok: Running"
    
    # Get ngrok URL
    sleep 3
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'N/A')" 2>/dev/null || echo "N/A")
    
    if [ "$NGROK_URL" != "N/A" ]; then
        echo "✅ Ngrok URL: $NGROK_URL"
    else
        echo "⚠️  Ngrok: No tunnel found"
    fi
else
    echo "❌ Ngrok: Not running"
fi

echo ""
echo "Recent Flask logs:"
sudo journalctl -u vani-flask -n 5 --no-pager
ENDSSH

# Final summary
print_header "Deployment Complete!"

print_success "Application deployed successfully to $VM_IP"
echo ""
echo "Next steps:"
echo "  1. Access: https://vani.ngrok.app"
echo "  2. Login: https://vani.ngrok.app/login"
echo "  3. Command Center: https://vani.ngrok.app/command-center"
echo ""
echo "To view logs:"
if [ -n "$SSH_KEY" ]; then
    echo "  ssh -i $SSH_KEY $VM_USER@$VM_IP 'sudo journalctl -u vani-flask -f'"
else
    echo "  ssh $VM_USER@$VM_IP 'sudo journalctl -u vani-flask -f'"
fi
echo ""

print_success "Deployment completed successfully! 🚀"






