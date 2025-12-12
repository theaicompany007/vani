#!/bin/bash
# VANI Deployment Verification Script
# Run this on chroma-vm to verify deployment
# Modified to use /home/postgres/vani

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_header() { echo ""; echo -e "${BLUE}========================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}========================================${NC}"; echo ""; }

ERRORS=0
WARNINGS=0

print_header "VANI Deployment Verification"

# Check 1: Python installation
print_info "Checking Python 3.11..."
if command -v python3.11 &> /dev/null; then
    VERSION=$(python3.11 --version)
    print_success "Python installed: $VERSION"
else
    print_error "Python 3.11 not found"
    ((ERRORS++))
fi

# Check 2: Ngrok installation
print_info "Checking ngrok..."
if command -v ngrok &> /dev/null; then
    VERSION=$(ngrok version | head -n1)
    print_success "Ngrok installed: $VERSION"
else
    print_error "Ngrok not found"
    ((ERRORS++))
fi

# Check 3: Application directory
print_info "Checking application directory..."
if [ -d /home/postgres/vani ]; then
    print_success "Application directory exists: /home/postgres/vani"
    
    # Check key files
    if [ -f /home/postgres/vani/run.py ]; then
        print_success "run.py found"
    else
        print_error "run.py not found"
        ((ERRORS++))
    fi
    
    if [ -f /home/postgres/vani/requirements.txt ]; then
        print_success "requirements.txt found"
    else
        print_error "requirements.txt not found"
        ((ERRORS++))
    fi
else
    print_error "Application directory not found: /home/postgres/vani"
    ((ERRORS++))
fi

# Check 4: Virtual environment
print_info "Checking Python virtual environment..."
if [ -d /home/postgres/vani/venv ]; then
    print_success "Virtual environment exists"
    
    # Check if packages are installed
    if [ -f /home/postgres/vani/venv/bin/python ]; then
        print_success "Python interpreter in venv"
        
        # Check Flask
        if /home/postgres/vani/venv/bin/python -c "import flask" 2>/dev/null; then
            FLASK_VERSION=$(/home/postgres/vani/venv/bin/python -c "import flask; print(flask.__version__)")
            print_success "Flask installed: $FLASK_VERSION"
        else
            print_error "Flask not installed in venv"
            ((ERRORS++))
        fi
        
        # Check Supabase
        if /home/postgres/vani/venv/bin/python -c "import supabase" 2>/dev/null; then
            print_success "Supabase client installed"
        else
            print_error "Supabase client not installed in venv"
            ((ERRORS++))
        fi
    fi
else
    print_error "Virtual environment not found"
    ((ERRORS++))
fi

# Check 5: Environment file
print_info "Checking environment configuration..."
if [ -f /home/postgres/vani/.env.local ]; then
    print_success ".env.local exists"
    
    # Check for required variables
    source /home/postgres/vani/.env.local 2>/dev/null || true
    
    REQUIRED_VARS=(
        "SUPABASE_URL"
        "SUPABASE_KEY"
        "FLASK_PORT"
        "WEBHOOK_BASE_URL"
        "OPENAI_API_KEY"
        "RESEND_API_KEY"
    )
    
    for VAR in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!VAR}" ]; then
            print_warning "$VAR not set in .env.local"
            ((WARNINGS++))
        else
            print_success "$VAR is set"
        fi
    done
else
    print_error ".env.local not found"
    ((ERRORS++))
fi

# Check 6: Systemd services
print_info "Checking systemd services..."

if [ -f /etc/systemd/system/vani-flask.service ]; then
    print_success "Flask service file exists"
    
    if systemctl is-enabled vani-flask &>/dev/null; then
        print_success "Flask service enabled"
    else
        print_warning "Flask service not enabled"
        ((WARNINGS++))
    fi
    
    if systemctl is-active vani-flask &>/dev/null; then
        print_success "Flask service is running"
    else
        print_error "Flask service not running"
        ((ERRORS++))
    fi
else
    print_error "Flask service file not found"
    ((ERRORS++))
fi

if [ -f /etc/systemd/system/vani-ngrok.service ]; then
    print_success "Ngrok service file exists"
    
    if systemctl is-enabled vani-ngrok &>/dev/null; then
        print_success "Ngrok service enabled"
    else
        print_warning "Ngrok service not enabled"
        ((WARNINGS++))
    fi
    
    if systemctl is-active vani-ngrok &>/dev/null; then
        print_success "Ngrok service is running"
    else
        print_warning "Ngrok service not running"
        ((WARNINGS++))
    fi
else
    print_error "Ngrok service file not found"
    ((ERRORS++))
fi

# Check 7: Flask endpoint
print_info "Testing Flask endpoint..."
if curl -f http://127.0.0.1:5000 -o /dev/null -s --max-time 5; then
    print_success "Flask is responding on port 5000"
else
    print_error "Flask not responding on port 5000"
    ((ERRORS++))
fi

# Check 8: Ngrok tunnel
print_info "Checking ngrok tunnel..."
if curl -s http://localhost:4040/api/tunnels &>/dev/null; then
    TUNNELS=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('tunnels', [])))" 2>/dev/null || echo "0")
    
    if [ "$TUNNELS" -gt 0 ]; then
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'N/A')" 2>/dev/null || echo "N/A")
        print_success "Ngrok tunnel active: $NGROK_URL"
        
        # Test public URL
        if [ "$NGROK_URL" != "N/A" ]; then
            if curl -f "$NGROK_URL" -o /dev/null -s --max-time 10; then
                print_success "Public URL is accessible"
            else
                print_warning "Public URL not responding"
                ((WARNINGS++))
            fi
        fi
    else
        print_warning "No ngrok tunnels found"
        ((WARNINGS++))
    fi
else
    print_error "Cannot connect to ngrok API"
    ((ERRORS++))
fi

# Check 9: Ngrok config
print_info "Checking ngrok configuration..."
if [ -f ~/.config/ngrok/ngrok.yml ]; then
    print_success "Ngrok config exists"
    
    if grep -q "vani.ngrok.app" ~/.config/ngrok/ngrok.yml; then
        print_success "Static domain configured: vani.ngrok.app"
    else
        print_warning "Static domain not configured"
        ((WARNINGS++))
    fi
else
    print_error "Ngrok config not found"
    ((ERRORS++))
fi

# Check 10: Disk space
print_info "Checking disk space..."
DISK_USAGE=$(df -h /home/postgres/vani | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    print_success "Disk usage: ${DISK_USAGE}%"
else
    print_warning "High disk usage: ${DISK_USAGE}%"
    ((WARNINGS++))
fi

# Summary
print_header "Verification Summary"

echo "Total Checks: 10"
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    print_success "All checks passed! ✅"
    echo ""
    echo "Your VANI deployment is healthy and ready to use!"
    echo ""
    echo "Access your application:"
    echo "  • Public URL: https://vani.ngrok.app"
    echo "  • Login: https://vani.ngrok.app/login"
    echo "  • Command Center: https://vani.ngrok.app/command-center"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    print_warning "Verification completed with warnings"
    echo ""
    echo "Your deployment is working but has some warnings."
    echo "Review the warnings above and fix if necessary."
    echo ""
    exit 0
else
    print_error "Verification failed with $ERRORS error(s)"
    echo ""
    echo "Please fix the errors above before using the application."
    echo ""
    echo "Common fixes:"
    echo "  • Install dependencies: cd /home/postgres/vani && source venv/bin/activate && pip install -r requirements.txt"
    echo "  • Configure environment: nano /home/postgres/vani/.env.local"
    echo "  • Start services: sudo systemctl start vani-flask vani-ngrok"
    echo "  • Check logs: sudo journalctl -u vani-flask -u vani-ngrok -f"
    echo ""
    exit 1
fi

