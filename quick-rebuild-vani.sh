#!/bin/bash
# Quick Rebuild Script for VANI
# Rebuilds VANI Docker image and restarts container
# Usage: ./quick-rebuild-vani.sh [--no-cache]

set -e

cd /home/postgres/vani

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VANI Quick Rebuild"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if --no-cache flag is provided
if [ "$1" = "--no-cache" ]; then
    echo "🔄 Rebuilding VANI image (no cache)..."
    docker compose -p vani build --no-cache
else
    echo "🔄 Rebuilding VANI image..."
    docker compose -p vani build
fi

echo ""
echo "🚀 Starting VANI container..."
docker compose -p vani up -d

echo ""
echo "⏳ Waiting for container to start..."
sleep 5

echo ""
echo "📊 Container Status:"
docker compose -p vani ps

echo ""
echo "✅ VANI rebuild complete!"
echo ""
echo "View logs: docker compose -p vani logs -f"
echo "Check health: curl http://localhost:5000/health"

