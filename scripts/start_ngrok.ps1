# Start Ngrok Tunnel for VANI Project
# Exposes local Flask app (port 5000) to public internet for webhooks

param(
    [int]$Port = 5000,
    [string]$Domain = ""  # Will be read from .env.local
)

$ErrorActionPreference = "Stop"

# Load environment variables from .env.local
$envLocalPath = Join-Path (Get-Location) ".env.local"
$envLoaded = $false
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
                $envLoaded = $true
            }
        }
    }
    if ($envLoaded) {
        Write-Host "✅ Loaded environment variables from .env.local" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  .env.local not found at: $envLocalPath" -ForegroundColor Yellow
}

# Load from ngrok.config.json as fallback
$ngrokConfigPath = Join-Path (Get-Location) "ngrok.config.json"
if (Test-Path $ngrokConfigPath) {
    try {
        $ngrokConfig = Get-Content $ngrokConfigPath | ConvertFrom-Json
        
        # Use ngrok.config.json values if not set from .env.local
        if (-not [Environment]::GetEnvironmentVariable("FLASK_PORT", "Process")) {
            if ($ngrokConfig.flask.port) {
                [Environment]::SetEnvironmentVariable("FLASK_PORT", $ngrokConfig.flask.port.ToString(), "Process")
                Write-Host "✅ Loaded FLASK_PORT from ngrok.config.json" -ForegroundColor Green
            }
        }
        
        if (-not [Environment]::GetEnvironmentVariable("NGROK_DOMAIN", "Process")) {
            if ($ngrokConfig.ngrok.domain) {
                [Environment]::SetEnvironmentVariable("NGROK_DOMAIN", $ngrokConfig.ngrok.domain, "Process")
                Write-Host "✅ Loaded NGROK_DOMAIN from ngrok.config.json" -ForegroundColor Green
            }
        }
        
        if (-not [Environment]::GetEnvironmentVariable("WEBHOOK_BASE_URL", "Process")) {
            if ($ngrokConfig.webhooks.base_url) {
                [Environment]::SetEnvironmentVariable("WEBHOOK_BASE_URL", $ngrokConfig.webhooks.base_url, "Process")
                Write-Host "✅ Loaded WEBHOOK_BASE_URL from ngrok.config.json" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "⚠️  Could not load ngrok.config.json: $_" -ForegroundColor Yellow
    }
}

# Get values from environment (with defaults)
if (-not $Port -or $Port -eq 5000) {
    $envPort = [Environment]::GetEnvironmentVariable("FLASK_PORT", "Process")
    if ($envPort) {
        $Port = [int]$envPort
    }
}

if (-not $Domain -or $Domain -eq "") {
    $Domain = [Environment]::GetEnvironmentVariable("NGROK_DOMAIN", "Process")
    if (-not $Domain) {
        # Try to extract from WEBHOOK_BASE_URL
        $webhookUrl = [Environment]::GetEnvironmentVariable("WEBHOOK_BASE_URL", "Process")
        if ($webhookUrl -and $webhookUrl -match 'https://([^/]+)') {
            $Domain = $matches[1]
            Write-Host "📝 Extracted domain from WEBHOOK_BASE_URL: $Domain" -ForegroundColor Cyan
        } else {
            $Domain = "vani.ngrok.app"  # Default fallback
        }
    }
}

Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "  STARTING NGROK TUNNEL FOR VANI" -ForegroundColor Yellow
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokPath) {
    Write-Host "❌ ngrok not found in PATH" -ForegroundColor Red
    Write-Host "`n💡 Install ngrok:" -ForegroundColor Yellow
    Write-Host "   1. Download from: https://ngrok.com/download" -ForegroundColor White
    Write-Host "   2. Extract to a folder in your PATH" -ForegroundColor White
    Write-Host "   3. Or install via: choco install ngrok" -ForegroundColor White
    Write-Host "   4. Sign up at: https://dashboard.ngrok.com/signup" -ForegroundColor White
    Write-Host "   5. Get authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
    Write-Host "   6. Run: ngrok config add-authtoken YOUR_TOKEN" -ForegroundColor White
    exit 1
}

Write-Host "✅ ngrok found: $($ngrokPath.Source)" -ForegroundColor Green

# Check if Flask app is running on the port
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Flask app is running on port $Port" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Flask app not responding on port $Port" -ForegroundColor Yellow
    Write-Host "   Make sure Flask is running: python run.py" -ForegroundColor White
    Write-Host "   Continuing anyway - ngrok will start but won't work until Flask is running" -ForegroundColor Yellow
}

# Kill any existing ngrok processes
$existingNgrok = Get-Process ngrok -ErrorAction SilentlyContinue
if ($existingNgrok) {
    Write-Host "`n⚠️  Found existing ngrok process(es), stopping..." -ForegroundColor Yellow
    $existingNgrok | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Check if ngrok.yml has a tunnel configured
$useNgrokYml = $false
$ngrokYmlPath = "$env:APPDATA\ngrok\ngrok.yml"
if (-not (Test-Path $ngrokYmlPath)) {
    $ngrokYmlPath = "$env:USERPROFILE\.ngrok2\ngrok.yml"
}

if (Test-Path $ngrokYmlPath) {
    $ngrokYmlContent = Get-Content $ngrokYmlPath -Raw
    # Check if 'vani' tunnel is configured
    if ($ngrokYmlContent -match 'vani:') {
        Write-Host "`n📡 Starting ngrok using 'vani' tunnel from ngrok.yml" -ForegroundColor Cyan
        Write-Host "   Command: ngrok start vani" -ForegroundColor Gray
        Start-Process -NoNewWindow -FilePath "ngrok" -ArgumentList "start", "vani", "--log=stdout" -PassThru | Out-Null
        $useNgrokYml = $true
    }
}

# Check if static domain is configured
$useDomain = $false
if (-not $useNgrokYml) {
    if ($Domain -and $Domain -ne "") {
        Write-Host "`n📡 Starting ngrok with static domain: $Domain" -ForegroundColor Cyan
        Write-Host "   Command: ngrok http $Port --domain=$Domain" -ForegroundColor Gray
        
        # Start ngrok with static domain
        Start-Process -NoNewWindow -FilePath "ngrok" -ArgumentList "http", $Port, "--domain=$Domain", "--log=stdout" -PassThru | Out-Null
        $useDomain = $true
    } else {
        Write-Host "`n📡 Starting ngrok tunnel (random URL)..." -ForegroundColor Cyan
        Write-Host "   Command: ngrok http $Port" -ForegroundColor Gray
        
        # Start ngrok without domain (will get random URL)
        Start-Process -NoNewWindow -FilePath "ngrok" -ArgumentList "http", $Port, "--log=stdout" -PassThru | Out-Null
    }
}

Write-Host "`n⏳ Waiting for ngrok to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Get ngrok URL from API
$maxRetries = 10
$retryCount = 0
$ngrokUrl = $null

while ($retryCount -lt $maxRetries -and !$ngrokUrl) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($response.tunnels -and $response.tunnels.Count -gt 0) {
            $ngrokUrl = $response.tunnels[0].public_url
            if ($ngrokUrl) {
                break
            }
        }
    } catch {
        $retryCount++
        Write-Host "   Waiting for ngrok API... ($retryCount/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (!$ngrokUrl) {
    Write-Host "`n❌ Failed to get ngrok URL after $maxRetries attempts" -ForegroundColor Red
    Write-Host "`n💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check ngrok is running: Get-Process ngrok" -ForegroundColor White
    Write-Host "   2. Check ngrok dashboard: http://localhost:4040" -ForegroundColor White
    Write-Host "   3. Verify authtoken: ngrok config check" -ForegroundColor White
    if ($useDomain) {
        Write-Host "   4. Verify static domain is configured in ngrok dashboard" -ForegroundColor White
        Write-Host "      Go to: https://dashboard.ngrok.com/cloud-edge/domains" -ForegroundColor White
    }
    exit 1
}

Write-Host "`n✅ Ngrok tunnel established!" -ForegroundColor Green
Write-Host "   Public URL: $ngrokUrl" -ForegroundColor Cyan

# Check if URL matches expected domain
if ($useDomain -and $ngrokUrl -notlike "*$Domain*") {
    Write-Host "`n⚠️  Warning: URL doesn't match expected domain" -ForegroundColor Yellow
    Write-Host "   Expected: *$Domain*" -ForegroundColor White
    Write-Host "   Got: $ngrokUrl" -ForegroundColor White
    Write-Host "   Static domain may not be configured in ngrok" -ForegroundColor Yellow
}

# Update .env.local with ngrok URL
$envLocalPath = Join-Path (Get-Location) ".env.local"
if (Test-Path $envLocalPath) {
    $lines = Get-Content $envLocalPath
    $updated = $false
    $newLines = @()
    
    foreach ($line in $lines) {
        if ($line -match "^\s*WEBHOOK_BASE_URL\s*=") {
            $newLines += "WEBHOOK_BASE_URL=$ngrokUrl"
            $updated = $true
        } else {
            $newLines += $line
        }
    }
    
    if (-not $updated) {
        $newLines += ""
        $newLines += "# Webhook Base URL (auto-updated by start_ngrok.ps1)"
        $newLines += "WEBHOOK_BASE_URL=$ngrokUrl"
    }
    
    $newLines | Set-Content -Path $envLocalPath
    Write-Host "`n📝 Updated WEBHOOK_BASE_URL in .env.local" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  .env.local not found - cannot update WEBHOOK_BASE_URL" -ForegroundColor Yellow
}

# Save URL to file
$ngrokUrl | Out-File -FilePath "ngrok-url.txt" -Encoding UTF8 -NoNewline
Write-Host "   Saved URL to ngrok-url.txt" -ForegroundColor Green

# Display webhook endpoints
Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "  WEBHOOK ENDPOINTS" -ForegroundColor Yellow
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Resend:    $ngrokUrl/api/webhooks/resend" -ForegroundColor White
Write-Host "Twilio:    $ngrokUrl/api/webhooks/twilio" -ForegroundColor White
Write-Host "Cal.com:   $ngrokUrl/api/webhooks/cal-com" -ForegroundColor White
Write-Host ""
Write-Host "📊 Ngrok Dashboard: http://localhost:4040" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Ngrok is running! Keep this terminal open." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop ngrok" -ForegroundColor Yellow
Write-Host ""

# Keep script running and monitor ngrok
try {
    while ($true) {
        Start-Sleep -Seconds 30
        $ngrokProcess = Get-Process ngrok -ErrorAction SilentlyContinue
        if (-not $ngrokProcess) {
            Write-Host "`n⚠️  Ngrok process stopped! Restarting..." -ForegroundColor Yellow
            if ($useNgrokYml) {
                Start-Process -NoNewWindow -FilePath "ngrok" -ArgumentList "start", "vani", "--log=stdout" -PassThru | Out-Null
            } elseif ($useDomain) {
                Start-Process -NoNewWindow -FilePath "ngrok" -ArgumentList "http", $Port, "--domain=$Domain", "--log=stdout" -PassThru | Out-Null
            } else {
                Start-Process -NoNewWindow -FilePath "ngrok" -ArgumentList "http", $Port, "--log=stdout" -PassThru | Out-Null
            }
            Start-Sleep -Seconds 5
        }
    }
} catch {
    Write-Host "`n🛑 Stopping ngrok..." -ForegroundColor Yellow
    Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ Ngrok stopped" -ForegroundColor Green
}

