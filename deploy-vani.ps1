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
        $fullCmd = "gcloud compute ssh ${VmUser}@${VmHost} --zone=$GcpZone --project=$GcpProject --command=`"$Command`""
        Write-Host "  Running: $fullCmd" -ForegroundColor Gray
        Invoke-Expression $fullCmd
        if ($LASTEXITCODE -ne 0) {
            throw "SSH command failed"
        }
    } else {
        $fullCmd = "ssh $sshOptions $sshTarget `"$Command`""
        Write-Host "  Running: ssh $sshTarget ..." -ForegroundColor Gray
        Invoke-Expression $fullCmd
        if ($LASTEXITCODE -ne 0) {
            throw "SSH command failed"
        }
    }
}

# Function to run SCP command
function Invoke-ScpCommand {
    param([string]$Source, [string]$Destination)
    
    if ($DeployMethod -eq "gcloud") {
        $fullCmd = "gcloud compute scp `"$Source`" `"${VmUser}@${VmHost}:${Destination}`" --zone=$GcpZone --project=$GcpProject --recurse"
        Write-Host "  Copying: $(Split-Path $Source -Leaf) ..." -ForegroundColor Gray
        Invoke-Expression $fullCmd
        if ($LASTEXITCODE -ne 0) {
            throw "SCP command failed"
        }
    } else {
        $scpCmd = if ($SshKeyPath) {
            "scp -i `"$SshKeyPath`" -r `"$Source`" ${sshTarget}:${Destination}"
        } else {
            "scp -r `"$Source`" ${sshTarget}:${Destination}"
        }
        Write-Host "  Copying: $(Split-Path $Source -Leaf) ..." -ForegroundColor Gray
        Invoke-Expression $scpCmd
        if ($LASTEXITCODE -ne 0) {
            throw "SCP command failed"
        }
    }
}

# Step 1: Sync code to VM
Write-Host "📤 Step 1: Syncing code to VM..." -ForegroundColor Yellow
Write-Host ""

try {
    # Create remote directory if it doesn't exist
    Invoke-SshCommand "mkdir -p $RemoteProjectPath"
    
    # Sync project files
    Write-Host "  Syncing project files..." -ForegroundColor Cyan
    Invoke-ScpCommand $LocalProjectPath (Split-Path $RemoteProjectPath -Parent)
    
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
    
    # Check if manage script exists
    $checkCmd = "test -f $manageScript && echo 'exists' || echo 'missing'"
    $result = if ($DeployMethod -eq "gcloud") {
        gcloud compute ssh ${VmUser}@${VmHost} --zone=$GcpZone --project=$GcpProject --command=$checkCmd 2>&1 | Out-String
    } else {
        ssh $sshOptions $sshTarget $checkCmd 2>&1 | Out-String
    }
    
    if ($result -match "missing") {
        Write-Host "  ⚠️  manage-vani.sh not found. It will be created during initial setup." -ForegroundColor Yellow
        Write-Host "  💡 For now, running docker compose directly..." -ForegroundColor Yellow
        Write-Host ""
        
        # Fallback: run docker compose directly
        $dockerCmd = "cd $RemoteProjectPath && docker compose -p vani $Action"
        if ($Action -eq "full-deploy") {
            $dockerCmd = "cd $RemoteProjectPath && docker compose -p vani up -d --build && $RemoteProjectPath/scripts/supabase_post_deploy.sh"
        }
        Invoke-SshCommand $dockerCmd
    } else {
        # Make script executable and run it
        Invoke-SshCommand "chmod +x $manageScript && $manageScript $Action"
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


