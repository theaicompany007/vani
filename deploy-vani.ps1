# Deploy Project VANI to VM
# Syncs code from Windows to VM and runs manage-vani.sh script
#
# Usage:
#   .\deploy-vani.ps1                    # Default: full-deploy
#   .\deploy-vani.ps1 start              # Start containers
#   .\deploy-vani.ps1 rebuild            # Rebuild and start
#   .\deploy-vani.ps1 full-deploy        # Rebuild + Supabase post-deploy
#
# Prerequisites:
#   - OpenSSH client installed (or use gcloud compute scp/ssh)
#   - SSH key configured for VM access
#   - VM user has permissions to run docker compose

param(
    [string]$Action = "full-deploy"  # Action to pass to manage-vani.sh
)

# ============================================================================
# CONFIGURATION - Update these values for your environment
# ============================================================================

# VM Connection Settings
$VmHost = "chroma-vm"                    # VM hostname or IP
$VmUser = "postgres"                     # VM username
$SshKeyPath = ""                         # Path to SSH private key (leave empty to use default)
                                         # Example: "C:\Users\YourName\.ssh\id_rsa"

# Project Paths
$LocalProjectPath = $PSScriptRoot        # Current directory (vani)
$RemoteProjectPath = "/home/postgres/vani"

# Deployment Method: "ssh" (OpenSSH) or "gcloud" (Google Cloud SDK)
$DeployMethod = "ssh"                    # Change to "gcloud" if OpenSSH not available

# Google Cloud Settings (only needed if DeployMethod = "gcloud")
$GcpZone = "asia-south1-a"
$GcpProject = "onlynereputation-agentic"

# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   🚀 Deploying Project VANI" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Action: $Action" -ForegroundColor Cyan
Write-Host "Local Path: $LocalProjectPath" -ForegroundColor Gray
Write-Host "Remote Path: $RemoteProjectPath" -ForegroundColor Gray
Write-Host ""

# Verify local project path exists
if (-not (Test-Path $LocalProjectPath)) {
    Write-Host "❌ Local project path not found: $LocalProjectPath" -ForegroundColor Red
    exit 1
}

# Build SSH/SCP commands
$sshTarget = "${VmUser}@${VmHost}"
$sshOptions = if ($SshKeyPath) { "-i `"$SshKeyPath`"" } else { "" }

# Function to run SSH command
function Invoke-SshCommand {
    param([string]$Command)
    
    if ($DeployMethod -eq "gcloud") {
        Write-Host "  Running: gcloud compute ssh ${VmUser}@${VmHost} ..." -ForegroundColor Gray
        $result = & gcloud compute ssh "${VmUser}@${VmHost}" --zone=$GcpZone --project=$GcpProject --command=$Command 2>&1
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            Write-Host $result -ForegroundColor Red
            throw "SSH command failed with exit code $LASTEXITCODE"
        }
        return $result
    } else {
        Write-Host "  Running: ssh $sshTarget ..." -ForegroundColor Gray
        if ($SshKeyPath) {
            $result = & ssh -i $SshKeyPath $sshTarget $Command 2>&1
        } else {
            $result = & ssh $sshTarget $Command 2>&1
        }
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            Write-Host $result -ForegroundColor Red
            throw "SSH command failed with exit code $LASTEXITCODE"
        }
        return $result
    }
}

# Function to run SCP command
function Invoke-ScpCommand {
    param([string]$Source, [string]$Destination)
    
    Write-Host "  Copying: $(Split-Path $Source -Leaf) ..." -ForegroundColor Gray
    
    if ($DeployMethod -eq "gcloud") {
        # gcloud compute scp handles paths better
        $result = & gcloud compute scp --recurse $Source "${VmUser}@${VmHost}:${Destination}" --zone=$GcpZone --project=$GcpProject 2>&1
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            Write-Host $result -ForegroundColor Red
            throw "SCP command failed with exit code $LASTEXITCODE"
        }
    } else {
        # Use scp with proper path handling
        if ($SshKeyPath) {
            $result = & scp -i $SshKeyPath -r $Source "${sshTarget}:${Destination}" 2>&1
        } else {
            $result = & scp -r $Source "${sshTarget}:${Destination}" 2>&1
        }
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            Write-Host $result -ForegroundColor Red
            throw "SCP command failed with exit code $LASTEXITCODE"
        }
    }
}

# Step 1: Sync code to VM
Write-Host "📤 Step 1: Syncing code to VM..." -ForegroundColor Yellow
Write-Host ""

try {
    # Create remote directory if it doesn't exist
    Invoke-SshCommand "mkdir -p $RemoteProjectPath"
    
    # Sync project files (exclude common ignore patterns)
    # Note: This syncs the entire directory. For production, you might want to exclude:
    # node_modules, .next, .git, etc. Adjust as needed.
    Write-Host "  Syncing project files..." -ForegroundColor Cyan
    
    # For now, sync everything. In production, you might want to:
    # 1. Use rsync with exclusions
    # 2. Or sync specific directories only
    # 3. Or use git pull on VM instead
    
    # SCP copies the directory, so we copy to parent and it creates the project folder
    $remoteParent = Split-Path $RemoteProjectPath -Parent
    Invoke-ScpCommand $LocalProjectPath $remoteParent
    
    Write-Host "  ✅ Code synced successfully" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "  ❌ Failed to sync code: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Run manage script on VM
Write-Host "🔧 Step 2: Running manage-vani.sh $Action on VM..." -ForegroundColor Yellow
Write-Host ""

try {
    $manageScript = "$RemoteProjectPath/manage-vani.sh"
    
    # Check if manage script exists, if not, create it first (for initial setup)
    $checkCmd = "test -f $manageScript && echo 'exists' || echo 'missing'"
    $checkResult = Invoke-SshCommand $checkCmd
    
    if ($checkResult -match "missing") {
        Write-Host "  ⚠️  manage-vani.sh not found. It will be created during initial setup." -ForegroundColor Yellow
        Write-Host "  💡 For now, running docker compose directly..." -ForegroundColor Yellow
        Write-Host ""
        
        # Fallback: run docker compose directly
        $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani"
        if ($Action -eq "full-deploy") {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani up -d --build"
        } elseif ($Action -eq "start") {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani up -d"
        } elseif ($Action -eq "stop") {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani stop"
        } elseif ($Action -eq "restart") {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani restart"
        } elseif ($Action -eq "rebuild") {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani up -d --build"
        } else {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -f docker-compose.yml -p vani $Action"
        }
        
        Invoke-SshCommand $dockerCmd | Out-Null
        
        # Run Supabase post-deploy if full-deploy
        if ($Action -eq "full-deploy") {
            $supabaseScript = "$RemoteProjectPath/supabase_post_deploy.sh"
            $supabaseCheck = Invoke-SshCommand "test -f $supabaseScript && echo 'exists' || echo 'missing'"
            if ($supabaseCheck -match "exists") {
                Write-Host "  📝 Running Supabase post-deploy..." -ForegroundColor Cyan
                Invoke-SshCommand "chmod +x $supabaseScript && $supabaseScript" | Out-Null
            }
        }
    } else {
        # Make script executable and run it
        Invoke-SshCommand "chmod +x $manageScript && $manageScript $Action" | Out-Null
    }
    
    Write-Host "  ✅ Deployment completed" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "  ❌ Failed to run manage script: $_" -ForegroundColor Red
    exit 1
}

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✅ Deployment Complete" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  • Check container status: ssh $sshTarget 'docker compose -p vani ps'" -ForegroundColor Gray
Write-Host "  • View logs: ssh $sshTarget 'docker compose -p vani logs -f'" -ForegroundColor Gray
Write-Host ""


