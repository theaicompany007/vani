# VANI Outreach Command Center Setup Script
# This script sets up the virtual environment and database

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   🚀 VANI Outreach Command Center - Setup" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "❌ .env.local file not found!" -ForegroundColor Red
    Write-Host "   Please create .env.local from .env.example and add your credentials.`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ .env.local found`n" -ForegroundColor Green

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`n📥 Installing dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully`n" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies`n" -ForegroundColor Red
    exit 1
}

# Setup database
Write-Host "🗄️  Setting up database..." -ForegroundColor Cyan
python scripts\setup_database.py

Write-Host "`n📊 Seeding initial targets..." -ForegroundColor Cyan
python scripts\seed_targets.py

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✅ Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Run the SQL migration in Supabase Dashboard (see instructions above)" -ForegroundColor White
Write-Host "   2. Start the application: python run.py" -ForegroundColor White
Write-Host "   3. Open: http://localhost:5000/command-center" -ForegroundColor White
Write-Host ""

