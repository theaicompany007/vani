#!/bin/bash
# Update Environment Variables for VANI
# Edits .env.local and restarts container
# Usage: ./update-env-vani.sh

set -e

cd /home/postgres/vani

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VANI Environment Update"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Backup current .env.local
if [ -f .env.local ]; then
    echo "📦 Backing up current .env.local..."
    cp .env.local .env.local.backup.$(date +%Y%m%d_%H%M%S)
fi

# Fix line endings if needed (in case file was edited on Windows)
if command -v dos2unix &> /dev/null; then
    dos2unix .env.local 2>/dev/null || true
else
    sed -i 's/\r$//' .env.local 2>/dev/null || true
fi

# Open editor
echo "📝 Opening .env.local for editing..."
echo "   (Press Ctrl+X, then Y, then Enter to save in nano)"
echo ""
nano .env.local

# Fix line endings after editing (in case editor added CRLF)
if command -v dos2unix &> /dev/null; then
    dos2unix .env.local 2>/dev/null || true
else
    sed -i 's/\r$//' .env.local 2>/dev/null || true
fi

# Ask if Supabase URLs changed
echo ""
read -p "Did you change Supabase URLs or webhook URLs? (y/n): " supabase_changed

if [ "$supabase_changed" = "y" ] || [ "$supabase_changed" = "Y" ]; then
    echo ""
    echo "🔄 Restarting with full deployment (updates Supabase)..."
    ./manage-vani.sh full-deploy
else
    echo ""
    echo "🔄 Restarting container to load new environment variables..."
    ./manage-vani.sh restart
fi

echo ""
echo "✅ Environment update complete!"
echo ""
echo "Verify variables: docker compose -p vani exec vani-app env | grep YOUR_VAR"

