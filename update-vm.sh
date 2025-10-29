#!/bin/bash
# Update-Script für VM
# Führe auf der VM aus: ./update-vm.sh
echo "🔄 Git Pull..."
git pull origin main
echo "🛑 Stoppe Container..."
docker compose down
echo "🔨 Rebuild Image (mit --no-cache für sauberen Build)..."
docker compose build --no-cache
echo "🚀 Starte Container..."
docker compose up -d
echo "📊 Status Check..."
docker compose ps
echo "📝 Logs (Ctrl+C zum Beenden)..."
docker compose logs -f
