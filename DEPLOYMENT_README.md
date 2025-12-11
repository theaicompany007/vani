# VANI Deployment Resources

This document provides an overview of all deployment resources available for deploying Project VANI on Google Cloud VM with ngrok.

## Quick Navigation

### 🚀 Getting Started

- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Fast track deployment guide (~45 minutes)
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist to track progress

### 📚 Comprehensive Documentation

- **[GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md)** - Complete deployment guide with detailed explanations
- **[NGROK_SETUP.md](NGROK_SETUP.md)** - Ngrok configuration and troubleshooting
- **[deployment/README.md](deployment/README.md)** - Service files documentation

## Deployment Approach

Choose your approach based on experience level:

### 1. Express Deployment (Recommended for Beginners)

**Time**: ~45 minutes  
**Difficulty**: Easy  
**Prerequisites**: Basic terminal knowledge

**Steps**:
1. Read [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
2. Follow step-by-step instructions
3. Use deployment scripts
4. Run verification script

**Best for**: First-time deployments, quick setup

---

### 2. Detailed Deployment (Recommended for Production)

**Time**: ~2 hours  
**Difficulty**: Moderate  
**Prerequisites**: Understanding of Linux, systemd, networking

**Steps**:
1. Read [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md) thoroughly
2. Follow all steps manually
3. Configure security features
4. Set up monitoring

**Best for**: Production deployments, learning the system

---

### 3. Automated Deployment (Recommended for Multiple Deployments)

**Time**: ~30 minutes  
**Difficulty**: Easy  
**Prerequisites**: SSH access, deployment scripts

**Steps**:
1. Run `scripts/setup_vm.sh` on VM
2. Run `scripts/deploy_to_vm.sh` from local machine
3. Configure `.env.local` on VM
4. Run `deployment/install_services.sh`
5. Start services

**Best for**: Updating existing deployments, multiple environments

---

## Files and Scripts Overview

### Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `QUICK_DEPLOY.md` | Fast deployment guide | First deployment, need to get running quickly |
| `GOOGLE_VM_DEPLOYMENT.md` | Comprehensive guide | Production deployment, detailed understanding |
| `DEPLOYMENT_CHECKLIST.md` | Progress tracking | Any deployment, ensures nothing is missed |
| `NGROK_SETUP.md` | Ngrok configuration | Ngrok issues, webhook setup |
| `DEPLOYMENT_README.md` | This file | Overview and navigation |
| `deployment/README.md` | Service files docs | Service configuration, troubleshooting |

### Deployment Scripts

| Script | Location | Purpose | Run On |
|--------|----------|---------|--------|
| `setup_vm.sh` | `scripts/` | Initial VM setup | VM |
| `deploy_to_vm.sh` | `scripts/` | Deploy from local to VM | Local Machine |
| `verify_deployment.sh` | `scripts/` | Verify deployment | VM |
| `install_services.sh` | `deployment/` | Install systemd services | VM |

### Service Files

| File | Location | Purpose |
|------|----------|---------|
| `vani-flask.service` | `deployment/` | Flask app systemd service |
| `vani-ngrok.service` | `deployment/` | Ngrok tunnel systemd service |

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `.env.local` | Application environment variables | `/opt/vani/.env.local` |
| `ngrok.yml` | Ngrok configuration | `~/.config/ngrok/ngrok.yml` |

---

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│         Google Cloud Platform               │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │   VM: vani-server (Ubuntu 22.04)     │ │
│  │                                       │ │
│  │   ┌─────────────────────────────┐   │ │
│  │   │  Flask App (Port 5000)      │   │ │
│  │   │  - Python 3.11              │   │ │
│  │   │  - Managed by systemd       │   │ │
│  │   └─────────────┬───────────────┘   │ │
│  │                 │                     │ │
│  │                 ↓                     │ │
│  │   ┌─────────────────────────────┐   │ │
│  │   │  Ngrok Tunnel               │   │ │
│  │   │  - Static domain            │   │ │
│  │   │  - Managed by systemd       │   │ │
│  │   └─────────────┬───────────────┘   │ │
│  └─────────────────┼───────────────────┘ │
│                    │                       │
└────────────────────┼───────────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │  vani.ngrok.app       │
         │  (Public Access)      │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ↓                       ↓
   ┌─────────┐           ┌─────────────┐
   │ Users   │           │ Webhooks    │
   │ Browser │           │ (Resend,    │
   └─────────┘           │  Twilio)    │
                         └─────────────┘

External Services:
├── Supabase (Database & Auth)
├── OpenAI (AI Generation)
├── Resend (Email)
├── Twilio (WhatsApp)
└── Cal.com (Meetings)
```

---

## Prerequisites

### Accounts & Services

- ✅ Google Cloud Platform account (with billing)
- ✅ Ngrok account with static domain reserved
- ✅ Supabase project created
- ✅ OpenAI API key
- ✅ Resend API key
- ✅ Twilio account with WhatsApp enabled

### API Keys Required

| Service | Key/Credential | Where to Get |
|---------|---------------|--------------|
| Supabase | URL, Anon Key, Service Key | https://supabase.com/dashboard |
| Ngrok | Authtoken | https://dashboard.ngrok.com/get-started/your-authtoken |
| OpenAI | API Key | https://platform.openai.com/api-keys |
| Resend | API Key | https://resend.com/api-keys |
| Twilio | Account SID, Auth Token | https://console.twilio.com/ |
| Cal.com | API Key (optional) | https://app.cal.com/settings/developer |

---

## Deployment Flow

### Standard Deployment Process

```
1. CREATE VM
   ├── Google Cloud Console or gcloud CLI
   └── Ubuntu 22.04 LTS, e2-medium, 20GB

2. SETUP ENVIRONMENT
   ├── SSH to VM
   ├── Run setup_vm.sh
   │   ├── Install Python 3.11
   │   ├── Install ngrok
   │   ├── Configure ngrok
   │   └── Create app directory
   └── Verify setup

3. DEPLOY APPLICATION
   ├── Option A: Use deploy_to_vm.sh from local machine
   └── Option B: Manual git clone and setup
       ├── Clone repository
       ├── Create virtual environment
       └── Install dependencies

4. CONFIGURE
   ├── Create .env.local
   ├── Add all API keys and credentials
   └── Set file permissions (chmod 600)

5. SETUP DATABASE
   ├── Run COMPLETE_SETUP.sql in Supabase
   └── Verify tables created

6. INSTALL SERVICES
   ├── Run install_services.sh
   ├── systemd services created
   └── Services enabled

7. START SERVICES
   ├── Start vani-flask
   ├── Wait 10 seconds
   └── Start vani-ngrok

8. VERIFY
   ├── Run verify_deployment.sh
   ├── Check all endpoints
   └── Test features

9. POST-DEPLOYMENT
   ├── Create super user
   ├── Configure webhooks
   └── Test end-to-end
```

---

## Common Tasks

### First Deployment

1. Read [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
2. Print [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
3. Gather all API keys
4. Follow guide step-by-step
5. Check off items in checklist
6. Run verification script

### Update Existing Deployment

```bash
# From local machine
./scripts/deploy_to_vm.sh YOUR_VM_IP

# Or manually on VM
cd /opt/vani
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vani-flask vani-ngrok
```

### Troubleshooting

1. Check service status
   ```bash
   sudo systemctl status vani-flask vani-ngrok
   ```

2. View logs
   ```bash
   sudo journalctl -u vani-flask -u vani-ngrok -f
   ```

3. Run verification
   ```bash
   cd /opt/vani/scripts
   ./verify_deployment.sh
   ```

4. Check detailed guide: [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md#troubleshooting)

---

## Support Matrix

| Issue Type | Resource |
|------------|----------|
| General deployment | `GOOGLE_VM_DEPLOYMENT.md` |
| Quick reference | `QUICK_DEPLOY.md` |
| Ngrok issues | `NGROK_SETUP.md` |
| Service management | `deployment/README.md` |
| Step tracking | `DEPLOYMENT_CHECKLIST.md` |
| Verification | `scripts/verify_deployment.sh` |

---

## Best Practices

### Security

- ✅ Use strong passwords for all services
- ✅ Keep `.env.local` with mode 600
- ✅ Enable firewall (allow only necessary ports)
- ✅ Use SSH keys (disable password auth)
- ✅ Regularly update system packages
- ✅ Monitor logs for suspicious activity
- ✅ Backup `.env.local` securely

### Monitoring

- ✅ Set up log monitoring
- ✅ Monitor disk space
- ✅ Check service status regularly
- ✅ Set up alerts for service failures
- ✅ Monitor ngrok tunnel uptime
- ✅ Track resource usage (CPU, memory)

### Maintenance

- ✅ Regular updates to application code
- ✅ Update Python dependencies periodically
- ✅ Rotate logs to prevent disk full
- ✅ Review and clean old data
- ✅ Test backups regularly
- ✅ Document any custom changes

---

## Costs Estimate

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Google VM (e2-medium) | Always On | ~$25 |
| Ngrok Static Domain | Pro Plan | $8 |
| Supabase | Free/Pro | $0-$25 |
| **Total** | | **~$33-58** |

*Additional costs*:
- OpenAI API usage (pay-as-you-go)
- Resend emails (pay-as-you-go)
- Twilio WhatsApp (pay-as-you-go)

---

## Frequently Asked Questions

### Can I use a different cloud provider?

Yes, the deployment process is similar for AWS, Azure, DigitalOcean, etc. The main difference is VM creation. All other steps remain the same.

### Do I need a static ngrok domain?

Highly recommended. Free ngrok URLs change on restart. Static domains require a paid plan ($8/month) but provide stability for webhooks.

### Can I run without ngrok?

Yes, but you'll need to configure a reverse proxy (nginx) and SSL certificates. Ngrok is simpler for getting started.

### What if my deployment fails?

1. Check the troubleshooting section in guides
2. Run verification script
3. Review logs: `sudo journalctl -u vani-flask -u vani-ngrok -f`
4. Check [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for missed steps

### How do I add more users?

Super users can manage users via the Admin Panel in the application, or users can sign up and be approved.

### Can I change the domain?

Yes, reserve a different domain in ngrok dashboard and update `NGROK_DOMAIN` and `WEBHOOK_BASE_URL` in `.env.local` and `ngrok.yml`.

---

## Getting Help

### Quick Fixes

Check [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md#troubleshooting) for common issues and solutions.

### Debugging Steps

1. **Service not starting**: Check logs with `sudo journalctl -u SERVICE_NAME -n 50`
2. **Can't access URL**: Verify ngrok tunnel with `curl http://localhost:4040/api/tunnels`
3. **Database errors**: Verify Supabase credentials in `.env.local`
4. **Webhooks failing**: Check webhook URLs and ngrok tunnel stability

### Useful Commands

```bash
# Full system status
sudo systemctl status vani-flask vani-ngrok
curl http://127.0.0.1:5000
curl http://localhost:4040/api/tunnels

# Restart everything
sudo systemctl restart vani-flask vani-ngrok

# View all logs
sudo journalctl -u vani-flask -u vani-ngrok --since "1 hour ago"

# Check resources
htop
df -h

# Re-verify deployment
cd /opt/vani/scripts && ./verify_deployment.sh
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial deployment documentation |

---

## Contributing

Found an issue or have improvements? Update the documentation and commit changes.

---

## License

Project VANI - Internal Documentation

---

**Ready to deploy?**

Start with [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for a fast deployment, or [GOOGLE_VM_DEPLOYMENT.md](GOOGLE_VM_DEPLOYMENT.md) for detailed instructions.

**Good luck! 🚀**

