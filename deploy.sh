#!/bin/bash

# ============================================
# Unstructured.io Streamlit Prototype - Deployment Script
# ============================================

set -e  # Exit bei Fehler

echo "🚀 Starting Unstructured.io Prototype Deployment..."
echo ""

# ============================================
# 1. Prüfe Docker Installation
# ============================================
echo "📋 Schritt 1/5: Prüfe Docker-Installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert!"
    echo "   Installiere Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose ist nicht installiert!"
    echo "   Installiere Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "✅ Docker und Docker Compose gefunden"
echo ""

# ============================================
# 2. Erstelle notwendige Verzeichnisse
# ============================================
echo "📁 Schritt 2/5: Erstelle Verzeichnisse..."
mkdir -p test_files
mkdir -p logs
echo "✅ Verzeichnisse erstellt: test_files/, logs/"
echo ""

# ============================================
# 3. Stoppe laufende Container (falls vorhanden)
# ============================================
echo "🛑 Schritt 3/5: Stoppe alte Container..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
echo "✅ Alte Container gestoppt"
echo ""

# ============================================
# 4. Baue Docker Image
# ============================================
echo "🔨 Schritt 4/5: Baue Docker Image..."
echo "   ⚠️  Dies kann beim ersten Mal 5-10 Minuten dauern!"
echo "   ⚠️  Das offizielle unstructured.io Image wird heruntergeladen (~2-3 GB)"
echo ""

if docker compose version &> /dev/null; then
    docker compose build --progress=plain
else
    docker-compose build --progress=plain
fi
echo ""
echo "✅ Docker Image erfolgreich gebaut"
echo ""

# ============================================
# 5. Starte Container
# ============================================
echo "▶️  Schritt 5/5: Starte Container..."
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi
echo ""

# ============================================
# Warte auf Streamlit Start
# ============================================
echo "⏳ Warte auf Streamlit-Start (max. 60 Sekunden)..."
COUNTER=0
MAX_WAIT=60
while [ $COUNTER -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo ""
        echo "✅ Streamlit ist bereit!"
        break
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 2))
done

if [ $COUNTER -ge $MAX_WAIT ]; then
    echo ""
    echo "⚠️  Timeout beim Warten auf Streamlit!"
    echo "   Prüfe die Logs mit: docker-compose logs -f"
fi

echo ""
echo "============================================"
echo "🎉 DEPLOYMENT ERFOLGREICH!"
echo "============================================"
echo ""
echo "📱 Anwendung erreichbar unter:"
echo "   🌐 http://localhost:8501"
echo ""
echo "📊 Nützliche Befehle:"
echo "   Logs anzeigen:    docker-compose logs -f"
echo "   Container stoppen: docker-compose down"
echo "   Neu starten:      docker-compose restart"
echo "   Status prüfen:    docker-compose ps"
echo ""
echo "📂 Volumes:"
echo "   Uploads:  ./test_files/"
echo "   Logs:     ./logs/"
echo ""
echo "🔧 Technische Details:"
echo "   Base Image: downloads.unstructured.io/unstructured-io/unstructured:latest"
echo "   Container:  unstructured-prototype"
echo "   Port:       8501"
echo ""
echo "✅ Bereit zum Testen!"
echo ""

