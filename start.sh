#!/bin/bash

# ============================================
# Quick Start - Als optimise User
# ============================================
# Startet die Anwendung ohne kompletten Rebuild

echo "🚀 Starte Unstructured.io Anwendung..."
echo ""

cd "$(dirname "$0")"

# Stoppe alte Container
echo "🛑 Stoppe alte Container..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null
echo ""

# Starte Container
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
echo "✅ Anwendung läuft!"
echo "============================================"
echo ""
echo "🌐 Zugriff:"
echo "   Lokal:  http://localhost:8501"
if [ ! -z "$VM_IP" ]; then
    echo "   Extern: http://$VM_IP:8501"
fi
echo ""
echo "📊 Befehle:"
echo "   Logs:    docker compose logs -f"
echo "   Stoppen: ./stop.sh"
echo "   Status:  docker compose ps"
echo ""

