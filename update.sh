#!/bin/bash

# ============================================
# Update - Als optimise User
# ============================================
# Aktualisiert Code von GitHub und baut Image neu

echo "🔄 Update Unstructured.io Anwendung..."
echo ""

cd "$(dirname "$0")"

# Git Repository aktualisieren
echo "📥 Hole Updates von GitHub..."
git pull origin main
echo ""

# Container stoppen
echo "🛑 Stoppe Container..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null
echo ""

# Image neu bauen
echo "🔨 Baue neues Image..."
echo "   ⚠️  Dies kann 2-5 Minuten dauern..."
echo ""
docker compose build --no-cache 2>/dev/null || docker-compose build --no-cache 2>/dev/null
echo ""

# Container starten
echo "▶️  Starte Container..."
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null
echo ""

# Warte auf Streamlit
echo "⏳ Warte auf Streamlit..."
COUNTER=0
MAX_WAIT=30
while [ $COUNTER -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ Streamlit ist bereit!"
        break
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 2))
done
echo ""

VM_IP=$(hostname -I | awk '{print $1}')
echo "============================================"
echo "✅ Update erfolgreich!"
echo "============================================"
echo ""
echo "🌐 Zugriff:"
echo "   Lokal:  http://localhost:8501"
if [ ! -z "$VM_IP" ]; then
    echo "   Extern: http://$VM_IP:8501"
fi
echo ""

