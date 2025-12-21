<#
.SYNOPSIS
  Push current project to GitHub

.DESCRIPTION
  This script checks git status, optionally commits changes, and pushes to GitHub.
  Run this from the project root directory.

.PARAMETER AutoCommit
  Automatically commit all changes without prompting

.PARAMETER CommitMessage
  Custom commit message (if not provided, will prompt or use default)

.PARAMETER ForceCommit
  Force commit even if no changes detected (creates empty commit)

.EXAMPLE
  .\push-to-github.ps1
  .\push-to-github.ps1 -AutoCommit
  .\push-to-github.ps1 -CommitMessage "Update deployment scripts"
  .\push-to-github.ps1 -AutoCommit -CommitMessage "Full repository commit" -ForceCommit
#>

param(
    [switch]$AutoCommit = $false,
    [string]$CommitMessage = "",
    [switch]$ForceCommit = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   Push to GitHub" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "[ERROR] Not in a git repository" -ForegroundColor Red
    Write-Host "[TIP] Run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Get project name from current directory
$ProjectName = Split-Path -Leaf (Get-Location)
Write-Host "[INFO] Project: $ProjectName" -ForegroundColor Cyan
Write-Host ""

# Check git remote
Write-Host "[CHECK] Checking git remote..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No 'origin' remote configured" -ForegroundColor Red
    Write-Host "[TIP] Configure git remote first:" -ForegroundColor Yellow
    Write-Host '   git remote add origin "your-github-repo-url"' -ForegroundColor Gray
    exit 1
}

Write-Host "[OK] Remote: $remoteUrl" -ForegroundColor Green
Write-Host ""

# Check git status
Write-Host "[CHECK] Checking git status..." -ForegroundColor Yellow
$status = git status --porcelain
$branch = git rev-parse --abbrev-ref HEAD

Write-Host "[INFO] Branch: $branch" -ForegroundColor Cyan

# Check for any changes (staged, unstaged, or untracked)
$hasChanges = $false
if ($status) {
    $statusLines = $status -split "`n" | Where-Object { $_.Trim() -ne "" }
    if ($statusLines) {
        $hasChanges = $true
        $changedFiles = $statusLines.Count
        Write-Host "[INFO] Changes detected: $changedFiles file(s)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Changed files:" -ForegroundColor Gray
        git status --short | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        Write-Host ""
    }
}

if ($hasChanges) {
    
    # Handle committing
    $shouldCommit = $false
    if ($AutoCommit) {
        $shouldCommit = $true
        if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
            $CommitMessage = "Update project files"
        }
    } else {
        $response = Read-Host "Commit and push these changes? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            $shouldCommit = $true
            if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
                $CommitMessage = Read-Host "Enter commit message (or press Enter for default)"
                if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
                    $CommitMessage = "Update project files"
                }
            }
        }
    }
    
    if ($shouldCommit) {
        Write-Host ""
        Write-Host "[COMMIT] Committing all changes..." -ForegroundColor Yellow
        
        # Stage all changes (including new files, modified files, and deleted files)
        Write-Host "  Staging all changes..." -ForegroundColor Cyan
        git add -A
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to stage changes" -ForegroundColor Red
            exit 1
        }
        
        # Commit with message
        Write-Host "  Committing with message: $CommitMessage" -ForegroundColor Cyan
        git commit -m "$CommitMessage"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to commit changes" -ForegroundColor Red
            Write-Host "[TIP] This might happen if there are no changes to commit" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "[OK] All changes committed successfully" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] Skipping commit" -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] Working directory clean - no changes to commit" -ForegroundColor Green
    Write-Host ""
    
    if ($ForceCommit) {
        Write-Host "[WARN] Force commit requested - will create empty commit" -ForegroundColor Yellow
        Write-Host ""
        
        if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
            if ($AutoCommit) {
                $CommitMessage = "Empty commit - force update"
            } else {
                $CommitMessage = Read-Host "Enter commit message for empty commit"
                if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
                    $CommitMessage = "Empty commit - force update"
                }
            }
        }
        
        Write-Host "[COMMIT] Creating empty commit..." -ForegroundColor Yellow
        git commit --allow-empty -m "$CommitMessage"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to create empty commit" -ForegroundColor Red
            exit 1
        }
        Write-Host "[OK] Empty commit created" -ForegroundColor Green
    } else {
        Write-Host "[TIP] If you want to commit everything, make sure you have changes in the repository" -ForegroundColor Cyan
        Write-Host "[TIP] Or use -ForceCommit to create an empty commit" -ForegroundColor Cyan
    }
}

# Check if we need to push
Write-Host ""
Write-Host "[CHECK] Checking if push is needed..." -ForegroundColor Yellow
$localCommit = git rev-parse HEAD
$remoteCommit = git ls-remote origin $branch 2>$null | Select-Object -First 1

if ($remoteCommit) {
    $remoteHash = ($remoteCommit -split '\s+')[0]
    if ($localCommit -eq $remoteHash) {
        Write-Host "[OK] Local and remote are in sync" -ForegroundColor Green
        Write-Host ""
        Write-Host "[INFO] No push needed. Repository is up to date." -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "[INFO] Local commits ahead of remote" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] No remote branch found, will push new branch" -ForegroundColor Yellow
}

# Push to GitHub
Write-Host ""
Write-Host "[PUSH] Pushing to GitHub..." -ForegroundColor Yellow
git push origin $branch

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to push to GitHub" -ForegroundColor Red
    Write-Host "[TIP] Check your git credentials and remote URL" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Successfully pushed to GitHub!" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Repository: $remoteUrl" -ForegroundColor Cyan
Write-Host "[INFO] Branch: $branch" -ForegroundColor Cyan
Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "[OK] Push Complete!" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

