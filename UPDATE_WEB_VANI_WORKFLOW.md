# How to Update Web and VANI Projects

Complete guide for updating GitHub and production environment for **Web** and **VANI** projects.

---

## 📋 Quick Workflow Summary

For **Web Project** (The AI Company Website):
1. Make changes locally
2. Push to GitHub: `.\push-to-github.ps1`
3. Sync to VM: `.\deploy-web.ps1 full-deploy`

For **VANI Project** (VANI Outreach Command Center):
1. Make changes locally
2. Push to GitHub: `.\push-to-github.ps1`
3. Sync to VM: `.\deploy-vani.ps1 full-deploy`

---

## 🔄 Detailed Workflow

### Step 1: Make Changes Locally

Edit files in your local project directories:

**Web Project:**
```
C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web
```

**VANI Project:**
```
C:\Raaj\kcube_consulting_labs\onlyne-reputation\vani
```

### Step 2: Push to GitHub

Navigate to the project directory and run the push script:

**For Web Project:**
```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web
.\push-to-github.ps1 -AutoCommit -CommitMessage "Your commit message"
```

**For VANI Project:**
```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\vani
.\push-to-github.ps1 -AutoCommit -CommitMessage "Your commit message"
```

**Options:**
- `-AutoCommit` - Automatically commit all changes without prompting
- `-CommitMessage "message"` - Custom commit message
- `-ForceCommit` - Force commit even if no changes detected

**What it does:**
1. Checks git status
2. Stages all changes (`git add -A`)
3. Commits with your message
4. Pushes to GitHub remote

### Step 3: Deploy to Production VM

After pushing to GitHub, deploy to the VM:

**For Web Project:**
```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web
.\deploy-web.ps1 full-deploy
```

**For VANI Project:**
```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\vani
.\deploy-vani.ps1 full-deploy
```

**Available Actions:**
- `full-deploy` (default) - Rebuild + Supabase post-deploy
- `rebuild` - Rebuild and start containers
- `start` - Start existing containers
- `stop` - Stop containers
- `restart` - Restart containers

**What it does:**
1. Syncs code from Windows to VM (using SCP or gcloud)
2. Runs `manage-web.sh` or `manage-vani.sh` on the VM
3. Rebuilds Docker images (if needed)
4. Starts containers
5. Runs Supabase post-deploy script (if `full-deploy`)

---

## 🔄 Alternative: GitHub-First Workflow

If you prefer to sync from GitHub on the VM instead of direct SCP:

### Step 1: Push to GitHub (Same as above)

```powershell
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web
.\push-to-github.ps1 -AutoCommit -CommitMessage "Update web project"
```

### Step 2: Sync from GitHub on VM

SSH to the VM and run the sync script:

```bash
# SSH to VM
gcloud compute ssh postgres@chroma-vm --zone=asia-south1-a --project=onlynereputation-agentic

# Sync all projects from GitHub
cd /home/postgres
./sync-all-projects-from-github.sh
```

This will:
- Pull latest changes from GitHub for all projects
- Handle uncommitted changes (stash before pull)
- Update each project directory

### Step 3: Setup and Deploy on VM

After syncing, run setup and deploy:

```bash
# Setup projects (if needed)
cd /home/postgres
./setup-all-projects-on-vm.sh

# Deploy web project
cd /home/postgres/theaicompany-web
./manage-web.sh full-deploy

# Or deploy VANI project
cd /home/postgres/vani
./manage-vani.sh full-deploy
```

---

## 📝 Prerequisites

### For Web Project

1. **GitHub Repository:**
   - Repository: `https://github.com/theaicompany007/theaicompany-web`
   - Ensure `push-to-github.ps1` is in the project root
   - Git remote configured: `git remote -v`

2. **Deploy Script:**
   - `deploy-web.ps1` in project root
   - Configured with correct VM settings

3. **VM Setup:**
   - Directory: `/home/postgres/theaicompany-web`
   - `manage-web.sh` executable
   - `docker-compose.yml` present
   - `.env.local` configured

### For VANI Project

1. **GitHub Repository:**
   - Repository: `https://github.com/theaicompany007/vani`
   - Ensure `push-to-github.ps1` is in the project root
   - Git remote configured: `git remote -v`

2. **Deploy Script:**
   - `deploy-vani.ps1` in project root
   - Configured with correct VM settings

3. **VM Setup:**
   - Directory: `/home/postgres/vani`
   - `manage-vani.sh` executable
   - `docker-compose.yml` present
   - `.env.local` configured

---

## 🔧 Troubleshooting

### Issue: Push to GitHub Fails

**Error:** `remote: error: GH013: Repository rule violations found`

**Solution:**
- Check for secrets in your code
- Ensure `.gitignore` includes sensitive files
- Remove secrets from git history if needed

**Error:** `! [rejected] main -> main (non-fast-forward)`

**Solution:**
```powershell
# Pull remote changes first
git pull origin main

# Then push again
.\push-to-github.ps1
```

### Issue: Deploy Script Fails

**Error:** `SSH command failed`

**Solution:**
1. Check VM connectivity:
   ```powershell
   gcloud compute ssh postgres@chroma-vm --zone=asia-south1-a --project=onlynereputation-agentic
   ```

2. Verify deploy script settings:
   - `$VmHost = "chroma-vm"`
   - `$VmUser = "postgres"`
   - `$GcpZone = "asia-south1-a"`
   - `$GcpProject = "onlynereputation-agentic"`

3. Try using `gcloud` method:
   - Edit deploy script: `$DeployMethod = "gcloud"`

**Error:** `manage-web.sh not found`

**Solution:**
- Run setup script on VM: `./setup-all-projects-on-vm.sh`
- Or manually create from template (see DEPLOYMENT_WORKFLOW.md)

### Issue: Container Won't Start

**Check logs:**
```bash
# SSH to VM
gcloud compute ssh postgres@chroma-vm --zone=asia-south1-a --project=onlynereputation-agentic

# Check container status
cd /home/postgres/theaicompany-web
docker compose -p web ps

# View logs
docker compose -p web logs -f
```

**Common causes:**
- Missing `.env.local` file
- Incorrect environment variables
- Port conflicts
- Docker build errors

---

## 📊 Quick Reference

### Web Project Commands

```powershell
# Push to GitHub
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\theaicompany-web
.\push-to-github.ps1 -AutoCommit -CommitMessage "Update web"

# Deploy to VM
.\deploy-web.ps1 full-deploy

# Or just rebuild
.\deploy-web.ps1 rebuild
```

### VANI Project Commands

```powershell
# Push to GitHub
cd C:\Raaj\kcube_consulting_labs\onlyne-reputation\vani
.\push-to-github.ps1 -AutoCommit -CommitMessage "Update vani"

# Deploy to VM
.\deploy-vani.ps1 full-deploy

# Or just rebuild
.\deploy-vani.ps1 rebuild
```

### VM Management (SSH)

```bash
# Check web project status
cd /home/postgres/theaicompany-web
./manage-web.sh status

# Check VANI project status
cd /home/postgres/vani
./manage-vani.sh status

# View logs
docker compose -p web logs -f
docker compose -p vani logs -f
```

---

## 🎯 Best Practices

1. **Always push to GitHub first** - This creates a backup and allows VM sync
2. **Use descriptive commit messages** - Helps track changes
3. **Test locally before deploying** - Catch issues early
4. **Use `full-deploy` for production** - Ensures Supabase config is updated
5. **Check container status after deploy** - Verify everything started correctly
6. **Monitor logs** - Watch for errors during deployment

---

## 📚 Related Documentation

- `DEPLOYMENT_WORKFLOW.md` - Complete deployment guide
- `DEPLOYMENT_TROUBLESHOOTING.md` - Common issues and fixes
- `SYNC_PROJECTS_TO_VM.md` - GitHub sync workflow

---

## ✅ Checklist

Before deploying:

- [ ] Changes tested locally
- [ ] Git status clean (or changes committed)
- [ ] Commit message written
- [ ] GitHub remote configured
- [ ] Deploy script configured with correct VM settings
- [ ] VM accessible via SSH/gcloud
- [ ] `.env.local` exists on VM (for production config)

After deploying:

- [ ] Push to GitHub successful
- [ ] Deploy script completed without errors
- [ ] Containers running (`docker compose -p <project> ps`)
- [ ] Application accessible (check ngrok URL or port)
- [ ] Logs show no errors (`docker compose -p <project> logs`)

