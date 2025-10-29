#!/bin/bash

# ============================================
# Stop - Als optimise User
# ============================================

echo "🛑 Stoppe Unstructured.io Anwendung..."
echo ""

cd "$(dirname "$0")"

docker compose down 2>/dev/null || docker-compose down 2>/dev/null

echo ""
echo "✅ Container gestoppt!"
echo ""

