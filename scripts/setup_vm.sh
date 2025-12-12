#!/bin/bash
# VANI VM Setup Script for chroma-vm
# Run this ON the VM to set up the environment
# Modified to use /home/postgres/vani

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() { echo -e "\n${BLUE}========================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}========================================${NC}\n"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

print_header "VANI VM Setup for chroma-vm"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as a normal user (postgres), not root"
    exit 1
fi

print_info "This script will set up VANI on chroma-vm"
print_info "Deployment directory: /home/postgres/vani"
echo ""

# Step 1: Update system
print_header "[1/8] Updating System"
print_info "Updating package lists..."
sudo apt update -qq
print_info "Upgrading installed packages..."
sudo apt upgrade -y -qq
print_success "System updated"

# Step 2: Install Python 3.11
print_header "[2/8] Installing Python 3.11"
if command -v python3.11 &> /dev/null; then
    print_success "Python 3.11 already installed"
    python3.11 --version
else
    print_info "Installing Python 3.11..."
    sudo apt install software-properties-common -y -qq
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update -qq
    sudo apt install python3.11 python3.11-venv python3.11-dev -y -qq
    print_success "Python 3.11 installed"
    python3.11 --version
fi

# Step 3: Install system dependencies
print_header "[3/8] Installing System Dependencies"
print_info "Installing build tools and libraries..."
sudo apt install -y -qq \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    python3-pip \
    htop \
    unzip \
    jq
print_success "System dependencies installed"

# Step 4: Install ngrok
print_header "[4/8] Installing Ngrok"
if command -v ngrok &> /dev/null; then
    print_success "Ngrok already installed"
    ngrok version
else
    print_info "Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
        sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
        sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update -qq
    sudo apt install ngrok -y -qq
    print_success "Ngrok installed"
    ngrok version
fi

# Step 5: Configure ngrok
print_header "[5/8] Configuring Ngrok"
if [ -f ~/.config/ngrok/ngrok.yml ]; then
    print_warning "Ngrok config already exists"
    print_info "Skipping ngrok configuration"
else
    print_info "Please enter your ngrok authtoken"
    print_info "Get it from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo ""
    read -p "Ngrok authtoken: " NGROK_TOKEN
    
    if [ -n "$NGROK_TOKEN" ]; then
        ngrok config add-authtoken "$NGROK_TOKEN"
        
        # Create config with static domain
        mkdir -p ~/.config/ngrok
        cat > ~/.config/ngrok/ngrok.yml << EOF
version: "2"
authtoken: $NGROK_TOKEN
tunnels:
  vani:
    proto: http
    addr: 5000
    domain: vani.ngrok.app
log_level: info
log_format: json
EOF
        
        print_success "Ngrok configured with domain: vani.ngrok.app"
    else
        print_warning "Skipped ngrok configuration"
        print_info "You can configure it later with: ngrok config add-authtoken YOUR_TOKEN"
    fi
fi

# Step 6: Create application directory
print_header "[6/8] Creating Application Directory"
if [ -d /home/postgres/vani ]; then
    print_warning "Directory /home/postgres/vani already exists"
else
    mkdir -p /home/postgres/vani
    print_success "Created /home/postgres/vani"
fi

# Step 7: Setup systemd services
print_header "[7/8] Setting Up Systemd Services"

# Flask service
print_info "Creating Flask service..."
sudo tee /etc/systemd/system/vani-flask.service > /dev/null << EOF
[Unit]
Description=VANI Flask Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=postgres
Group=postgres
WorkingDirectory=/home/postgres/vani
Environment="PATH=/home/postgres/vani/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/home/postgres/vani/.env.local

ExecStart=/home/postgres/vani/venv/bin/python /home/postgres/vani/run.py

Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=vani-flask

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

print_success "Flask service created"

# Ngrok service
print_info "Creating ngrok service..."
sudo tee /etc/systemd/system/vani-ngrok.service > /dev/null << EOF
[Unit]
Description=Ngrok Tunnel for VANI
After=network-online.target vani-flask.service
Wants=network-online.target
Requires=vani-flask.service

[Service]
Type=simple
User=postgres
Group=postgres
WorkingDirectory=/home/postgres

ExecStartPre=/bin/sleep 10
ExecStart=/usr/local/bin/ngrok start vani --config /home/postgres/.config/ngrok/ngrok.yml

Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=vani-ngrok

NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

print_success "Ngrok service created"

# Reload systemd
sudo systemctl daemon-reload
print_success "Systemd services configured"

# Step 8: Create .env.local template
print_header "[8/8] Creating Environment Template"
if [ -f /home/postgres/vani/.env.local ]; then
    print_warning ".env.local already exists, not overwriting"
else
    cat > /home/postgres/vani/.env.local << 'EOF'
# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
DEBUG=False
SECRET_KEY=CHANGE_THIS_TO_RANDOM_STRING

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_CONNECTION=postgresql://postgres.xxx:5432/postgres
SUPABASE_DB_PASSWORD=your-db-password

# Ngrok Configuration
NGROK_AUTHTOKEN=your-ngrok-authtoken
NGROK_DOMAIN=vani.ngrok.app
WEBHOOK_BASE_URL=https://vani.ngrok.app

# Email - Resend
RESEND_API_KEY=re_your_key
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_HIT_EMAIL=notifications@yourdomain.com

# WhatsApp - Twilio
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_TO_WHATSAPP_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=sk-your-key

# Cal.com (optional)
CAL_COM_API_KEY=cal_live_your_key
CAL_COM_EVENT_TYPE_ID=your-event-id
CAL_COM_USERNAME=your-username

# Google Sheets (optional)
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}

# Industry (default)
DEFAULT_INDUSTRY=fmcg
EOF
    
    chmod 600 /home/postgres/vani/.env.local
    print_success "Created .env.local template"
    print_warning "IMPORTANT: Edit /home/postgres/vani/.env.local with your actual credentials"
fi

# Final instructions
print_header "Setup Complete!"

print_success "VM environment is ready for VANI deployment"
echo ""
echo "Next steps:"
echo ""
echo "1. Deploy application files to /home/postgres/vani"
echo ""
echo "2. Edit environment file:"
echo "   nano /home/postgres/vani/.env.local"
echo ""
echo "3. Install Python dependencies:"
echo "   cd /home/postgres/vani"
echo "   python3.11 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Run database migrations:"
echo "   python do_setup.py"
echo ""
echo "5. Start services:"
echo "   sudo systemctl enable vani-flask vani-ngrok"
echo "   sudo systemctl start vani-flask"
echo "   sudo systemctl start vani-ngrok"
echo ""
echo "6. Check status:"
echo "   sudo systemctl status vani-flask vani-ngrok"
echo ""
echo "7. Access application:"
echo "   https://vani.ngrok.app"
echo ""

print_success "Setup completed! 🚀"

