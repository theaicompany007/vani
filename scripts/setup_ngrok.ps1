# Setup Ngrok for VANI Project
# Guides user through ngrok installation and configuration

# Load environment variables from .env.local
$envLocalPath = Join-Path (Get-Location) ".env.local"
if (Test-Path $envLocalPath) {
    Get-Content $envLocalPath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            if ($line -match '^\s*([^#][^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove quotes if present
                if ($value -match '^["''](.*)["'']$') {
                    $value = $matches[1]
                }
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
    Write-Host "✅ Loaded environment variables from .env.local" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env.local not found, some checks may use defaults" -ForegroundColor Yellow
}

Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "  NGROK SETUP FOR VANI PROJECT" -ForegroundColor Yellow
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if ($ngrokPath) {
    Write-Host "✅ ngrok is installed: $($ngrokPath.Source)" -ForegroundColor Green
    $ngrokVersion = & ngrok version 2>&1
    Write-Host "   Version: $ngrokVersion" -ForegroundColor Gray
} else {
    Write-Host "❌ ngrok is not installed" -ForegroundColor Red
    Write-Host "`n📥 Installation Steps:" -ForegroundColor Yellow
    Write-Host "   1. Download ngrok from: https://ngrok.com/download" -ForegroundColor White
    Write-Host "   2. Extract ngrok.exe to a folder in your PATH" -ForegroundColor White
    Write-Host "      (e.g., C:\Program Files\ngrok\)" -ForegroundColor Gray
    Write-Host "   3. Or install via Chocolatey: choco install ngrok" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if authtoken is configured
Write-Host "`n🔐 Checking ngrok authentication..." -ForegroundColor Cyan
$configCheck = & ngrok config check 2>&1
if ($configCheck -match "valid" -or $configCheck -match "authtoken") {
    Write-Host "✅ Ngrok authtoken is configured" -ForegroundColor Green
} else {
    Write-Host "❌ Ngrok authtoken not configured" -ForegroundColor Red
    Write-Host "`n📝 Setup Steps:" -ForegroundColor Yellow
    Write-Host "   1. Sign up at: https://dashboard.ngrok.com/signup" -ForegroundColor White
    Write-Host "   2. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
    Write-Host "   3. Run: ngrok config add-authtoken YOUR_TOKEN" -ForegroundColor White
    Write-Host ""
    Write-Host "   Or for static domain (vani.ngrok.app):" -ForegroundColor Yellow
    Write-Host "   1. Go to: https://dashboard.ngrok.com/cloud-edge/domains" -ForegroundColor White
    Write-Host "   2. Reserve domain: vani.ngrok.app" -ForegroundColor White
    Write-Host "   3. Configure in ngrok.yml or use --domain flag" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check for static domain configuration
Write-Host "`n🌐 Checking static domain configuration..." -ForegroundColor Cyan

# Get expected domain from .env.local
$expectedDomain = [Environment]::GetEnvironmentVariable("NGROK_DOMAIN", "Process")
if (-not $expectedDomain) {
    $webhookUrl = [Environment]::GetEnvironmentVariable("WEBHOOK_BASE_URL", "Process")
    if ($webhookUrl -and $webhookUrl -match 'https://([^/]+)') {
        $expectedDomain = $matches[1]
    } else {
        $expectedDomain = "vani.ngrok.app"  # Default
    }
}

Write-Host "   Expected domain: $expectedDomain" -ForegroundColor Gray

$configPath = "$env:USERPROFILE\.ngrok2\ngrok.yml"
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Raw
    $domainPattern = $expectedDomain -replace '\.', '\.'
    if ($configContent -match $domainPattern) {
        Write-Host "✅ Static domain '$expectedDomain' is configured in ngrok.yml" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Static domain '$expectedDomain' not found in ngrok.yml" -ForegroundColor Yellow
        Write-Host "   You'll get a random ngrok URL instead" -ForegroundColor Gray
        Write-Host "`n💡 To configure static domain:" -ForegroundColor Yellow
        Write-Host "   1. Reserve domain at: https://dashboard.ngrok.com/cloud-edge/domains" -ForegroundColor White
        Write-Host "   2. Add to ngrok.yml:" -ForegroundColor White
        Write-Host "      tunnels:" -ForegroundColor Gray
        Write-Host "        vani:" -ForegroundColor Gray
        Write-Host "          proto: http" -ForegroundColor Gray
        $flaskPort = [Environment]::GetEnvironmentVariable("FLASK_PORT", "Process")
        if (-not $flaskPort) { $flaskPort = "5000" }
        Write-Host "          addr: $flaskPort" -ForegroundColor Gray
        Write-Host "          domain: $expectedDomain" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️  ngrok.yml not found at: $configPath" -ForegroundColor Yellow
    Write-Host "   Using default configuration" -ForegroundColor Gray
}

Write-Host "`n✅ Ngrok setup complete!" -ForegroundColor Green
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Start Flask app: python run.py" -ForegroundColor White
Write-Host "   2. Start ngrok: .\scripts\start_ngrok.ps1" -ForegroundColor White
Write-Host "   3. Configure webhooks with the ngrok URL" -ForegroundColor White
Write-Host ""

