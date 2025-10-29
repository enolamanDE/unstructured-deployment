# 🚀 Unstructured.io - Anleitung für optimise User

## 📋 Übersicht

Als `optimise` User kannst du die Anwendung **komplett selbstständig** verwalten:
- ✅ Starten/Stoppen
- ✅ Updates von GitHub holen
- ✅ Code-Änderungen deployen
- ✅ Logs anschauen

**Docker muss nur einmal als root installiert sein!**

---

## 🚀 Schnellstart

### Erste Installation (als root):
```bash
# NUR EINMAL nötig - Docker installieren
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo usermod -aG docker optimise  # optimise zur docker-Gruppe
sudo systemctl enable docker
sudo systemctl start docker
```

### Repository klonen (als optimise):
```bash
# Als optimise User
cd ~
git clone https://github.com/enolamanDE/unstructured-deployment.git
cd unstructured-deployment
chmod +x *.sh
```

### Erste Deployment (als optimise):
```bash
./deploy.sh
```

---

## 📝 Tägliche Befehle (als optimise)

### ▶️ Anwendung starten
```bash
cd ~/unstructured-deployment
./start.sh
```

### 🛑 Anwendung stoppen
```bash
cd ~/unstructured-deployment
./stop.sh
```

### 🔄 Update von GitHub + Rebuild
```bash
cd ~/unstructured-deployment
./update.sh
```

### 📊 Logs anschauen
```bash
cd ~/unstructured-deployment
docker compose logs -f
```

### 🔍 Status prüfen
```bash
cd ~/unstructured-deployment
docker compose ps
```

---

## 🔧 Erweiterte Befehle

### Nur Code aktualisieren (ohne Rebuild)
```bash
cd ~/unstructured-deployment
git pull origin main
./start.sh
```

### Manueller Rebuild (bei Dockerfile-Änderungen)
```bash
cd ~/unstructured-deployment
docker compose build --no-cache
./start.sh
```

### Container komplett neu erstellen
```bash
cd ~/unstructured-deployment
docker compose down -v  # Löscht auch Volumes!
./deploy.sh
```

### Alte Images aufräumen
```bash
docker image prune -a
```

---

## 🌐 Zugriff auf Anwendung

- **Lokal auf VM:** http://localhost:8501
- **Extern von PC:** http://[VM-IP]:8501

**VM-IP herausfinden:**
```bash
hostname -I | awk '{print $1}'
```

---

## 🔥 Firewall (falls nötig)

**UFW (Ubuntu/Debian):**
```bash
sudo ufw allow 8501/tcp
sudo ufw reload
```

**FirewallD (CentOS/RHEL):**
```bash
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

---

## 📂 Verzeichnis-Struktur

```
~/unstructured-deployment/
├── deploy.sh              # Komplettes Deployment (erstes Mal)
├── start.sh              # Schnellstart (täglich)
├── stop.sh               # Stoppen
├── update.sh             # Update von GitHub + Rebuild
├── docker-compose.yml    # Docker-Konfiguration
├── Dockerfile            # Image-Definition
├── app_open_source_recovered.py  # Streamlit-App
├── pptx_helpers.py       # Helper-Funktionen
├── test_files/           # Upload-Verzeichnis
└── logs/                 # Log-Dateien
```

---

## 🆘 Troubleshooting

### Problem: Docker Permission Denied
```bash
# Prüfe ob optimise in docker-Gruppe ist
groups

# Falls "docker" NICHT in der Liste:
# Als root ausführen:
sudo usermod -aG docker optimise

# Dann NEU einloggen (wichtig!)
exit
ssh optimise@vm-ip
```

### Problem: Container startet nicht
```bash
# Logs anschauen
docker compose logs

# Status prüfen
docker compose ps

# Neu starten
./stop.sh
./start.sh
```

### Problem: Port 8501 bereits belegt
```bash
# Prüfe was Port 8501 nutzt
sudo lsof -i :8501

# Alten Container stoppen
docker compose down

# Neu starten
./start.sh
```

### Problem: Git Pull schlägt fehl
```bash
# Lokale Änderungen verwerfen
git reset --hard origin/main
git pull origin main
```

---

## ✅ Best Practices

### Regelmäßige Updates
```bash
# Jeden Tag/Woche ausführen:
cd ~/unstructured-deployment
./update.sh
```

### Logs regelmäßig prüfen
```bash
# Letzte 50 Zeilen:
docker compose logs --tail=50

# Live-Logs:
docker compose logs -f
```

### Backups (optional)
```bash
# Wichtige Dateien sichern:
tar -czf backup-$(date +%Y%m%d).tar.gz test_files/ logs/
```

---

## 📞 Support

Bei Problemen:
1. Logs prüfen: `docker compose logs`
2. Status prüfen: `docker compose ps`
3. Container neu starten: `./stop.sh && ./start.sh`
4. Komplett neu bauen: `./update.sh`

---

**🎉 Viel Erfolg!**

