#!/bin/bash
# Deploy both Next.js applications to VM
# This script builds Docker images, updates docker-compose, and restarts services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
THEAI_COMPANY_ROOT="$PROJECT_ROOT/../theaicompany-web"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're on the VM (check for docker-compose.worker.yml)
if [ ! -f "$PROJECT_ROOT/docker-compose.worker.yml" ]; then
    log_error "docker-compose.worker.yml not found. Are you on the VM?"
    exit 1
fi

log_step "Deploying Next.js applications to VM"

# Step 1: Verify both projects exist
log_step "1. Verifying project directories..."
if [ ! -d "$THEAI_COMPANY_ROOT" ]; then
    log_error "theaicompany-web directory not found at: $THEAI_COMPANY_ROOT"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    log_error "onlynereputation-agentic-app directory not found at: $PROJECT_ROOT"
    exit 1
fi

log_info "Both project directories found"

# Step 2: Build Docker images
log_step "2. Building Docker images..."

log_info "Building theaicompany-web..."
cd "$THEAI_COMPANY_ROOT"
docker build -f docker/Dockerfile -t theaicompany-web:latest . || {
    log_error "Failed to build theaicompany-web image"
    exit 1
}

log_info "Building onlynereputation-agentic-app..."
cd "$PROJECT_ROOT"
docker build -f Dockerfile -t onlynereputation-app:latest . || {
    log_error "Failed to build onlynereputation-agentic-app image"
    exit 1
}

log_info "Both images built successfully"

# Step 3: Update docker-compose services
log_step "3. Updating docker-compose services..."
cd "$PROJECT_ROOT"

# Stop existing services if running
log_info "Stopping existing services..."
docker-compose -f docker-compose.worker.yml stop theaicompany-web onlynereputation-app 2>/dev/null || true

# Start/restart services
log_info "Starting services..."
docker-compose -f docker-compose.worker.yml up -d theaicompany-web onlynereputation-app || {
    log_error "Failed to start services"
    exit 1
}

log_info "Services started"

# Step 4: Wait for services to be healthy
log_step "4. Waiting for services to be healthy..."
sleep 10

# Check health
log_info "Checking service health..."
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    log_info "✓ theaicompany-web is healthy"
else
    log_warn "⚠ theaicompany-web health check failed"
fi

if curl -f http://localhost:3001/api/health > /dev/null 2>&1; then
    log_info "✓ onlynereputation-app is healthy"
else
    log_warn "⚠ onlynereputation-app health check failed"
fi

# Step 5: Restart ngrok tunnels
log_step "5. Restarting ngrok tunnels..."
if [ -f "$PROJECT_ROOT/scripts/stop-ngrok-tunnels.sh" ]; then
    bash "$PROJECT_ROOT/scripts/stop-ngrok-tunnels.sh"
    sleep 2
fi

if [ -f "$PROJECT_ROOT/scripts/start-ngrok-tunnels.sh" ]; then
    bash "$PROJECT_ROOT/scripts/start-ngrok-tunnels.sh"
else
    log_warn "ngrok start script not found. Please start ngrok manually."
fi

# Step 6: Show status
log_step "6. Deployment Summary"
echo ""
log_info "Docker containers:"
docker-compose -f docker-compose.worker.yml ps theaicompany-web onlynereputation-app

echo ""
log_info "Service URLs:"
log_info "  - theaicompany-web: http://localhost:3000"
log_info "  - onlynereputation-app: http://localhost:3001"

echo ""
log_info "ngrok tunnels (if started):"
log_info "  - https://theaicompany.ngrok.app -> localhost:3000"
log_info "  - https://revenuegrowth.ngrok.app -> localhost:3001"

echo ""
log_info "Deployment complete!"














