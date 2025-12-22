#!/bin/bash
# VANI Outreach Command Center Management Script
# Manages VANI application
# Location: /home/postgres/vani/manage-vani.sh
#
# Usage:
#   ./manage-vani.sh [start|stop|restart|rebuild|purge|full-deploy|status]
#
# Commands:
#   start       - Start VANI application
#   stop        - Stop VANI application
#   restart     - Restart VANI application
#   rebuild     - Rebuild and restart application
#   purge       - Stop and remove containers/networks (keeps volumes, only affects vani project)
#   full-deploy - Full deployment: rebuild, restart, update Supabase config
#   status      - Show status of VANI application
#
# Notes:
#   - Requires infrastructure (RAG/ChromaDB/Redis) to be running
#   - Connects to shared-infra-network to access RAG/ChromaDB AND Redis
#   - Purge only affects vani project, not infrastructure or other projects

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="vani"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  VANI Outreach Command Center Management${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}❌ Error: $COMPOSE_FILE not found in $(pwd)${NC}"
        exit 1
    fi
}

check_infrastructure() {
    if ! docker network ls | grep -q "shared-infra-network"; then
        echo -e "${RED}❌ Error: shared-infra-network not found${NC}"
        echo -e "${YELLOW}💡 Start infrastructure first: cd /home/postgres/rag-infrastructure && ./manage-infra.sh start${NC}"
        exit 1
    fi
    
    # Check if Redis is running
    if ! docker ps --format "{{.Names}}" | grep -q "^redis$"; then
        echo -e "${YELLOW}⚠️  Warning: Redis container not found${NC}"
        echo -e "${YELLOW}💡 Start infrastructure to ensure Redis is running${NC}"
    fi
}

cmd_start() {
    print_header
    echo -e "${YELLOW}🚀 Starting VANI application...${NC}"
    echo ""
    
    check_compose_file
    check_infrastructure
    
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    
    echo ""
    echo -e "${GREEN}✅ VANI application started!${NC}"
    echo ""
    echo -e "${CYAN}Application:${NC}"
    echo "  - URL: http://localhost:5000"
    echo "  - Health: http://localhost:5000/api/health"
    echo "  - Command Center: http://localhost:5000/command-center"
}

cmd_stop() {
    print_header
    echo -e "${YELLOW}🛑 Stopping VANI application...${NC}"
    echo ""
    
    check_compose_file
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" stop
    
    echo ""
    echo -e "${GREEN}✅ VANI application stopped${NC}"
}

cmd_restart() {
    print_header
    echo -e "${YELLOW}🔄 Restarting VANI application...${NC}"
    echo ""
    
    check_compose_file
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart
    
    echo ""
    echo -e "${GREEN}✅ VANI application restarted${NC}"
}

cmd_rebuild() {
    print_header
    echo -e "${YELLOW}🔨 Rebuilding and restarting VANI application...${NC}"
    echo ""
    
    check_compose_file
    check_infrastructure
    
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --build
    
    echo ""
    echo -e "${GREEN}✅ VANI application rebuilt and started${NC}"
}

cmd_purge() {
    print_header
    echo -e "${RED}🗑️  Purging VANI application...${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  This will:${NC}"
    echo "  - Stop VANI containers"
    echo "  - Remove VANI containers"
    echo "  - Remove VANI networks"
    echo "  - Keep volumes (data preserved)"
    echo "  - Only affects vani project (infrastructure and other projects untouched)"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Cancelled${NC}"
        exit 0
    fi
    
    check_compose_file
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    
    echo ""
    echo -e "${GREEN}✅ VANI application purged${NC}"
}

cmd_full_deploy() {
    print_header
    echo -e "${YELLOW}🚀 Full deployment: Rebuild + Supabase config update...${NC}"
    echo ""
    
    check_compose_file
    check_infrastructure
    
    # Rebuild
    cmd_rebuild
    
    # Wait for service to be healthy
    echo ""
    echo -e "${YELLOW}⏳ Waiting for service to be healthy...${NC}"
    sleep 10
    
    # Run Supabase post-deploy script
    if [ -f "supabase_post_deploy.sh" ]; then
        echo ""
        echo -e "${YELLOW}📝 Updating Supabase configuration...${NC}"
        chmod +x supabase_post_deploy.sh
        ./supabase_post_deploy.sh
    else
        echo -e "${YELLOW}⚠️  supabase_post_deploy.sh not found, skipping Supabase update${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Full deployment completed!${NC}"
}

cmd_status() {
    print_header
    echo -e "${CYAN}📊 VANI Application Status${NC}"
    echo ""
    
    check_compose_file
    
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    
    echo ""
    echo -e "${CYAN}Infrastructure Connection:${NC}"
    if docker network ls | grep -q "shared-infra-network"; then
        echo -e "${GREEN}✅ Connected to shared-infra-network${NC}"
        
        # Check Redis connectivity
        if docker ps --format "{{.Names}}" | grep -q "^redis$"; then
            echo -e "${GREEN}✅ Redis is running${NC}"
        else
            echo -e "${YELLOW}⚠️  Redis not found (should be in infrastructure)${NC}"
        fi
    else
        echo -e "${RED}❌ shared-infra-network not found${NC}"
        echo -e "${YELLOW}💡 Start infrastructure first${NC}"
    fi
}

# Main command dispatcher
case "${1:-}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    rebuild)
        cmd_rebuild
        ;;
    purge)
        cmd_purge
        ;;
    full-deploy)
        cmd_full_deploy
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|rebuild|purge|full-deploy|status}"
        echo ""
        echo "Commands:"
        echo "  start       - Start VANI application"
        echo "  stop        - Stop VANI application"
        echo "  restart     - Restart VANI application"
        echo "  rebuild     - Rebuild and restart application"
        echo "  purge       - Stop and remove containers/networks (keeps volumes)"
        echo "  full-deploy - Full deployment: rebuild + Supabase config update"
        echo "  status      - Show status of application"
        exit 1
        ;;
esac

