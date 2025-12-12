#!/bin/bash
# VANI Deployment Script for chroma-vm
# Run this ON chroma-vm after cloning the repository
set -e

echo "============================================"
echo "VANI Docker Deployment to chroma-vm"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[1/9] Creating .env.local...${NC}"
cd /home/postgres/vani

# Create .env.local - USER MUST EDIT THIS WITH ACTUAL VALUES
cat > .env.local << 'EOF'
# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_ENV=production
SECRET_KEY=REPLACE_WITH_RANDOM_SECRET_KEY

# Supabase - REPLACE WITH YOUR ACTUAL VALUES
SUPABASE_URL=https://REPLACE.supabase.co
SUPABASE_KEY=REPLACE_WITH_YOUR_ANON_KEY
SUPABASE_SERVICE_KEY=REPLACE_WITH_YOUR_SERVICE_KEY
SUPABASE_CONNECTION=postgresql://postgres:password@host:5432/postgres
SUPABASE_DB_PASSWORD=REPLACE_WITH_DB_PASSWORD

# Ngrok
WEBHOOK_BASE_URL=https://vani.ngrok.app

# OpenAI - REPLACE THIS
OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY

# Resend - REPLACE THESE
RESEND_API_KEY=re_REPLACE_WITH_YOUR_KEY
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_HIT_EMAIL=notifications@yourdomain.com

# Twilio - REPLACE THESE
TWILIO_ACCOUNT_SID=REPLACE_WITH_SID
TWILIO_AUTH_TOKEN=REPLACE_WITH_TOKEN
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_TO_WHATSAPP_NUMBER=+REPLACE_WITH_YOUR_NUMBER

# Cal.com (optional)
CAL_COM_API_KEY=cal_live_REPLACE_IF_USING
CAL_COM_EVENT_TYPE_ID=REPLACE_IF_USING
CAL_COM_USERNAME=REPLACE_IF_USING

# Google Sheets (optional)
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account"}

# Docker flag
DOCKER_CONTAINER=true

# RAG Service
RAG_SERVICE_URL=https://rag.kcube-consulting.com
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Industry
DEFAULT_INDUSTRY=fmcg
EOF

chmod 600 .env.local
echo -e "${GREEN}✅ .env.local created${NC}"
echo -e "${RED}⚠️  IMPORTANT: Edit .env.local with your actual API keys before continuing!${NC}"
echo ""
read -p "Press Enter after you've edited .env.local with your API keys..."

echo ""
echo -e "${BLUE}[2/9] Updating docker-compose.worker.yml...${NC}"
cd /home/postgres/onlynereputation-agentic-app
sed -i 's|context: ../../vani|context: ../vani|g' docker-compose.worker.yml
echo -e "${GREEN}✅ docker-compose.worker.yml updated${NC}"

echo ""
echo -e "${BLUE}[3/9] Building VANI Docker container...${NC}"
echo "This may take 3-5 minutes..."
docker-compose -f docker-compose.worker.yml build vani
echo -e "${GREEN}✅ VANI container built${NC}"

echo ""
echo -e "${BLUE}[4/9] Starting VANI container...${NC}"
docker-compose -f docker-compose.worker.yml up -d vani
sleep 5
echo -e "${GREEN}✅ VANI container started${NC}"

echo ""
echo -e "${BLUE}[5/9] Checking container status...${NC}"
docker ps | grep vani

echo ""
echo -e "${BLUE}[6/9] Viewing initial logs...${NC}"
docker logs vani --tail 20

echo ""
echo -e "${BLUE}[7/9] Testing health endpoint...${NC}"
sleep 5
if curl -f http://localhost:5000/api/health 2>/dev/null; then
    echo -e "${GREEN}✅ Flask is responding${NC}"
else
    echo -e "${RED}⚠️  Flask not responding yet, check logs with: docker logs vani${NC}"
fi

echo ""
echo -e "${BLUE}[8/9] Restarting ngrok service...${NC}"
sudo systemctl restart onlyne-ngrok.service
sleep 10
echo -e "${GREEN}✅ Ngrok restarted${NC}"

echo ""
echo -e "${BLUE}[9/9] Verifying ngrok tunnels...${NC}"
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[] | "\(.public_url) -> localhost:\(.config.addr)"'

echo ""
echo "============================================"
echo -e "${GREEN}✅ VANI Deployment Complete!${NC}"
echo "============================================"
echo ""
echo "Access VANI at:"
echo "  • https://vani.ngrok.app"
echo "  • https://vani.ngrok.app/login"
echo "  • https://vani.ngrok.app/command-center"
echo ""
echo "Next steps:"
echo "  1. Test public access: curl https://vani.ngrok.app/api/health"
echo "  2. Run migrations: docker exec -it vani python do_setup.py"
echo "  3. Create super user: docker exec -it vani python create_super_user.py"
echo "  4. Configure webhooks in Resend, Twilio, Cal.com"
echo ""
echo "View logs: docker logs vani -f"
echo ""

