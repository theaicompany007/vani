# Fix .env.local Line Ending Issues

## Problem

When you see this error:
```
.env.local: line 6: $'\r': command not found
```

This means your `.env.local` file has **Windows line endings** (CRLF - `\r\n`) but Linux expects **Unix line endings** (LF - `\n`).

## Quick Fix

### Option 1: Use the Fix Script (Recommended)

```bash
# SSH to VM
ssh postgres@chroma-vm

# Navigate to project
cd /home/postgres/vani
# OR
cd /home/postgres/theaicompany-web

# Run fix script
chmod +x /home/postgres/fix-line-endings.sh
/home/postgres/fix-line-endings.sh .env.local
```

### Option 2: Fix Manually

```bash
# VANI
cd /home/postgres/vani
sed -i 's/\r$//' .env.local

# Web
cd /home/postgres/theaicompany-web
sed -i 's/\r$//' .env.local
```

### Option 3: Install dos2unix (Best for Multiple Files)

```bash
# Install dos2unix
sudo apt-get update
sudo apt-get install -y dos2unix

# Fix file
cd /home/postgres/vani
dos2unix .env.local
```

## Prevention

### When Editing on Windows

1. **Use a text editor that supports Unix line endings**:
   - VS Code: Set `"files.eol": "\n"` in settings
   - Notepad++: Edit → EOL Conversion → Unix (LF)
   - Sublime Text: View → Line Endings → Unix

2. **Or fix after copying to VM**:
   ```bash
   # After copying .env.local to VM, fix it
   dos2unix .env.local
   ```

### When Editing on VM

The `update-env-vani.sh` and `update-env-web.sh` scripts automatically fix line endings before and after editing.

## Verify Line Endings

```bash
# Check line endings
file .env.local
# Should show: ASCII text (not "with CRLF line terminators")

# Or check for CR characters
cat -A .env.local | grep '\^M'
# If you see ^M, file has CRLF endings
```

## Your Current .env.local Issues

Looking at your VANI `.env.local`, I notice:

1. **Line ending issue** - needs to be fixed (see above)
2. **Development vs Production** - Currently set to dev:
   ```bash
   WEBHOOK_BASE_URL=https://vani-dev.ngrok.app
   VANI_ENVIRONMENT=dev
   NGROK_DOMAIN=vani-dev.ngrok.app
   ```
3. **Redis configuration** - Should use Docker network:
   ```bash
   REDIS_HOST=redis  # Not 127.0.0.1 (use service name from Docker network)
   REDIS_PORT=6379
   ```

## Recommended Fixes for Your .env.local

After fixing line endings, update these:

```bash
# Redis - Use Docker service name
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# Flask - For Docker, use 0.0.0.0
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Production settings (uncomment when ready)
# WEBHOOK_BASE_URL=https://vani.ngrok.app
# VANI_ENVIRONMENT=prod
# NGROK_DOMAIN=vani.ngrok.app
```

## Complete Fix Command

```bash
# SSH to VM
ssh postgres@chroma-vm

# Fix VANI .env.local
cd /home/postgres/vani
sed -i 's/\r$//' .env.local

# Update Redis settings
sed -i 's/^REDIS_HOST=127.0.0.1/REDIS_HOST=redis/' .env.local
sed -i 's/^FLASK_HOST=127.0.0.1/FLASK_HOST=0.0.0.0/' .env.local

# Restart VANI
./manage-vani.sh restart

# Verify
docker compose -p vani logs --tail=20
```

