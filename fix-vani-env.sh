#!/bin/bash
# Fix VANI .env.local - Line Endings and Docker Settings
# Usage: ./fix-vani-env.sh

set -e

cd /home/postgres/vani

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Fixing VANI .env.local"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f .env.local ]; then
    echo "❌ Error: .env.local not found"
    exit 1
fi

# Backup
echo "📦 Creating backup..."
cp .env.local .env.local.backup.$(date +%Y%m%d_%H%M%S)

# Fix line endings
echo "🔧 Fixing line endings (CRLF → LF)..."
sed -i 's/\r$//' .env.local

# Fix Redis host for Docker
echo "🔧 Updating Redis configuration for Docker..."
sed -i 's/^REDIS_HOST=127.0.0.1/REDIS_HOST=redis/' .env.local
sed -i 's/^REDIS_HOST=localhost/REDIS_HOST=redis/' .env.local

# Fix Flask host for Docker
echo "🔧 Updating Flask host for Docker..."
sed -i 's/^FLASK_HOST=127.0.0.1/FLASK_HOST=0.0.0.0/' .env.local
sed -i 's/^FLASK_HOST=localhost/FLASK_HOST=0.0.0.0/' .env.local

# Add REDIS_URL if not present
if ! grep -q "^REDIS_URL=" .env.local; then
    echo "🔧 Adding REDIS_URL..."
    echo "" >> .env.local
    echo "# Redis URL for Docker network" >> .env.local
    echo "REDIS_URL=redis://redis:6379" >> .env.local
fi

echo ""
echo "✅ .env.local fixed!"
echo ""
echo "📋 Summary of changes:"
echo "  - Fixed line endings (CRLF → LF)"
echo "  - Updated REDIS_HOST to 'redis' (Docker service name)"
echo "  - Updated FLASK_HOST to '0.0.0.0' (for Docker)"
echo "  - Added REDIS_URL if missing"
echo ""
echo "🔄 Restarting VANI to apply changes..."
./manage-vani.sh restart

echo ""
echo "✅ Done! Check logs: docker compose -p vani logs -f"

