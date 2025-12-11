# Project VANI - Google VM Deployment with Ngrok

## Overview
This guide provides step-by-step instructions to deploy Project VANI on Google Cloud VM with ngrok static domain (`vani.ngrok.app`) for public access and webhook functionality.

## Architecture
- **Server**: Google Compute Engine VM (Ubuntu 22.04 LTS)
- **Application**: Flask Python app (Port 5000)
- **Public Access**: Ngrok tunnel with static domain
- **Database**: Supabase (PostgreSQL)
- **Services**: Systemd for process management

## Prerequisites

### 1. Google Cloud Platform
- Active GCP account with billing enabled
- `gcloud` CLI installed and configured (optional, can use GCP Console)

### 2. Ngrok Account
- Ngrok account (sign up at https://ngrok.com)
- Static domain reserved: `vani.ngrok.app` (requires paid plan)
- Ngrok authtoken from dashboard

### 3. API Keys & Credentials
- Supabase: URL, Anon Key, Service Key, Connection String
- Resend API Key
- Twilio: Account SID, Auth Token, WhatsApp Number
- OpenAI API Key
- Cal.com API Key (optional)
- Google Sheets credentials (optional)

---

## Part 1: Google VM Setup

### Step 1: Create VM Instance

#### Option A: Using GCP Console
1. Go to: https://console.cloud.google.com/compute/instances
2. Click "CREATE INSTANCE"
3. Configure:
   - **Name**: `vani-server`
   - **Region**: `us-central1` (or closest to your users)
   - **Zone**: `us-central1-a`
   - **Machine type**: `e2-medium` (2 vCPU, 4 GB RAM) - minimum
   - **Boot disk**: 
     - OS: Ubuntu 22.04 LTS
     - Size: 20 GB (minimum)
   - **Firewall**: 
     - ✅ Allow HTTP traffic
     - ✅ Allow HTTPS traffic
4. Click "CREATE"

#### Option B: Using gcloud CLI
```bash
gcloud compute instances create vani-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-balanced \
  --tags=http-server,https-server \
  --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git'
```

### Step 2: Configure Firewall Rules

```bash
# Allow Flask port (optional, only if accessing directly)
gcloud compute firewall-rules create allow-flask \
  --allow tcp:5000 \
  --source-ranges 0.0.0.0/0 \
  --target-tags http-server

# Allow ngrok management port (optional, for debugging)
gcloud compute firewall-rules create allow-ngrok-dashboard \
  --allow tcp:4040 \
  --source-ranges YOUR_IP/32 \
  --target-tags http-server
```

**Note**: With ngrok, you don't need to expose Flask port 5000 publicly. All traffic goes through ngrok tunnel.

### Step 3: Connect to VM

```bash
# SSH using gcloud
gcloud compute ssh vani-server --zone=us-central1-a

# Or using GCP Console: Click "SSH" button on VM instance
```

---

## Part 2: Server Configuration

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Python 3.11

```bash
# Add deadsnakes PPA for Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Verify installation
python3.11 --version
```

### Step 3: Install System Dependencies

```bash
# Install Git
sudo apt install git -y

# Install build essentials for Python packages
sudo apt install build-essential libpq-dev -y

# Install additional utilities
sudo apt install curl wget htop unzip -y
```

### Step 4: Install Ngrok

```bash
# Download and install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null

echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list

sudo apt update && sudo apt install ngrok -y

# Verify installation
ngrok version
```

### Step 5: Configure Ngrok

```bash
# Set your ngrok authtoken (get from https://dashboard.ngrok.com/get-started/your-authtoken)
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN

# Edit ngrok config to add static domain
nano ~/.config/ngrok/ngrok.yml
```

Add this configuration:

```yaml
version: "2"
authtoken: YOUR_NGROK_AUTHTOKEN
tunnels:
  vani:
    proto: http
    addr: 5000
    domain: vani.ngrok.app
log_level: info
log_format: json
log: /var/log/ngrok.log
```

**Note**: Replace `YOUR_NGROK_AUTHTOKEN` with your actual token. The domain `vani.ngrok.app` must be reserved in your ngrok dashboard.

---

## Part 3: Application Deployment

### Step 1: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/vani
sudo chown $USER:$USER /opt/vani

# Clone repository (replace with your actual repo URL)
cd /opt/vani
git clone https://github.com/YOUR_USERNAME/vani.git .

# Or if transferring from local machine
# On local machine: scp -r vani/* USER@VM_IP:/opt/vani/
```

**Alternative**: Use deployment script (see Part 5)

### Step 2: Create Python Virtual Environment

```bash
cd /opt/vani
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Verify installations
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import supabase; print('Supabase:', supabase.__version__)"
```

### Step 4: Configure Environment Variables

```bash
# Create .env.local file
nano .env.local
```

Add the following (replace with your actual values):

```bash
# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
DEBUG=False
SECRET_KEY=your-secret-key-here-generate-random-string

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
```

**Security Note**: Set proper file permissions:
```bash
chmod 600 .env.local
```

### Step 5: Run Database Migrations

```bash
# Ensure venv is activated
source venv/bin/activate

# Run database setup
python do_setup.py
```

**Alternative**: Run migrations in Supabase SQL Editor:
1. Go to your Supabase project
2. Navigate to SQL Editor
3. Copy contents of `COMPLETE_SETUP.sql`
4. Execute

### Step 6: Create Super User

```bash
# Method 1: Using script
python create_super_user.py

# Method 2: Via Supabase
# 1. Sign up first user via web interface
# 2. In Supabase SQL Editor, run:
# UPDATE app_users SET is_super_user = true 
# WHERE supabase_user_id = 'your-user-id';
```

---

## Part 4: Service Configuration with Systemd

### Step 1: Create Flask Service

```bash
sudo nano /etc/systemd/system/vani-flask.service
```

Add this content (replace `YOUR_USERNAME` with your actual username):

```ini
[Unit]
Description=VANI Flask Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/opt/vani
Environment="PATH=/opt/vani/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Load environment from .env files
EnvironmentFile=/opt/vani/.env.local

# Start Flask app
ExecStart=/opt/vani/venv/bin/python /opt/vani/run.py

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vani-flask

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Step 2: Create Ngrok Service

```bash
sudo nano /etc/systemd/system/vani-ngrok.service
```

Add this content (replace `YOUR_USERNAME`):

```ini
[Unit]
Description=Ngrok Tunnel for VANI
After=network-online.target vani-flask.service
Wants=network-online.target
Requires=vani-flask.service

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME

# Wait for Flask to start
ExecStartPre=/bin/sleep 10

# Start ngrok tunnel
ExecStart=/usr/local/bin/ngrok start vani --config /home/YOUR_USERNAME/.config/ngrok/ngrok.yml

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vani-ngrok

# Security
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### Step 3: Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable vani-flask
sudo systemctl enable vani-ngrok

# Start Flask first
sudo systemctl start vani-flask

# Check Flask status
sudo systemctl status vani-flask

# Wait 10 seconds, then start ngrok
sleep 10
sudo systemctl start vani-ngrok

# Check ngrok status
sudo systemctl status vani-ngrok
```

### Step 4: Monitor Services

```bash
# View Flask logs
sudo journalctl -u vani-flask -f

# View ngrok logs
sudo journalctl -u vani-ngrok -f

# View both
sudo journalctl -u vani-flask -u vani-ngrok -f

# Check if services are running
sudo systemctl status vani-flask vani-ngrok
```

---

## Part 5: Automated Deployment Script

Save this script as `deploy_to_vm.sh` on your **local machine**:

```bash
#!/bin/bash
# VANI Deployment Script for Google VM
# Usage: ./deploy_to_vm.sh VM_IP

set -e

VM_IP="$1"
VM_USER="${2:-$USER}"
SSH_KEY="${3:-~/.ssh/google_compute_engine}"

if [ -z "$VM_IP" ]; then
    echo "Usage: ./deploy_to_vm.sh VM_IP [VM_USER] [SSH_KEY]"
    echo "Example: ./deploy_to_vm.sh 35.123.45.67"
    exit 1
fi

echo "========================================"
echo "VANI Deployment to Google VM"
echo "========================================"
echo "VM IP: $VM_IP"
echo "User: $VM_USER"
echo ""

# Create deployment package
echo "[1/6] Creating deployment package..."
tar czf vani-deploy.tar.gz \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env.local' \
    --exclude='node_modules' \
    --exclude='logs/*' \
    .

echo "[2/6] Copying files to VM..."
scp -i "$SSH_KEY" vani-deploy.tar.gz "$VM_USER@$VM_IP:/tmp/"

echo "[3/6] Extracting files on VM..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'ENDSSH'
    sudo mkdir -p /opt/vani
    sudo chown $USER:$USER /opt/vani
    cd /opt/vani
    tar xzf /tmp/vani-deploy.tar.gz
    rm /tmp/vani-deploy.tar.gz
ENDSSH

echo "[4/6] Installing dependencies..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'ENDSSH'
    cd /opt/vani
    python3.11 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
ENDSSH

echo "[5/6] Restarting services..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'ENDSSH'
    sudo systemctl restart vani-flask
    sleep 5
    sudo systemctl restart vani-ngrok
ENDSSH

echo "[6/6] Verifying deployment..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'ENDSSH'
    sudo systemctl status vani-flask --no-pager
    sudo systemctl status vani-ngrok --no-pager
ENDSSH

# Cleanup
rm vani-deploy.tar.gz

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
echo "Access your app at: https://vani.ngrok.app"
echo ""
echo "To view logs:"
echo "  ssh $VM_USER@$VM_IP 'sudo journalctl -u vani-flask -f'"
echo "  ssh $VM_USER@$VM_IP 'sudo journalctl -u vani-ngrok -f'"
echo ""
```

Make it executable:
```bash
chmod +x deploy_to_vm.sh
```

Usage:
```bash
./deploy_to_vm.sh YOUR_VM_IP
```

---

## Part 6: Verification & Testing

### Step 1: Check Services Status

```bash
# On VM
sudo systemctl status vani-flask
sudo systemctl status vani-ngrok

# Check if processes are running
ps aux | grep python
ps aux | grep ngrok
```

### Step 2: Test Flask Locally

```bash
# On VM
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/
```

Expected: JSON response or HTML page

### Step 3: Check Ngrok Tunnel

```bash
# On VM
curl http://localhost:4040/api/tunnels | python3 -m json.tool

# Or check dashboard
# Forward port: ssh -L 4040:localhost:4040 USER@VM_IP
# Then open: http://localhost:4040
```

Expected: Tunnel information with `public_url: https://vani.ngrok.app`

### Step 4: Test Public Access

```bash
# From your local machine
curl https://vani.ngrok.app/api/health

# Open in browser
open https://vani.ngrok.app
```

### Step 5: Test Application Features

1. **Login**: https://vani.ngrok.app/login
2. **Command Center**: https://vani.ngrok.app/command-center
3. **Dashboard**: https://vani.ngrok.app/dashboard
4. **Webhooks**: 
   - Resend: https://vani.ngrok.app/api/webhooks/resend
   - Twilio: https://vani.ngrok.app/api/webhooks/twilio

---

## Part 7: Configure Webhooks

### Step 1: Update Webhook URLs

Run the configuration script:

```bash
# On VM
cd /opt/vani
source venv/bin/activate
python scripts/configure_webhooks.py
```

### Step 2: Manual Webhook Configuration

#### Resend Webhooks
1. Go to: https://resend.com/webhooks
2. Add webhook: `https://vani.ngrok.app/api/webhooks/resend`
3. Select events: `email.sent`, `email.delivered`, `email.bounced`, `email.opened`, `email.clicked`

#### Twilio Webhooks
1. Go to: https://console.twilio.com/
2. Configure WhatsApp Sandbox or Number
3. When message comes in: `https://vani.ngrok.app/api/webhooks/twilio`

#### Cal.com Webhooks
1. Go to: https://app.cal.com/settings/developer/webhooks
2. Add webhook: `https://vani.ngrok.app/api/webhooks/cal-com`
3. Select events: `BOOKING_CREATED`, `BOOKING_CANCELLED`

---

## Part 8: Maintenance & Operations

### View Logs

```bash
# Real-time Flask logs
sudo journalctl -u vani-flask -f

# Real-time ngrok logs
sudo journalctl -u vani-ngrok -f

# Application logs (if file logging enabled)
tail -f /opt/vani/logs/application.log

# Last 100 lines
sudo journalctl -u vani-flask -n 100

# Logs from last hour
sudo journalctl -u vani-flask --since "1 hour ago"
```

### Restart Services

```bash
# Restart Flask
sudo systemctl restart vani-flask

# Restart ngrok
sudo systemctl restart vani-ngrok

# Restart both
sudo systemctl restart vani-flask vani-ngrok
```

### Update Application

```bash
# SSH to VM
cd /opt/vani

# Pull latest code
git pull

# Activate venv
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart services
sudo systemctl restart vani-flask vani-ngrok
```

### Stop Services

```bash
# Stop all
sudo systemctl stop vani-flask vani-ngrok

# Disable from starting on boot
sudo systemctl disable vani-flask vani-ngrok
```

### Monitor Resources

```bash
# CPU and Memory usage
htop

# Disk usage
df -h

# Check specific process
ps aux | grep python
ps aux | grep ngrok
```

---

## Troubleshooting

### Flask Not Starting

**Check logs:**
```bash
sudo journalctl -u vani-flask -n 50
```

**Common issues:**
- Missing environment variables in `.env.local`
- Python dependency errors
- Database connection failures
- Port 5000 already in use

**Solution:**
```bash
# Check if port is in use
sudo lsof -i :5000

# Kill process if needed
sudo kill -9 $(sudo lsof -t -i:5000)

# Restart service
sudo systemctl restart vani-flask
```

### Ngrok Not Connecting

**Check logs:**
```bash
sudo journalctl -u vani-ngrok -n 50
```

**Common issues:**
- Flask not running (ngrok needs Flask to be up)
- Invalid authtoken
- Domain not reserved in ngrok dashboard
- Network connectivity issues

**Solution:**
```bash
# Verify Flask is running
curl http://127.0.0.1:5000

# Test ngrok manually
ngrok http 5000 --domain=vani.ngrok.app

# Check ngrok config
cat ~/.config/ngrok/ngrok.yml
```

### 502 Bad Gateway

**Cause**: Ngrok is running but Flask is not responding

**Solution:**
```bash
# Check Flask status
sudo systemctl status vani-flask

# Check Flask logs
sudo journalctl -u vani-flask -f

# Restart Flask
sudo systemctl restart vani-flask
```

### Database Connection Errors

**Check Supabase settings:**
```bash
# Test connection
cd /opt/vani
source venv/bin/activate
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv('.env.local'); client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('✅ Connected')"
```

**Solution:**
- Verify `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY` in `.env.local`
- Check Supabase project is not paused
- Run database migrations

### Webhooks Not Working

**Test webhook endpoint:**
```bash
curl -X POST https://vani.ngrok.app/api/webhooks/resend \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

**Check ngrok dashboard:**
- Forward port: `ssh -L 4040:localhost:4040 USER@VM_IP`
- Open: http://localhost:4040
- View incoming requests

---

## Security Best Practices

### 1. Firewall Configuration
```bash
# Only allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Secure Environment Variables
```bash
# Set proper permissions
chmod 600 /opt/vani/.env.local

# Never commit .env.local to git
echo ".env.local" >> /opt/vani/.gitignore
```

### 3. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /opt/vani
source venv/bin/activate
pip install --upgrade pip
pip list --outdated
```

### 4. Monitoring
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/vani
```

Add:
```
/opt/vani/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0640 YOUR_USER YOUR_USER
}
```

### 5. Backup
```bash
# Backup .env.local securely
scp user@vm:/opt/vani/.env.local ./vani-env-backup-$(date +%Y%m%d).local

# Database is backed up by Supabase automatically
```

---

## Production Checklist

- [ ] VM created with appropriate specs (e2-medium minimum)
- [ ] Python 3.11+ installed
- [ ] Ngrok installed and configured with authtoken
- [ ] Static domain `vani.ngrok.app` reserved in ngrok dashboard
- [ ] All dependencies installed in virtual environment
- [ ] `.env.local` configured with all required variables
- [ ] Database migrations completed
- [ ] Super user created
- [ ] systemd services created and enabled
- [ ] Flask service running and accessible locally
- [ ] Ngrok service running with tunnel established
- [ ] Public URL `https://vani.ngrok.app` accessible
- [ ] Webhooks configured in Resend, Twilio, Cal.com
- [ ] Login page accessible
- [ ] Command Center accessible
- [ ] Email/WhatsApp/LinkedIn integrations tested
- [ ] Firewall configured
- [ ] Logs rotating properly
- [ ] Monitoring set up
- [ ] Backups configured

---

## Quick Commands Reference

```bash
# SSH to VM
gcloud compute ssh vani-server --zone=us-central1-a

# View logs
sudo journalctl -u vani-flask -u vani-ngrok -f

# Restart services
sudo systemctl restart vani-flask vani-ngrok

# Check status
sudo systemctl status vani-flask vani-ngrok

# Update app
cd /opt/vani && git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart vani-flask

# Test endpoints
curl https://vani.ngrok.app/api/health

# View ngrok tunnels
curl http://localhost:4040/api/tunnels | python3 -m json.tool
```

---

## Support & Resources

- **Ngrok Documentation**: https://ngrok.com/docs
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Supabase Documentation**: https://supabase.com/docs
- **GCP Documentation**: https://cloud.google.com/compute/docs

## Next Steps

After deployment:
1. Configure your domain (optional): Point your custom domain to ngrok
2. Set up monitoring: Use GCP Cloud Monitoring or third-party tools
3. Configure backups: Automate `.env.local` backups
4. SSL Certificates: Ngrok provides HTTPS automatically
5. Scale: Upgrade VM instance as needed

---

**✅ Deployment Complete!**

Your VANI application should now be:
- Running on Google VM
- Accessible at https://vani.ngrok.app
- Ready to receive webhooks
- Auto-starting on system boot
- Logging to systemd journal

For issues, check the logs first:
```bash
sudo journalctl -u vani-flask -u vani-ngrok -f
```

