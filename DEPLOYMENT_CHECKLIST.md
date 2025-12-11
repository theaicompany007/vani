# VANI Deployment Checklist

Use this checklist to track your deployment progress.

## Pre-Deployment (Before You Start)

- [ ] Google Cloud account created and billing enabled
- [ ] Ngrok account created at https://ngrok.com
- [ ] Ngrok authtoken obtained from https://dashboard.ngrok.com/get-started/your-authtoken
- [ ] Static domain `vani.ngrok.app` reserved in ngrok dashboard
- [ ] Supabase project created at https://supabase.com
- [ ] Supabase credentials ready (URL, Anon Key, Service Key)
- [ ] OpenAI API key obtained
- [ ] Resend API key obtained (for email)
- [ ] Twilio credentials obtained (for WhatsApp)
- [ ] Cal.com API key obtained (optional, for meetings)

## Phase 1: VM Creation (5 minutes)

- [ ] Google VM instance created
  - [ ] Name: `vani-server`
  - [ ] Machine type: `e2-medium` or better
  - [ ] Boot disk: Ubuntu 22.04 LTS, 20GB minimum
  - [ ] Firewall: HTTP and HTTPS allowed
- [ ] VM is running (green checkmark in GCP Console)
- [ ] External IP address noted: ________________
- [ ] Can SSH to VM successfully

## Phase 2: VM Environment Setup (10 minutes)

- [ ] Connected to VM via SSH
- [ ] System packages updated (`sudo apt update && upgrade`)
- [ ] Python 3.11 installed
  - [ ] Verified: `python3.11 --version`
- [ ] Ngrok installed
  - [ ] Verified: `ngrok version`
- [ ] System dependencies installed (git, build-essential, etc.)
- [ ] Ngrok configured with authtoken
  - [ ] Config file exists: `~/.config/ngrok/ngrok.yml`
  - [ ] Static domain configured: `vani.ngrok.app`
- [ ] Application directory created: `/opt/vani`
- [ ] Directory ownership set to current user

## Phase 3: Application Deployment (10 minutes)

- [ ] Application files uploaded/cloned to `/opt/vani`
  - [ ] Method used: ☐ Deploy script ☐ Git clone ☐ Manual upload
- [ ] Python virtual environment created
  - [ ] Path: `/opt/vani/venv`
  - [ ] Verified: `ls /opt/vani/venv/bin/python`
- [ ] Python dependencies installed
  - [ ] Verified Flask: `venv/bin/python -c "import flask"`
  - [ ] Verified Supabase: `venv/bin/python -c "import supabase"`
- [ ] All required files present:
  - [ ] `run.py`
  - [ ] `requirements.txt`
  - [ ] `app/` directory
  - [ ] `scripts/` directory
  - [ ] `COMPLETE_SETUP.sql`

## Phase 4: Configuration (5 minutes)

- [ ] `.env.local` file created at `/opt/vani/.env.local`
- [ ] File permissions set: `chmod 600 .env.local`
- [ ] All required variables configured:
  - [ ] `FLASK_HOST=127.0.0.1`
  - [ ] `FLASK_PORT=5000`
  - [ ] `DEBUG=False`
  - [ ] `SECRET_KEY` (random string)
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `SUPABASE_SERVICE_KEY`
  - [ ] `NGROK_AUTHTOKEN`
  - [ ] `NGROK_DOMAIN=vani.ngrok.app`
  - [ ] `WEBHOOK_BASE_URL=https://vani.ngrok.app`
  - [ ] `OPENAI_API_KEY`
  - [ ] `RESEND_API_KEY`
  - [ ] `TWILIO_ACCOUNT_SID`
  - [ ] `TWILIO_AUTH_TOKEN`
  - [ ] `TWILIO_WHATSAPP_NUMBER`

## Phase 5: Database Setup (5 minutes)

- [ ] Database migrations completed
  - [ ] Method: ☐ Supabase SQL Editor ☐ Script (`do_setup.py`)
- [ ] Tables created successfully:
  - [ ] `industries`
  - [ ] `use_cases`
  - [ ] `app_users`
  - [ ] `targets`
  - [ ] `outreach_activities`
  - [ ] `generated_pitches`
  - [ ] `meetings`
  - [ ] `webhook_events`
  - [ ] `user_permissions`
- [ ] Default data seeded (industries, use cases)
- [ ] Database connection tested successfully

## Phase 6: Services Installation (2 minutes)

- [ ] Systemd service files installed
  - [ ] Method: ☐ Install script ☐ Manual
  - [ ] Flask service: `/etc/systemd/system/vani-flask.service`
  - [ ] Ngrok service: `/etc/systemd/system/vani-ngrok.service`
- [ ] Username updated in service files
- [ ] Systemd daemon reloaded
- [ ] Services enabled for auto-start on boot
  - [ ] `systemctl enable vani-flask`
  - [ ] `systemctl enable vani-ngrok`

## Phase 7: Start Services (2 minutes)

- [ ] Flask service started
  - [ ] Command: `sudo systemctl start vani-flask`
  - [ ] Status: `sudo systemctl status vani-flask` shows active (running)
- [ ] Waited 10 seconds for Flask to initialize
- [ ] Ngrok service started
  - [ ] Command: `sudo systemctl start vani-ngrok`
  - [ ] Status: `sudo systemctl status vani-ngrok` shows active (running)
- [ ] No errors in service logs
  - [ ] Flask logs clean: `sudo journalctl -u vani-flask -n 20`
  - [ ] Ngrok logs clean: `sudo journalctl -u vani-ngrok -n 20`

## Phase 8: Verification (2 minutes)

- [ ] Flask responding locally
  - [ ] Test: `curl http://127.0.0.1:5000`
  - [ ] Returns HTML or redirects (not connection refused)
- [ ] Ngrok tunnel active
  - [ ] Test: `curl http://localhost:4040/api/tunnels`
  - [ ] Shows tunnel information with public_url
- [ ] Public URL accessible
  - [ ] URL: https://vani.ngrok.app
  - [ ] Test from browser or: `curl https://vani.ngrok.app`
  - [ ] Page loads successfully
- [ ] Verification script passed
  - [ ] Run: `scripts/verify_deployment.sh`
  - [ ] All checks passed with 0 errors

## Phase 9: Application Setup (5 minutes)

- [ ] Login page accessible: https://vani.ngrok.app/login
- [ ] First user account created
  - [ ] Email: ________________
  - [ ] Password: ________________ (store securely!)
- [ ] User promoted to super user
  - [ ] Supabase User ID obtained
  - [ ] SQL executed to set `is_super_user = true`
- [ ] Can login successfully
- [ ] Command Center accessible: https://vani.ngrok.app/command-center
- [ ] Dashboard loads: https://vani.ngrok.app/dashboard

## Phase 10: Webhook Configuration (5 minutes)

- [ ] Resend webhook configured
  - [ ] URL: https://vani.ngrok.app/api/webhooks/resend
  - [ ] Events selected: sent, delivered, bounced, opened, clicked
  - [ ] Test webhook sent successfully
- [ ] Twilio webhook configured
  - [ ] URL: https://vani.ngrok.app/api/webhooks/twilio
  - [ ] Set for incoming WhatsApp messages
  - [ ] Test message received
- [ ] Cal.com webhook configured (if using)
  - [ ] URL: https://vani.ngrok.app/api/webhooks/cal-com
  - [ ] Events: BOOKING_CREATED, BOOKING_CANCELLED

## Phase 11: Feature Testing (10 minutes)

- [ ] Target management tested
  - [ ] Can add new target
  - [ ] Can edit target
  - [ ] Can delete target
  - [ ] Targets display in list
- [ ] Email outreach tested
  - [ ] AI message generation works
  - [ ] Test email sent successfully
  - [ ] Email appears in Resend dashboard
- [ ] WhatsApp outreach tested
  - [ ] Test WhatsApp message sent
  - [ ] Message appears in Twilio logs
- [ ] LinkedIn integration available (if applicable)
- [ ] Pitch generation tested
  - [ ] Can generate pitch for target
  - [ ] Pitch displays correctly
- [ ] Dashboard displays metrics
  - [ ] Shows target count
  - [ ] Shows activity count
  - [ ] Charts render

## Phase 12: Production Readiness (10 minutes)

- [ ] Security configured
  - [ ] `.env.local` is mode 600 (only user readable)
  - [ ] Firewall configured (optional: only allow 80, 443, SSH)
  - [ ] SSH key-based auth enabled (optional)
- [ ] Monitoring set up
  - [ ] Log rotation configured
  - [ ] Disk space monitoring enabled
  - [ ] Service health checks set up
- [ ] Backup strategy in place
  - [ ] `.env.local` backed up securely
  - [ ] Supabase backups enabled (automatic)
  - [ ] Code in git repository
- [ ] Documentation reviewed
  - [ ] Team has access to deployment docs
  - [ ] Credentials stored in password manager
  - [ ] Runbook created for common operations

## Post-Deployment Operations

- [ ] Application URL shared with team
- [ ] User accounts created for team members
- [ ] Permissions configured per user
- [ ] Initial targets imported
- [ ] Templates customized
- [ ] First outreach campaign launched

## Common Commands Reference

```bash
# View logs
sudo journalctl -u vani-flask -u vani-ngrok -f

# Restart services
sudo systemctl restart vani-flask vani-ngrok

# Check status
sudo systemctl status vani-flask vani-ngrok

# Update application
cd /opt/vani && git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart vani-flask

# Get ngrok URL
curl http://localhost:4040/api/tunnels | python3 -m json.tool

# Test Flask locally
curl http://127.0.0.1:5000

# View recent errors
sudo journalctl -u vani-flask -p err -n 50

# Check disk space
df -h /opt/vani

# Monitor resources
htop
```

## Troubleshooting Checklist

If something doesn't work:

- [ ] Check service status: `sudo systemctl status vani-flask vani-ngrok`
- [ ] View logs: `sudo journalctl -u vani-flask -u vani-ngrok -n 100`
- [ ] Verify .env.local: `cat /opt/vani/.env.local | grep -v API_KEY`
- [ ] Test Flask locally: `curl http://127.0.0.1:5000`
- [ ] Test ngrok API: `curl http://localhost:4040/api/tunnels`
- [ ] Check port 5000: `sudo lsof -i :5000`
- [ ] Verify venv: `ls /opt/vani/venv/bin/python`
- [ ] Run verification: `./scripts/verify_deployment.sh`
- [ ] Check Supabase: Visit dashboard and verify project is active
- [ ] Check ngrok dashboard: https://dashboard.ngrok.com/
- [ ] Review deployment guide: `GOOGLE_VM_DEPLOYMENT.md`

## Success Criteria

Your deployment is successful when:

- ✅ All services show "active (running)"
- ✅ Public URL https://vani.ngrok.app is accessible
- ✅ Login page loads
- ✅ Can create and login with user account
- ✅ Command Center is accessible
- ✅ Dashboard displays correctly
- ✅ Can create targets
- ✅ Can send test messages
- ✅ Webhooks are receiving events
- ✅ No errors in service logs
- ✅ Verification script passes

## Deployment Time Estimate

- **Minimum**: ~45 minutes (experienced user, no issues)
- **Average**: ~1-2 hours (first-time deployment)
- **Maximum**: ~3 hours (troubleshooting required)

## Support Resources

- **Detailed Guide**: `GOOGLE_VM_DEPLOYMENT.md`
- **Quick Start**: `QUICK_DEPLOY.md`
- **Verification Script**: `scripts/verify_deployment.sh`
- **Deploy Script**: `scripts/deploy_to_vm.sh`
- **Service Files**: `deployment/`

---

**Date Deployed**: _______________

**Deployed By**: _______________

**VM IP Address**: _______________

**Ngrok URL**: https://vani.ngrok.app

**Super User Email**: _______________

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________

---

**Deployment Status**: ☐ In Progress ☐ Complete ☐ Failed

**If failed, reason**: _________________________

