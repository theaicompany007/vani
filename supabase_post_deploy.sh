#!/bin/bash
# Supabase Post-Deploy Script for VANI
# Updates Supabase webhooks and Auth configuration after deployment
# Location: /home/postgres/vani/supabase_post_deploy.sh
#
# This script:
# 1. Sources .env.local to get Supabase credentials and webhook URLs
# 2. Updates Supabase webhooks (Resend, Twilio, Cal.com)
# 3. Updates Supabase Auth configuration (Site URL, Redirect URLs)
#
# Usage: Called automatically by manage-vani.sh full-deploy
#        Can also be run manually: ./supabase_post_deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Supabase Post-Deploy: VANI Outreach Command Center${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo -e "${RED}❌ Error: .env.local not found in $(pwd)${NC}"
    exit 1
fi

# Source .env.local to get environment variables
echo -e "${YELLOW}📥 Loading environment variables from .env.local...${NC}"
set -a
source .env.local
set +a

# Check required variables
if [ -z "$SUPABASE_URL" ]; then
    echo -e "${RED}❌ Error: SUPABASE_URL not found in .env.local${NC}"
    exit 1
fi

if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ Error: SUPABASE_ACCESS_TOKEN not found in .env.local${NC}"
    echo -e "${YELLOW}💡 Get your access token from: https://supabase.com/dashboard/account/tokens${NC}"
    exit 1
fi

# Get webhook base URL
WEBHOOK_BASE_URL="${WEBHOOK_BASE_URL:-}"
if [ -z "$WEBHOOK_BASE_URL" ]; then
    echo -e "${YELLOW}⚠️  Warning: WEBHOOK_BASE_URL not set, using default${NC}"
    WEBHOOK_BASE_URL="https://vani.ngrok.app"
fi

echo -e "${CYAN}Configuration:${NC}"
echo "  Supabase URL: $SUPABASE_URL"
echo "  Webhook Base URL: $WEBHOOK_BASE_URL"
echo ""

# Update Supabase Auth configuration using env-audit script
if [ -f "vani-env-audit.py" ]; then
    echo -e "${YELLOW}📝 Updating Supabase Auth configuration...${NC}"
    python3 vani-env-audit.py --update-auth-config --webhook-base-url "$WEBHOOK_BASE_URL" --env-file .env.local
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Supabase Auth configuration updated${NC}"
    else
        echo -e "${RED}❌ Failed to update Supabase Auth configuration${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  vani-env-audit.py not found, skipping Auth config update${NC}"
fi

# Update webhooks using configure_webhooks.py script
if [ -f "scripts/configure_webhooks.py" ]; then
    echo ""
    echo -e "${YELLOW}📝 Updating webhooks (Resend, Twilio, Cal.com)...${NC}"
    python3 scripts/configure_webhooks.py --webhook-base-url "$WEBHOOK_BASE_URL" --env-file .env.local
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Webhooks updated${NC}"
    else
        echo -e "${YELLOW}⚠️  Webhook update failed or skipped${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  scripts/configure_webhooks.py not found, skipping webhook update${NC}"
fi

echo ""
echo -e "${GREEN}✅ Supabase post-deploy completed!${NC}"
echo ""

