# VANI & The AI Company Web - Development & Deployment Guide

## Overview

This guide provides **separate, independent commands** for managing VANI and The AI Company Website projects during active development. Use this when you're working on both projects side by side and need to update code, environment variables, or rebuild Docker images independently.

---

## Quick Reference - Common Operations

### VANI Project

```bash
# Navigate to VANI
cd /home/postgres/vani

# Update code from GitHub
git pull origin main

# Edit environment file
nano .env.local

# Rebuild Docker image and restart
./manage-vani.sh rebuild

# Full deployment (rebuild + Supabase update)
./manage-vani.sh full-deploy

# View logs
docker compose -p vani logs -f

# Check status
./manage-vani.sh status
```

### The AI Company Web Project

```bash
# Navigate to Web
cd /home/postgres/theaicompany-web

# Update code from GitHub
git pull origin main

# Edit environment file
nano .env.local

# Rebuild Docker image and restart
./manage-web.sh rebuild

# Full deployment (rebuild + Supabase update)
./manage-web.sh full-deploy

# View logs
docker compose -p web logs -f

# Check status
./manage-web.sh status
```

---

## Step-by-Step: Update Code and Rebuild

### Scenario 1: Update VANI Code Only

```bash
# Step 1: SSH to VM
ssh postgres@chroma-vm

# Step 2: Navigate to VANI project
cd /home/postgres/vani

# Step 3: Pull latest code
git pull origin main

# Step 4: Rebuild Docker image (if code changes require rebuild)
./manage-vani.sh rebuild

# OR if you just changed config files (no code changes):
./manage-vani.sh restart

# Step 5: Verify it's running
./manage-vani.sh status
docker compose -p vani ps

# Step 6: Check logs for errors
docker compose -p vani logs -f --tail=50
```

### Scenario 2: Update The AI Company Web Code Only

```bash
# Step 1: SSH to VM
ssh postgres@chroma-vm

# Step 2: Navigate to Web project
cd /home/postgres/theaicompany-web

# Step 3: Pull latest code
git pull origin main

# Step 4: Rebuild Docker image (if code changes require rebuild)
./manage-web.sh rebuild

# OR if you just changed config files (no code changes):
./manage-web.sh restart

# Step 5: Verify it's running
./manage-web.sh status
docker compose -p web ps

# Step 6: Check logs for errors
docker compose -p web logs -f --tail=50
```

### Scenario 3: Update Both Projects

```bash
# Step 1: SSH to VM
ssh postgres@chroma-vm

# Step 2: Update VANI
cd /home/postgres/vani
git pull origin main
./manage-vani.sh rebuild

# Step 3: Update Web
cd /home/postgres/theaicompany-web
git pull origin main
./manage-web.sh rebuild

# Step 4: Verify both
docker compose -p vani ps
docker compose -p web ps
```

---

## Step-by-Step: Update Environment Variables

### Update VANI Environment Variables

```bash
# Step 1: Navigate to VANI
cd /home/postgres/vani

# Step 2: Edit environment file
nano .env.local
# OR
vi .env.local

# Step 3: Save and exit (Ctrl+X, Y, Enter for nano)

# Step 4: Restart container to load new environment variables
./manage-vani.sh restart

# Step 5: Verify new variables are loaded
docker compose -p vani exec vani-app env | grep YOUR_VARIABLE_NAME

# Step 6: If Supabase URLs changed, run post-deploy
./manage-vani.sh full-deploy
```

### Update Web Environment Variables

```bash
# Step 1: Navigate to Web
cd /home/postgres/theaicompany-web

# Step 2: Edit environment file
nano .env.local
# OR
vi .env.local

# Step 3: Save and exit

# Step 4: Restart container to load new environment variables
./manage-web.sh restart

# Step 5: Verify new variables are loaded
docker compose -p web exec web-app env | grep YOUR_VARIABLE_NAME

# Step 6: If Supabase URLs changed, run post-deploy
./manage-web.sh full-deploy
```

---

## Step-by-Step: Recreate Docker Image

### Recreate VANI Docker Image

```bash
# Step 1: Navigate to VANI
cd /home/postgres/vani

# Step 2: Stop container
./manage-vani.sh stop
# OR
docker compose -p vani stop

# Step 3: Remove old image (optional - forces fresh build)
docker rmi vani-app 2>/dev/null || true
# OR remove all vani images
docker images | grep vani | awk '{print $3}' | xargs docker rmi 2>/dev/null || true

# Step 4: Rebuild image from scratch
./manage-vani.sh rebuild
# OR
docker compose -p vani build --no-cache
docker compose -p vani up -d

# Step 5: Verify new image
docker images | grep vani
docker compose -p vani ps

# Step 6: Check logs
docker compose -p vani logs -f
```

### Recreate Web Docker Image

```bash
# Step 1: Navigate to Web
cd /home/postgres/theaicompany-web

# Step 2: Stop container
./manage-web.sh stop
# OR
docker compose -p web stop

# Step 3: Remove old image (optional - forces fresh build)
docker rmi web-app 2>/dev/null || true
# OR remove all web images
docker images | grep theaicompany-web | awk '{print $3}' | xargs docker rmi 2>/dev/null || true

# Step 4: Rebuild image from scratch
./manage-web.sh rebuild
# OR
docker compose -p web build --no-cache
docker compose -p web up -d

# Step 5: Verify new image
docker images | grep web
docker compose -p web ps

# Step 6: Check logs
docker compose -p web logs -f
```

---

## Step-by-Step: Complete Fresh Rebuild

### Fresh Rebuild VANI (Remove Everything and Rebuild)

```bash
# Step 1: Navigate to VANI
cd /home/postgres/vani

# Step 2: Stop and remove everything (keeps volumes)
./manage-vani.sh purge
# OR manually:
docker compose -p vani down

# Step 3: Remove images
docker images | grep vani | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

# Step 4: Pull latest code
git pull origin main

# Step 5: Rebuild from scratch
docker compose -p vani build --no-cache

# Step 6: Start fresh
docker compose -p vani up -d

# Step 7: Run Supabase post-deploy
./supabase_post_deploy-vani.sh

# Step 8: Verify
./manage-vani.sh status
curl http://localhost:5000/health
```

### Fresh Rebuild Web (Remove Everything and Rebuild)

```bash
# Step 1: Navigate to Web
cd /home/postgres/theaicompany-web

# Step 2: Stop and remove everything (keeps volumes)
./manage-web.sh purge
# OR manually:
docker compose -p web down

# Step 3: Remove images
docker images | grep theaicompany-web | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

# Step 4: Pull latest code
git pull origin main

# Step 5: Rebuild from scratch
docker compose -p web build --no-cache

# Step 6: Start fresh
docker compose -p web up -d

# Step 7: Run Supabase post-deploy
./supabase_post_deploy-web.sh

# Step 8: Verify
./manage-web.sh status
curl http://localhost:3000/health
```

---

## Management Scripts Reference

### VANI Management Script (`manage-vani.sh`)

**Location**: `/home/postgres/vani/manage-vani.sh`

**Available Commands**:

```bash
cd /home/postgres/vani

./manage-vani.sh start       # Start containers
./manage-vani.sh stop        # Stop containers
./manage-vani.sh restart     # Restart containers (no rebuild)
./manage-vani.sh rebuild     # Rebuild image and restart
./manage-vani.sh purge       # Remove containers/networks (keeps volumes)
./manage-vani.sh full-deploy # Rebuild + Supabase update
./manage-vani.sh status      # Show status
```

### Web Management Script (`manage-web.sh`)

**Location**: `/home/postgres/theaicompany-web/manage-web.sh`

**Available Commands**:

```bash
cd /home/postgres/theaicompany-web

./manage-web.sh start       # Start containers
./manage-web.sh stop        # Stop containers
./manage-web.sh restart     # Restart containers (no rebuild)
./manage-web.sh rebuild     # Rebuild image and restart
./manage-web.sh purge       # Remove containers/networks (keeps volumes)
./manage-web.sh full-deploy # Rebuild + Supabase update
./manage-web.sh test-rag    # Test RAG service connectivity
./manage-web.sh status      # Show status
```

---

## Direct Docker Compose Commands

### VANI Direct Commands

```bash
cd /home/postgres/vani

# Start
docker compose -p vani up -d

# Stop
docker compose -p vani stop

# Restart
docker compose -p vani restart

# Rebuild (with cache)
docker compose -p vani up -d --build

# Rebuild (no cache - fresh)
docker compose -p vani build --no-cache
docker compose -p vani up -d

# View logs
docker compose -p vani logs -f

# View logs (last 100 lines)
docker compose -p vani logs --tail=100

# Execute command in container
docker compose -p vani exec vani-app bash
docker compose -p vani exec vani-app python --version

# Check status
docker compose -p vani ps

# Remove everything (keeps volumes)
docker compose -p vani down

# Remove everything including volumes (⚠️ deletes data)
docker compose -p vani down -v
```

### Web Direct Commands

```bash
cd /home/postgres/theaicompany-web

# Start
docker compose -p web up -d

# Stop
docker compose -p web stop

# Restart
docker compose -p web restart

# Rebuild (with cache)
docker compose -p web up -d --build

# Rebuild (no cache - fresh)
docker compose -p web build --no-cache
docker compose -p web up -d

# View logs
docker compose -p web logs -f

# View logs (last 100 lines)
docker compose -p web logs --tail=100

# Execute command in container
docker compose -p web exec web-app sh
docker compose -p web exec web-app node --version

# Check status
docker compose -p web ps

# Remove everything (keeps volumes)
docker compose -p web down

# Remove everything including volumes (⚠️ deletes data)
docker compose -p web down -v
```

---

## Environment File Management

### View Current Environment Variables

**VANI**:
```bash
cd /home/postgres/vani
cat .env.local
# OR view specific variable
grep SUPABASE_URL .env.local
```

**Web**:
```bash
cd /home/postgres/theaicompany-web
cat .env.local
# OR view specific variable
grep SUPABASE_URL .env.local
```

### Backup Environment Files

```bash
# Backup VANI
cp /home/postgres/vani/.env.local /home/postgres/vani/.env.local.backup

# Backup Web
cp /home/postgres/theaicompany-web/.env.local /home/postgres/theaicompany-web/.env.local.backup
```

### Restore Environment Files

```bash
# Restore VANI
cp /home/postgres/vani/.env.local.backup /home/postgres/vani/.env.local
./manage-vani.sh restart

# Restore Web
cp /home/postgres/theaicompany-web/.env.local.backup /home/postgres/theaicompany-web/.env.local
./manage-web.sh restart
```

---

## Code Update Workflow

### Workflow 1: Update Code on Windows, Deploy to VM

```powershell
# On Windows - VANI
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\vani
git pull origin main
# Make your code changes
git add .
git commit -m "Your changes"
git push origin main
.\deploy-vani.ps1 full-deploy

# On Windows - Web
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web
git pull origin main
# Make your code changes
git add .
git commit -m "Your changes"
git push origin main
.\deploy-web.ps1 full-deploy
```

### Workflow 2: Update Code Directly on VM

```bash
# VANI
cd /home/postgres/vani
git pull origin main
# Make your code changes
git add .
git commit -m "Your changes"
git push origin main
./manage-vani.sh rebuild

# Web
cd /home/postgres/theaicompany-web
git pull origin main
# Make your code changes
git add .
git commit -m "Your changes"
git push origin main
./manage-web.sh rebuild
```

---

## Fix Line Ending Issues

### Problem: `$'\r': command not found` Error

If you see this error when sourcing `.env.local`, it means the file has Windows line endings.

**Quick Fix**:
```bash
# VANI
cd /home/postgres/vani
sed -i 's/\r$//' .env.local
./manage-vani.sh restart

# Web
cd /home/postgres/theaicompany-web
sed -i 's/\r$//' .env.local
./manage-web.sh restart
```

**Or use the fix script**:
```bash
cd /home/postgres/vani
./fix-vani-env.sh  # Fixes line endings + Docker settings
```

See `FIX_ENV_LINE_ENDINGS.md` for detailed instructions.

---

## Troubleshooting

### VANI Container Won't Start

```bash
cd /home/postgres/vani

# Check logs
docker compose -p vani logs

# Check environment file
cat .env.local

# Check if infrastructure is running
docker compose -p infra ps

# Try restarting
./manage-vani.sh restart

# If still failing, rebuild
./manage-vani.sh rebuild
```

### Web Container Won't Start

```bash
cd /home/postgres/theaicompany-web

# Check logs
docker compose -p web logs

# Check environment file
cat .env.local

# Check if infrastructure is running
docker compose -p infra ps

# Test RAG connectivity
./manage-web.sh test-rag

# Try restarting
./manage-web.sh restart

# If still failing, rebuild
./manage-web.sh rebuild
```

### Line Ending Errors

```bash
# If you see: .env.local: line X: $'\r': command not found

# VANI - Quick fix
cd /home/postgres/vani
sed -i 's/\r$//' .env.local
./manage-vani.sh restart

# Web - Quick fix
cd /home/postgres/theaicompany-web
sed -i 's/\r$//' .env.local
./manage-web.sh restart
```

### Environment Variables Not Updating

```bash
# VANI
cd /home/postgres/vani
# Edit .env.local
nano .env.local
# Restart (not just stop/start - need full restart)
docker compose -p vani down
docker compose -p vani up -d

# Web
cd /home/postgres/theaicompany-web
# Edit .env.local
nano .env.local
# Restart
docker compose -p web down
docker compose -p web up -d
```

### Image Build Fails

```bash
# VANI - Clean build
cd /home/postgres/vani
docker compose -p vani down
docker system prune -f
docker compose -p vani build --no-cache
docker compose -p vani up -d

# Web - Clean build
cd /home/postgres/theaicompany-web
docker compose -p web down
docker system prune -f
docker compose -p web build --no-cache
docker compose -p web up -d
```

---

## Quick Command Cheat Sheet

### VANI Quick Commands

```bash
# One-liners
cd /home/postgres/vani && git pull && ./manage-vani.sh rebuild
cd /home/postgres/vani && nano .env.local && ./manage-vani.sh restart
cd /home/postgres/vani && docker compose -p vani logs -f
cd /home/postgres/vani && docker compose -p vani ps
```

### Web Quick Commands

```bash
# One-liners
cd /home/postgres/theaicompany-web && git pull && ./manage-web.sh rebuild
cd /home/postgres/theaicompany-web && nano .env.local && ./manage-web.sh restart
cd /home/postgres/theaicompany-web && docker compose -p web logs -f
cd /home/postgres/theaicompany-web && docker compose -p web ps
```

### Both Projects

```bash
# Update both
cd /home/postgres/vani && git pull && ./manage-vani.sh rebuild && \
cd /home/postgres/theaicompany-web && git pull && ./manage-web.sh rebuild

# Status both
docker compose -p vani ps && docker compose -p web ps

# Logs both (in separate terminals)
docker compose -p vani logs -f
docker compose -p web logs -f
```

---

## Windows Deployment Scripts

### Deploy VANI from Windows

```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\vani

# Full deployment (rebuild + Supabase update)
.\deploy-vani.ps1 full-deploy

# Just rebuild
.\deploy-vani.ps1 rebuild

# Just restart
.\deploy-vani.ps1 restart

# Just start
.\deploy-vani.ps1 start
```

### Deploy Web from Windows

```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web

# Full deployment (rebuild + Supabase update)
.\deploy-web.ps1 full-deploy

# Just rebuild
.\deploy-web.ps1 rebuild

# Just restart
.\deploy-web.ps1 restart

# Just start
.\deploy-web.ps1 start

# Test RAG
.\deploy-web.ps1 test-rag
```

---

## Best Practices

1. **Always pull latest code before rebuilding**
   ```bash
   git pull origin main && ./manage-vani.sh rebuild
   ```

2. **Backup .env.local before major changes**
   ```bash
   cp .env.local .env.local.backup
   ```

3. **Check logs after rebuild**
   ```bash
   ./manage-vani.sh rebuild && docker compose -p vani logs -f
   ```

4. **Verify infrastructure is running before deploying**
   ```bash
   docker compose -p infra ps
   ```

5. **Use full-deploy when Supabase URLs change**
   ```bash
   ./manage-vani.sh full-deploy  # Updates Supabase webhooks
   ```

6. **Test endpoints after deployment**
   ```bash
   curl http://localhost:5000/health  # VANI
   curl http://localhost:3000/health  # Web
   ```

---

## Project-Specific Notes

### VANI Specific

- **Port**: 5000
- **Requires**: Redis (from infrastructure)
- **Ngrok**: `vani.ngrok.app`
- **Supabase Webhooks**: Resend, Twilio, Cal.com

### Web Specific

- **Port**: 3000
- **Requires**: RAG Service (from infrastructure)
- **Runs**: 24x7
- **Test RAG**: `./manage-web.sh test-rag`

---

**Last Updated**: Development workflow guide for VANI and The AI Company Web projects.

