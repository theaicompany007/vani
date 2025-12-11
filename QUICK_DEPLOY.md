# VANI - Quick Deployment Guide for Google VM

This is a **quick start guide** for deploying VANI on Google VM. For detailed instructions, see [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md).

## Prerequisites

- [ ] Google Cloud account with billing enabled
- [ ] Ngrok account with authtoken
- [ ] Static domain `vani.ngrok.app` reserved in ngrok dashboard
- [ ] All API keys ready (Supabase, OpenAI, Resend, Twilio, etc.)

---

## Part 1: Create VM (5 minutes)

### Option A: Using GCP Console (Recommended for beginners)

1. Go to: https://console.cloud.google.com/compute/instances
2. Click **CREATE INSTANCE**
3. Set:
   - Name: `vani-server`
   - Region: `us-central1` (or closest)
   - Machine type: `e2-medium`
   - Boot disk: Ubuntu 22.04 LTS, 20GB
   - Firewall: ✅ Allow HTTP and HTTPS
4. Click **CREATE**
5. Wait 1-2 minutes for VM to start

### Option B: Using gcloud CLI

```bash
gcloud compute instances create vani-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server
```

---

## Part 2: Setup VM Environment (10 minutes)

### Step 1: SSH to VM

**Console**: Click **SSH** button next to your VM

**CLI**:
```bash
gcloud compute ssh vani-server --zone=us-central1-a
```

### Step 2: Run Setup Script

On the VM, run:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/vani/main/scripts/setup_vm.sh -o setup_vm.sh
chmod +x setup_vm.sh
./setup_vm.sh
```

Or if you have the script locally:

```bash
cd /tmp
nano setup_vm.sh  # Paste the script content
chmod +x setup_vm.sh
./setup_vm.sh
```

This script will:
- Install Python 3.11
- Install ngrok
- Configure ngrok with your authtoken
- Create application directory
- Setup systemd services
- Create `.env.local` template

**When prompted**: Enter your ngrok authtoken from https://dashboard.ngrok.com/get-started/your-authtoken

---

## Part 3: Deploy Application (10 minutes)

### Option A: Deploy from Local Machine (Recommended)

On your **local machine** (not VM):

```bash
cd /path/to/vani
chmod +x scripts/deploy_to_vm.sh
./scripts/deploy_to_vm.sh YOUR_VM_IP
```

Replace `YOUR_VM_IP` with your VM's external IP (find it in GCP Console).

### Option B: Manual Deployment

On the **VM**:

```bash
# Clone repository
cd /opt/vani
git clone https://github.com/YOUR_USERNAME/vani.git .

# Or upload files via SCP from local machine:
# scp -r vani/* USER@VM_IP:/opt/vani/

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Part 4: Configure Environment (5 minutes)

On the **VM**, edit environment file:

```bash
nano /opt/vani/.env.local
```

Update these critical values:

```bash
# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Ngrok (REQUIRED)
NGROK_AUTHTOKEN=your-ngrok-authtoken
NGROK_DOMAIN=vani.ngrok.app
WEBHOOK_BASE_URL=https://vani.ngrok.app

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-your-key

# Resend (REQUIRED for email)
RESEND_API_KEY=re_your_key
RESEND_FROM_EMAIL=noreply@yourdomain.com

# Twilio (REQUIRED for WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_WHATSAPP_NUMBER=+14155238886

# Flask
SECRET_KEY=generate-a-random-secret-key-here
DEBUG=False
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

Set permissions:
```bash
chmod 600 /opt/vani/.env.local
```

---

## Part 5: Setup Database (5 minutes)

### Option A: Using Supabase SQL Editor (Recommended)

1. Go to your Supabase project
2. Click **SQL Editor**
3. Copy content from `/opt/vani/COMPLETE_SETUP.sql`
4. Paste and click **Run**

### Option B: Using Script

On the **VM**:

```bash
cd /opt/vani
source venv/bin/activate
python do_setup.py
```

---

## Part 6: Install Services (2 minutes)

On the **VM**:

```bash
cd /opt/vani/deployment
chmod +x install_services.sh
./install_services.sh
```

This will install and enable systemd services.

---

## Part 7: Start Services (2 minutes)

```bash
# Start Flask
sudo systemctl start vani-flask

# Wait 10 seconds
sleep 10

# Start ngrok
sudo systemctl start vani-ngrok

# Check status
sudo systemctl status vani-flask vani-ngrok
```

Expected output: Both services should show **active (running)** in green.

---

## Part 8: Verify Deployment (2 minutes)

```bash
cd /opt/vani/scripts
chmod +x verify_deployment.sh
./verify_deployment.sh
```

This will check:
- ✅ Python and ngrok installed
- ✅ Application files present
- ✅ Virtual environment configured
- ✅ Services running
- ✅ Flask responding
- ✅ Ngrok tunnel active
- ✅ Public URL accessible

---

## Part 9: Access Application

**Public URL**: https://vani.ngrok.app

**Login Page**: https://vani.ngrok.app/login

**Command Center**: https://vani.ngrok.app/command-center

---

## Part 10: Create Super User

### Method 1: Via Supabase Dashboard

1. Go to: https://vani.ngrok.app/login
2. Click "Sign up" and create your account
3. Go to Supabase → Authentication → Users
4. Copy your User ID
5. Go to SQL Editor and run:

```sql
UPDATE app_users 
SET is_super_user = true 
WHERE supabase_user_id = 'YOUR_USER_ID_HERE';
```

### Method 2: Using Script

On the **VM**:

```bash
cd /opt/vani
source venv/bin/activate
python create_super_user.py
```

---

## Useful Commands

### View Logs
```bash
# Flask logs
sudo journalctl -u vani-flask -f

# Ngrok logs
sudo journalctl -u vani-ngrok -f

# Both
sudo journalctl -u vani-flask -u vani-ngrok -f
```

### Restart Services
```bash
sudo systemctl restart vani-flask vani-ngrok
```

### Stop Services
```bash
sudo systemctl stop vani-flask vani-ngrok
```

### Check Ngrok URL
```bash
curl http://localhost:4040/api/tunnels | python3 -m json.tool
```

### Test Local Flask
```bash
curl http://127.0.0.1:5000
```

### Update Application
```bash
cd /opt/vani
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vani-flask vani-ngrok
```

---

## Troubleshooting

### Flask Not Starting

**Check logs**:
```bash
sudo journalctl -u vani-flask -n 50
```

**Common fixes**:
```bash
# Check .env.local
cat /opt/vani/.env.local

# Reinstall dependencies
cd /opt/vani
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Check if port in use
sudo lsof -i :5000

# Restart service
sudo systemctl restart vani-flask
```

### Ngrok Not Connecting

**Check logs**:
```bash
sudo journalctl -u vani-ngrok -n 50
```

**Common fixes**:
```bash
# Verify authtoken
cat ~/.config/ngrok/ngrok.yml

# Test manually
ngrok http 5000 --domain=vani.ngrok.app

# Restart service
sudo systemctl restart vani-ngrok
```

### Can't Access Public URL

**Check**:
```bash
# Is Flask running?
curl http://127.0.0.1:5000

# Is ngrok running?
curl http://localhost:4040/api/tunnels

# Get public URL
curl http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

### Database Connection Error

**Verify Supabase credentials**:
```bash
cd /opt/vani
source venv/bin/activate

python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('.env.local')
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('✅ Supabase connection successful')
"
```

---

## Next Steps

After deployment:

1. **Configure Webhooks**: Update webhook URLs in Resend, Twilio, Cal.com dashboards
2. **Import Targets**: Use Google Sheets integration to import target companies
3. **Customize Templates**: Update email/WhatsApp templates in Settings
4. **Test Outreach**: Send test messages via Command Center
5. **Monitor**: Check Dashboard for analytics

---

## Getting Help

**View all logs**:
```bash
sudo journalctl -u vani-flask -u vani-ngrok --since "1 hour ago"
```

**Check system resources**:
```bash
htop
df -h
```

**Re-run verification**:
```bash
cd /opt/vani/scripts
./verify_deployment.sh
```

**For detailed help**: See [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md)

---

## Summary Checklist

- [ ] VM created on Google Cloud
- [ ] SSH access working
- [ ] Setup script completed
- [ ] Application deployed
- [ ] Environment configured
- [ ] Database migrated
- [ ] Services installed
- [ ] Services started and running
- [ ] Verification passed
- [ ] Public URL accessible
- [ ] Super user created
- [ ] Webhooks configured

---

**🎉 Congratulations!**

Your VANI application is now deployed and accessible at:

**https://vani.ngrok.app**

---

**Total Time**: ~45 minutes

**Estimated Costs**:
- Google VM (e2-medium): ~$25/month
- Ngrok static domain: Free tier or $8/month
- Supabase: Free tier (up to 500MB)

---

## Support Files

- **Detailed Guide**: [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md)
- **Setup Script**: [scripts/setup_vm.sh](scripts/setup_vm.sh)
- **Deploy Script**: [scripts/deploy_to_vm.sh](scripts/deploy_to_vm.sh)
- **Verify Script**: [scripts/verify_deployment.sh](scripts/verify_deployment.sh)
- **Flask Service**: [deployment/vani-flask.service](deployment/vani-flask.service)
- **Ngrok Service**: [deployment/vani-ngrok.service](deployment/vani-ngrok.service)

