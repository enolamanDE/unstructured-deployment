#!/bin/bash

# ============================================
# GitHub VM-Deployment Quick Start
# ============================================
# Dieses Script hilft dir, den Code via GitHub auf die VM zu deployen

set -e

echo "🚀 GitHub VM-Deployment Helper"
echo "================================"
echo ""

# ============================================
# Konfiguration
# ============================================
read -p "GitHub Username: " GITHUB_USER
read -p "Repository Name: " REPO_NAME
read -p "Branch (default: main): " BRANCH
BRANCH=${BRANCH:-main}
read -p "VM IP-Adresse: " VM_IP
read -p "VM Benutzer: " VM_USER
read -p "Zielverzeichnis auf VM (default: /opt): " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-/opt}

echo ""
echo "📋 Konfiguration:"
echo "   GitHub: https://github.com/$GITHUB_USER/$REPO_NAME"
echo "   Branch: $BRANCH"
echo "   VM: $VM_USER@$VM_IP"
echo "   Ziel: $TARGET_DIR/$REPO_NAME"
echo ""
read -p "Fortfahren? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 1
fi

# ============================================
# 1. Lokale Änderungen zu GitHub pushen
# ============================================
echo ""
echo "📤 Schritt 1/4: Pushe Code zu GitHub..."
git add deployment/
git commit -m "Add Docker deployment setup - $(date +%Y-%m-%d)" || echo "Keine Änderungen zum committen"
git push origin $BRANCH

if [ $? -eq 0 ]; then
    echo "✅ Code erfolgreich zu GitHub gepusht"
else
    echo "⚠️  Push fehlgeschlagen - Code könnte schon aktuell sein"
fi

# ============================================
# 2. SSH-Verbindung zur VM testen
# ============================================
echo ""
echo "🔌 Schritt 2/4: Teste SSH-Verbindung zur VM..."
ssh -o ConnectTimeout=5 $VM_USER@$VM_IP "echo '✅ SSH-Verbindung erfolgreich'"

if [ $? -ne 0 ]; then
    echo "❌ Kann nicht zur VM verbinden!"
    echo "   Prüfe: ssh $VM_USER@$VM_IP"
    exit 1
fi

# ============================================
# 3. Auf VM: Repository klonen/updaten
# ============================================
echo ""
echo "📥 Schritt 3/4: Hole Code auf VM..."

# Prüfen ob Repository bereits existiert
ssh $VM_USER@$VM_IP "test -d $TARGET_DIR/$REPO_NAME" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   Repository existiert bereits - führe git pull aus..."
    ssh $VM_USER@$VM_IP "cd $TARGET_DIR/$REPO_NAME && git pull origin $BRANCH"
else
    echo "   Klone Repository..."
    ssh $VM_USER@$VM_IP "cd $TARGET_DIR && git clone https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

if [ $? -eq 0 ]; then
    echo "✅ Code erfolgreich auf VM"
else
    echo "❌ Fehler beim Holen des Codes"
    exit 1
fi

# ============================================
# 4. Deployment auf VM starten
# ============================================
echo ""
echo "🐳 Schritt 4/4: Starte Docker-Deployment auf VM..."
ssh $VM_USER@$VM_IP "cd $TARGET_DIR/$REPO_NAME/deployment && chmod +x deploy.sh && ./deploy.sh"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "🎉 DEPLOYMENT ERFOLGREICH!"
    echo "============================================"
    echo ""
    echo "📱 Anwendung erreichbar unter:"
    echo "   🌐 http://$VM_IP:8501"
    echo ""
    echo "📊 Nützliche Befehle auf VM:"
    echo "   Logs:      ssh $VM_USER@$VM_IP 'cd $TARGET_DIR/$REPO_NAME/deployment && docker-compose logs -f'"
    echo "   Status:    ssh $VM_USER@$VM_IP 'cd $TARGET_DIR/$REPO_NAME/deployment && docker-compose ps'"
    echo "   Stoppen:   ssh $VM_USER@$VM_IP 'cd $TARGET_DIR/$REPO_NAME/deployment && docker-compose down'"
    echo ""
else
    echo "❌ Deployment fehlgeschlagen"
    echo "   Logs prüfen: ssh $VM_USER@$VM_IP 'cd $TARGET_DIR/$REPO_NAME/deployment && docker-compose logs'"
    exit 1
fi

# ============================================
# 5. Anwendung im Browser öffnen
# ============================================
echo ""
read -p "Browser öffnen? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://$VM_IP:8501"
    elif command -v open &> /dev/null; then
        open "http://$VM_IP:8501"
    else
        echo "Öffne manuell: http://$VM_IP:8501"
    fi
fi

echo ""
echo "✅ Fertig!"

