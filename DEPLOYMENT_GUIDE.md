# Project VANI - Google VM Deployment Guide with ngrok

## Overview
This guide covers deploying Project VANI on Google Cloud VM with ngrok static domain for public access.

## Prerequisites
- Google Cloud Platform account
- ngrok account with static domain (e.g., `vani.ngrok.app`)
- Supabase project configured
- All API keys and credentials ready

## Step 1: Create Google Cloud VM

### 1.1 Create VM Instance
```bash
# Using gcloud CLI
gcloud compute instances create vani-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server
```

### 1.2 Configure Firewall
```bash
# Allow HTTP/HTTPS traffic
gcloud compute firewall-rules create allow-http-https \
  --allow tcp:80,tcp:443,tcp:5000 \
  --source-ranges 0.0.0.0/0 \
  --target-tags http-server,https-server
```

## Step 2: Setup VM Environment

### 2.1 SSH into VM
```bash
gcloud compute ssh vani-server --zone=us-central1-a
```

### 2.2 Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok -y
```

### 2.3 Configure ngrok
```bash
# Authenticate ngrok
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN

# Configure static domain
ngrok config edit
# Add:
# tunnels:
#   vani:
#     proto: http
#     addr: 5000
#     domain: vani.ngrok.app
```

## Step 3: Deploy Application

### 3.1 Clone Repository
```bash
cd /opt
sudo git clone YOUR_REPO_URL vani
sudo chown -R $USER:$USER /opt/vani
cd /opt/vani
```

### 3.2 Setup Python Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Configure Environment
```bash
# Copy and edit .env.local
cp .env.example .env.local
nano .env.local

# Ensure these are set:
# - SUPABASE_URL
# - SUPABASE_KEY
# - SUPABASE_SERVICE_KEY
# - SUPABASE_CONNECTION
# - SUPABASE_DB_PASSWORD
# - NGROK_AUTHTOKEN
# - NGROK_DOMAIN=vani.ngrok.app
# - WEBHOOK_BASE_URL=https://vani.ngrok.app
# - All API keys (Resend, Twilio, Cal.com, OpenAI, etc.)
```

### 3.4 Run Database Migrations
```bash
# Run all migrations in Supabase SQL Editor or via script
python scripts/create_database_tables_direct.py
```

## Step 4: Setup Systemd Service

### 4.1 Create Service File
```bash
sudo nano /etc/systemd/system/vani.service
```

Add:
```ini
[Unit]
Description=Project VANI Flask Application
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/opt/vani
Environment="PATH=/opt/vani/venv/bin"
ExecStart=/opt/vani/venv/bin/python /opt/vani/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.2 Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable vani
sudo systemctl start vani
sudo systemctl status vani
```

## Step 5: Setup ngrok Service

### 5.1 Create ngrok Service
```bash
sudo nano /etc/systemd/system/ngrok.service
```

Add:
```ini
[Unit]
Description=ngrok tunnel for VANI
After=network.target vani.service

[Service]
Type=simple
User=YOUR_USER
ExecStart=/usr/bin/ngrok start --all --config /home/YOUR_USER/.ngrok2/ngrok.yml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Start ngrok
```bash
sudo systemctl enable ngrok
sudo systemctl start ngrok
sudo systemctl status ngrok
```

## Step 6: Verify Deployment

### 6.1 Check Services
```bash
# Check Flask app
curl http://localhost:5000/api/health

# Check ngrok status
curl http://localhost:4040/api/tunnels

# Check public URL
curl https://vani.ngrok.app/api/health
```

### 6.2 Access Application
- Public URL: `https://vani.ngrok.app`
- Command Center: `https://vani.ngrok.app/command-center`
- Login: `https://vani.ngrok.app/login`

## Step 7: Configure Webhooks

Update webhook URLs in:
- Resend: `https://vani.ngrok.app/webhooks/resend`
- Twilio: `https://vani.ngrok.app/webhooks/twilio`
- Cal.com: `https://vani.ngrok.app/webhooks/cal-com`

Run:
```bash
python scripts/configure_webhooks.py
```

## Step 8: Initial Setup

### 8.1 Create Super User
1. Access Supabase Auth dashboard
2. Create first user account
3. In Supabase SQL Editor, run:
```sql
-- Update user to super user (replace SUPABASE_USER_ID)
UPDATE app_users 
SET is_super_user = true 
WHERE supabase_user_id = 'YOUR_SUPABASE_USER_ID';
```

### 8.2 Create Industries
```sql
-- Industries should already be seeded, but verify:
SELECT * FROM industries;
```

### 8.3 Grant Permissions
- Login as super user
- Access Admin Panel
- Grant use case permissions to users

## Troubleshooting

### Flask App Not Starting
```bash
# Check logs
sudo journalctl -u vani -f

# Check Python environment
source /opt/vani/venv/bin/activate
python -c "import flask; print(flask.__version__)"
```

### ngrok Not Connecting
```bash
# Check ngrok logs
sudo journalctl -u ngrok -f

# Test ngrok manually
ngrok http 5000 --domain=vani.ngrok.app
```

### Database Connection Issues
```bash
# Verify Supabase connection
python -c "from app.supabase_client import init_supabase; print('OK')"

# Check .env.local
cat .env.local | grep SUPABASE
```

## Security Considerations

1. **Firewall**: Only allow necessary ports
2. **HTTPS**: Use ngrok's HTTPS (included with static domain)
3. **Secrets**: Never commit `.env.local` to git
4. **Updates**: Regularly update system and dependencies
5. **Monitoring**: Set up monitoring for service health

## Backup Strategy

1. **Database**: Supabase handles backups automatically
2. **Code**: Use git repository
3. **Config**: Backup `.env.local` securely
4. **Logs**: Rotate logs regularly

## Maintenance

### Update Application
```bash
cd /opt/vani
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vani
```

### View Logs
```bash
# Application logs
sudo journalctl -u vani -f

# ngrok logs
sudo journalctl -u ngrok -f

# Application file logs
tail -f /opt/vani/logs/application.log
```

## Alternative: Using Public IP (No ngrok)

If you prefer using VM's public IP directly:

1. Reserve static IP:
```bash
gcloud compute addresses create vani-ip --region=us-central1
```

2. Assign to VM:
```bash
gcloud compute instances add-access-config vani-server \
  --access-config-name="External NAT" \
  --address=vani-ip
```

3. Update DNS to point domain to this IP
4. Setup SSL certificate (Let's Encrypt)
5. Configure nginx as reverse proxy

## Support

For issues:
1. Check application logs
2. Check ngrok status
3. Verify environment variables
4. Test database connection
5. Review Supabase dashboard

