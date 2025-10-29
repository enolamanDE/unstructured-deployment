# 🚀 Unstructured.io Deployment

Docker-basiertes Deployment für unstructured.io Document Processing mit Streamlit UI.

## 📋 Features

- ✅ **Open Source Stack**: Vollständig kostenlos ohne API-Keys
- ✅ **Multi-Format Support**: PDF, DOCX, PPTX, Excel, HTML, Markdown, Bilder
- ✅ **AI Features**: YOLOvX Object Detection, Tesseract OCR, PaddleOCR, Table Transformer
- ✅ **Streamlit UI**: Interaktive Web-Oberfläche für Dokument-Upload und -Verarbeitung
- ✅ **Export-Formate**: Text, JSON, HTML, Markdown, Bedrock RAG JSON
- ✅ **Bild-Extraktion**: Automatische Extraktion und Download von Bildern
- ✅ **Docker Ready**: Einfaches Deployment mit einem Befehl

---

## ⚡ Quick Start (als optimise User)

### Voraussetzungen (einmalig als root)
```bash
# Docker installieren und optimise-User berechtigen
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo usermod -aG docker optimise
sudo systemctl enable docker
sudo systemctl start docker
```

### Installation (als optimise)
```bash
# 1. Repository klonen (privates Repo - braucht Personal Access Token!)
cd ~
git clone https://enolamanDE:[DEIN-TOKEN]@github.com/enolamanDE/unstructured-deployment.git

# Token erstellen: https://github.com/settings/tokens/new
# Berechtigung: "repo" (full control)

# 2. Setup
cd unstructured-deployment
chmod +x *.sh
git config credential.helper store  # Token speichern für Updates

# 3. Erstes Deployment (als root!)
exit  # Zurück zu root
cd /home/optimise/unstructured-deployment
./deploy.sh
```

### Zugriff
```
Lokal:  http://localhost:8501
Extern: http://[VM-IP]:8501
```

---

## 📝 Tägliche Befehle (als optimise)

### Anwendung starten
```bash
cd ~/unstructured-deployment
./start.sh
```

### Anwendung stoppen
```bash
cd ~/unstructured-deployment
./stop.sh
```

### Updates von GitHub + Rebuild
```bash
cd ~/unstructured-deployment
./update.sh
```

### Logs anschauen
```bash
docker compose logs -f
```

### Status prüfen
```bash
docker compose ps
```

---

## 🔄 Workflow

### Als Entwickler (lokal)
```bash
# Code ändern und pushen
cd /home/amu/project/unstructured.io/deployment
git add .
git commit -m "Update XYZ"
git push origin main
```

### Auf VM (als optimise)
```bash
# Updates holen
cd ~/unstructured-deployment
git pull origin main

# Anwendung aktualisieren
./update.sh  # Holt Updates + baut neu + startet
```

---

## 🔧 Erweiterte Befehle

### Manueller Rebuild
```bash
cd ~/unstructured-deployment
docker compose build --no-cache
./start.sh
```

### Container komplett neu erstellen
```bash
docker compose down -v
./deploy.sh
```

### Alte Images aufräumen
```bash
docker image prune -a
```

---

## 🔥 Firewall

Das `deploy.sh` Script prüft automatisch die Firewall und bietet an, Port 8501 zu öffnen.

**Manuell:**
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8501/tcp
sudo ufw reload

# FirewallD (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

---

## 📂 Verzeichnis-Struktur

```
~/unstructured-deployment/
├── deploy.sh                     # Erstes Deployment (alle Features)
├── start.sh                      # Schnellstart (täglich)
├── stop.sh                       # Stoppen
├── update.sh                     # Updates + Rebuild
├── docker-compose.yml            # Docker-Konfiguration
├── Dockerfile                    # Image-Definition
├── app_open_source_recovered.py # Streamlit-App
├── pptx_helpers.py              # Helper-Funktionen
├── requirements.txt             # Python-Dependencies
├── test_files/                  # Upload-Verzeichnis (automatisch erstellt)
└── logs/                        # Logs (automatisch erstellt)
```

---

## 🆘 Troubleshooting

### Docker Permission Denied
```bash
# Prüfe ob optimise in docker-Gruppe
groups

# Falls nicht: als root ausführen
sudo usermod -aG docker optimise

# Dann NEU einloggen (wichtig!)
exit
ssh optimise@vm-ip
```

### Container startet nicht
```bash
# Logs anschauen
docker compose logs

# Neu starten
./stop.sh && ./start.sh
```

### Port 8501 bereits belegt
```bash
# Prüfe was Port nutzt
sudo lsof -i :8501

# Container stoppen
docker compose down

# Neu starten
./start.sh
```

### Git Pull schlägt fehl (private Repo)
```bash
# Credentials neu eingeben
cd ~/unstructured-deployment
git config credential.helper store
git pull origin main
# Username: enolamanDE
# Password: [DEIN-PERSONAL-ACCESS-TOKEN]
```

---

## 🔐 GitHub Personal Access Token

**Erstellen:**
1. https://github.com/settings/tokens/new
2. Name: "VM Deployment"
3. Expiration: No expiration (oder 1 Jahr)
4. Berechtigung: ✅ **repo** (full control)
5. "Generate token" → **SOFORT KOPIEREN!**

**Verwenden:**
```bash
# Beim Klonen
git clone https://enolamanDE:[TOKEN]@github.com/enolamanDE/unstructured-deployment.git

# Für zukünftige Pulls speichern
git config credential.helper store
```

---

## 🎯 Best Practices

### Regelmäßige Updates
```bash
# Einmal täglich/wöchentlich
cd ~/unstructured-deployment
./update.sh
```

### Logs prüfen
```bash
# Letzte 50 Zeilen
docker compose logs --tail=50

# Live-Logs
docker compose logs -f
```

### Container-Status
```bash
# Alle Container anzeigen
docker compose ps

# Ressourcen-Nutzung
docker stats
```

---

## 📊 System-Anforderungen

- **RAM**: Mindestens 8 GB (empfohlen 16 GB)
- **Speicher**: Mindestens 10 GB frei
- **Docker**: Version 20.10+
- **Docker Compose**: Version 1.29+ oder Docker Compose Plugin
- **OS**: Ubuntu 20.04+, Debian 10+, CentOS 8+, oder vergleichbar

---

## 🚀 Architektur

- **Base Image**: `downloads.unstructured.io/unstructured-io/unstructured:latest`
- **Frontend**: Streamlit 1.28.0
- **Processing**: Unstructured.io Open Source Library
- **Features**: YOLOvX, Tesseract, PaddleOCR, Table Transformer (alle inklusive)
- **User**: Container läuft als `optimise` (UID 1000)
- **Port**: 8501 (extern erreichbar via 0.0.0.0)

---

## 📞 Support

**Bei Problemen:**
1. Logs prüfen: `docker compose logs`
2. Status prüfen: `docker compose ps`
3. Container neu starten: `./stop.sh && ./start.sh`
4. Komplett neu bauen: `./update.sh`

---

## 📄 Lizenz

Basiert auf [unstructured.io](https://github.com/Unstructured-IO/unstructured) - Apache 2.0 License

---

**Erstellt:** 2025-10-29  
**Für:** Optimise User Workflow mit privatem GitHub Repository

