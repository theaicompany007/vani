#!/bin/bash
# Start ngrok tunnels for both Next.js applications
# This script starts two separate ngrok processes for:
# - theaicompany.ngrok.app -> localhost:3000
# - revenuegrowth.ngrok.app -> localhost:3001

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
THEAI_COMPANY_ROOT="$PROJECT_ROOT/../theaicompany-web"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    log_error "ngrok is not installed. Please install ngrok first."
    exit 1
fi

# Function to get auth token from config
get_auth_token() {
    local config_file="$1"
    if [ ! -f "$config_file" ]; then
        log_error "Config file not found: $config_file"
        return 1
    fi
    
    # Extract authtoken using Python or jq (prefer Python as it's more likely available)
    python3 -c "import json, sys; config = json.load(open('$config_file')); account = config.get('accounts', {}).get(config.get('active_account', 'theaicompany007'), {}); print(account.get('authtoken', ''))" 2>/dev/null || \
    jq -r '.accounts[.active_account].authtoken' "$config_file" 2>/dev/null || \
    grep -o '"authtoken"[[:space:]]*:[[:space:]]*"[^"]*"' "$config_file" | head -1 | sed 's/.*"authtoken"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
}

# Function to get domain from config
get_domain() {
    local config_file="$1"
    local env="${2:-prod}"
    
    if [ ! -f "$config_file" ]; then
        log_error "Config file not found: $config_file"
        return 1
    fi
    
    python3 -c "import json, sys; config = json.load(open('$config_file')); print(config.get('domains', {}).get('$env', ''))" 2>/dev/null || \
    jq -r ".domains.$env" "$config_file" 2>/dev/null || \
    echo ""
}

# Stop any existing ngrok processes
log_info "Stopping any existing ngrok processes..."
pkill -f "ngrok http" || true
sleep 2

# Get configurations
THEAI_COMPANY_CONFIG="$THEAI_COMPANY_ROOT/ngrok.config.json"
ONLYNE_CONFIG="$PROJECT_ROOT/ngrok.config.json"

THEAI_COMPANY_TOKEN=$(get_auth_token "$THEAI_COMPANY_CONFIG")
THEAI_COMPANY_DOMAIN=$(get_domain "$THEAI_COMPANY_CONFIG" "prod")

ONLYNE_TOKEN=$(get_auth_token "$ONLYNE_CONFIG")
ONLYNE_DOMAIN=$(get_domain "$ONLYNE_CONFIG" "prod")

if [ -z "$THEAI_COMPANY_TOKEN" ] || [ -z "$THEAI_COMPANY_DOMAIN" ]; then
    log_error "Failed to get theaicompany-web ngrok configuration"
    exit 1
fi

if [ -z "$ONLYNE_TOKEN" ] || [ -z "$ONLYNE_DOMAIN" ]; then
    log_error "Failed to get onlynereputation-agentic-app ngrok configuration"
    exit 1
fi

log_info "Starting ngrok tunnel for theaicompany-web..."
log_info "  Domain: $THEAI_COMPANY_DOMAIN"
log_info "  Port: 3000"

# Start ngrok for theaicompany-web
export NGROK_AUTHTOKEN="$THEAI_COMPANY_TOKEN"
nohup ngrok http 3000 \
    --domain="$THEAI_COMPANY_DOMAIN" \
    --authtoken="$THEAI_COMPANY_TOKEN" \
    --host-header=localhost \
    --log=stdout \
    > "$PROJECT_ROOT/ngrok-theaicompany.log" 2>&1 &

THEAI_COMPANY_PID=$!
echo $THEAI_COMPANY_PID > "$PROJECT_ROOT/ngrok-theaicompany.pid"
log_info "Started ngrok for theaicompany-web (PID: $THEAI_COMPANY_PID)"

sleep 3

log_info "Starting ngrok tunnel for onlynereputation-agentic-app..."
log_info "  Domain: $ONLYNE_DOMAIN"
log_info "  Port: 3001"

# Start ngrok for onlynereputation-agentic-app
export NGROK_AUTHTOKEN="$ONLYNE_TOKEN"
nohup ngrok http 3001 \
    --domain="$ONLYNE_DOMAIN" \
    --authtoken="$ONLYNE_TOKEN" \
    --host-header=localhost \
    --log=stdout \
    > "$PROJECT_ROOT/ngrok-onlynereputation.log" 2>&1 &

ONLYNE_PID=$!
echo $ONLYNE_PID > "$PROJECT_ROOT/ngrok-onlynereputation.pid"
log_info "Started ngrok for onlynereputation-agentic-app (PID: $ONLYNE_PID)"

log_info "Waiting for tunnels to establish..."
sleep 5

# Verify tunnels
log_info "Verifying tunnels..."
if ps -p $THEAI_COMPANY_PID > /dev/null && ps -p $ONLYNE_PID > /dev/null; then
    log_info "Both ngrok processes are running"
    log_info "Check logs:"
    log_info "  - theaicompany-web: $PROJECT_ROOT/ngrok-theaicompany.log"
    log_info "  - onlynereputation: $PROJECT_ROOT/ngrok-onlynereputation.log"
    log_info ""
    log_info "Tunnels should be available at:"
    log_info "  - https://$THEAI_COMPANY_DOMAIN"
    log_info "  - https://$ONLYNE_DOMAIN"
else
    log_warn "One or both ngrok processes may have failed to start"
    log_warn "Check the log files for details"
fi














