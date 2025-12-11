# VANI Deployment Files

This directory contains systemd service files and deployment scripts for running VANI on Google VM.

## Files

### Systemd Service Files

- **`vani-flask.service`** - Systemd service for Flask application
- **`vani-ngrok.service`** - Systemd service for ngrok tunnel

### Scripts

- **`install_services.sh`** - Installs systemd service files

## Usage

### 1. Install Services

After deploying your application to `/opt/vani`:

```bash
cd /opt/vani/deployment
chmod +x install_services.sh
./install_services.sh
```

This will:
- Copy service files to `/etc/systemd/system/`
- Replace `YOUR_USERNAME` with current user
- Enable services to start on boot
- Reload systemd

### 2. Start Services

```bash
# Start Flask first
sudo systemctl start vani-flask

# Wait for Flask to be ready
sleep 10

# Start ngrok
sudo systemctl start vani-ngrok
```

### 3. Check Status

```bash
sudo systemctl status vani-flask
sudo systemctl status vani-ngrok
```

### 4. View Logs

```bash
# Flask logs
sudo journalctl -u vani-flask -f

# Ngrok logs
sudo journalctl -u vani-ngrok -f

# Both
sudo journalctl -u vani-flask -u vani-ngrok -f
```

### 5. Restart Services

```bash
sudo systemctl restart vani-flask
sudo systemctl restart vani-ngrok
```

### 6. Stop Services

```bash
sudo systemctl stop vani-flask
sudo systemctl stop vani-ngrok
```

### 7. Disable Services

```bash
sudo systemctl disable vani-flask
sudo systemctl disable vani-ngrok
```

## Service Details

### vani-flask.service

**Description**: Runs the Flask application using Gunicorn

**Configuration**:
- **WorkingDirectory**: `/opt/vani`
- **EnvironmentFile**: `/opt/vani/.env.local`
- **ExecStart**: `/opt/vani/venv/bin/python /opt/vani/run.py`
- **Restart**: Always (with 10s delay)
- **User**: Your username (auto-configured by install script)

**Dependencies**:
- Starts after network is available
- Required for ngrok service

**Security**:
- `NoNewPrivileges=true` - Cannot gain privileges
- `PrivateTmp=true` - Private /tmp directory
- `ProtectSystem=strict` - Read-only system files
- `ProtectHome=read-only` - Read-only home directory
- Write access only to `/opt/vani/logs` and `/opt/vani/data`

### vani-ngrok.service

**Description**: Creates ngrok tunnel to Flask application

**Configuration**:
- **ExecStart**: `/usr/local/bin/ngrok start vani --config ~/.config/ngrok/ngrok.yml`
- **Restart**: Always (with 10s delay)
- **User**: Your username (auto-configured by install script)

**Dependencies**:
- Requires `vani-flask.service` to be running
- Starts after network is online
- Waits 10s for Flask to be ready

**Features**:
- Uses static domain `vani.ngrok.app`
- Automatically reconnects if connection drops
- Logs to systemd journal

## Customization

### Change User

If you need to run services as a different user:

1. Edit service files:
   ```bash
   sudo nano /etc/systemd/system/vani-flask.service
   sudo nano /etc/systemd/system/vani-ngrok.service
   ```

2. Change `User=` and `Group=` to desired username

3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart vani-flask vani-ngrok
   ```

### Change Paths

If your application is in a different location:

1. Edit service files and update `WorkingDirectory` and `ExecStart` paths

2. Reload and restart services

### Resource Limits

To add resource limits, edit service files and add:

```ini
[Service]
MemoryLimit=2G
CPUQuota=80%
```

## Troubleshooting

### Service Won't Start

**Check status**:
```bash
sudo systemctl status vani-flask
sudo systemctl status vani-ngrok
```

**View recent logs**:
```bash
sudo journalctl -u vani-flask -n 50
sudo journalctl -u vani-ngrok -n 50
```

**Common issues**:
- Missing `.env.local` file
- Wrong permissions on application files
- Python dependencies not installed
- Port 5000 already in use
- Ngrok authtoken not configured

### Flask Fails to Start

**Check**:
```bash
# Verify venv exists
ls -la /opt/vani/venv

# Test Flask manually
cd /opt/vani
source venv/bin/activate
python run.py
```

**Fix**:
```bash
# Reinstall dependencies
cd /opt/vani
source venv/bin/activate
pip install -r requirements.txt

# Check .env.local
cat /opt/vani/.env.local
```

### Ngrok Fails to Connect

**Check**:
```bash
# Verify config
cat ~/.config/ngrok/ngrok.yml

# Test manually
ngrok http 5000 --domain=vani.ngrok.app
```

**Fix**:
```bash
# Reconfigure authtoken
ngrok config add-authtoken YOUR_TOKEN

# Restart service
sudo systemctl restart vani-ngrok
```

### Service Keeps Restarting

**Check logs** to see the error:
```bash
sudo journalctl -u vani-flask -f
```

**Common causes**:
- Configuration errors in `.env.local`
- Database connection issues
- Missing API keys
- Python package conflicts

## Monitoring

### Check Service Status
```bash
sudo systemctl is-active vani-flask
sudo systemctl is-active vani-ngrok
```

### Check Service Uptime
```bash
sudo systemctl show vani-flask --property=ActiveEnterTimestamp
```

### View Service Details
```bash
sudo systemctl show vani-flask
sudo systemctl show vani-ngrok
```

### Resource Usage
```bash
# CPU and Memory
sudo systemctl status vani-flask | grep -E 'Memory|CPU'

# Full stats
ps aux | grep python
ps aux | grep ngrok
```

## Maintenance

### Update Application

```bash
cd /opt/vani
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vani-flask vani-ngrok
```

### View Logs

```bash
# Last 100 lines
sudo journalctl -u vani-flask -n 100

# Since yesterday
sudo journalctl -u vani-flask --since yesterday

# Follow logs
sudo journalctl -u vani-flask -f

# Export logs
sudo journalctl -u vani-flask --since today > flask-logs.txt
```

### Rotate Logs

Systemd automatically rotates journal logs, but you can configure it:

```bash
sudo nano /etc/systemd/journald.conf
```

Set:
```ini
[Journal]
MaxRetentionSec=7day
MaxFileSec=1day
```

Then restart:
```bash
sudo systemctl restart systemd-journald
```

## Best Practices

1. **Always check logs** after starting or restarting services
2. **Test manually** before enabling services
3. **Monitor resources** to prevent out-of-memory issues
4. **Keep services updated** with latest application code
5. **Backup .env.local** before making changes
6. **Use systemctl status** to check service health
7. **Set up monitoring** for production deployments

## Security Notes

- Service files are readable by all users but only editable by root
- Private information is in `.env.local` (mode 600)
- Services run as non-root user
- System directories are protected from writes
- Logs may contain sensitive information - restrict access

## Additional Resources

- [systemd documentation](https://www.freedesktop.org/software/systemd/man/)
- [systemd service files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [journalctl documentation](https://www.freedesktop.org/software/systemd/man/journalctl.html)

## Support

For deployment issues:
1. Check service status and logs
2. Run verification script: `../scripts/verify_deployment.sh`
3. Review main deployment guide: `../GOOGLE_VM_DEPLOYMENT.md`
4. Check quick start guide: `../QUICK_DEPLOY.md`

