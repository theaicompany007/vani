#!/bin/bash
# Stop ngrok tunnels for both Next.js applications

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# Stop by PID files if they exist
if [ -f "$PROJECT_ROOT/ngrok-theaicompany.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/ngrok-theaicompany.pid")
    if ps -p $PID > /dev/null 2>&1; then
        log_info "Stopping ngrok for theaicompany-web (PID: $PID)"
        kill $PID || true
    fi
    rm -f "$PROJECT_ROOT/ngrok-theaicompany.pid"
fi

if [ -f "$PROJECT_ROOT/ngrok-onlynereputation.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/ngrok-onlynereputation.pid")
    if ps -p $PID > /dev/null 2>&1; then
        log_info "Stopping ngrok for onlynereputation-agentic-app (PID: $PID)"
        kill $PID || true
    fi
    rm -f "$PROJECT_ROOT/ngrok-onlynereputation.pid"
fi

# Also kill any remaining ngrok processes
log_info "Stopping any remaining ngrok processes..."
pkill -f "ngrok http" || true

log_info "All ngrok tunnels stopped"














