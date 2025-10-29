# 📖 Deployment Guide - Unstructured.io Prototype

Detaillierte Schritt-für-Schritt Anleitung für das Docker-Deployment des Unstructured.io Streamlit-Prototypen.

---

## 📋 Übersicht

Dieses Deployment nutzt das **offizielle unstructured.io Docker-Image** als Basis und fügt eine Streamlit-Anwendung hinzu. Das resultierende Setup ist production-ready und enthält alle notwendigen AI/ML-Modelle vorinstalliert.

---

## 🎯 Deployment-Optionen

### Option 1: Automatisches Deployment (Empfohlen)
✅ Am einfachsten  
✅ Fehlerbehandlung integriert  
✅ Automatische Health Checks

### Option 2: Manuelles Deployment
✅ Volle Kontrolle  
✅ Schritt-für-Schritt nachvollziehbar  
✅ Gut für Debugging

### Option 3: VM-Deployment
✅ Für Remote-Server  
✅ Mit Transfer-Anleitung  
✅ Production-Setup

---

## 🚀 Option 1: Automatisches Deployment

### Schritt 1: Vorbereitung

```bash
# In das Deployment-Verzeichnis wechseln
cd /home/amu/project/unstructured.io/deployment

# Prüfen, ob alle Dateien vorhanden sind
ls -lah

# Sollte zeigen:
# - Dockerfile
# - docker-compose.yml
# - deploy.sh
# - app_open_source_recovered.py
# - pptx_helpers.py
# - requirements.txt
```

### Schritt 2: Deploy-Script ausführbar machen

```bash
chmod +x deploy.sh
```

### Schritt 3: Deployment starten

```bash
./deploy.sh
```

**Was passiert:**
1. Docker-Installation wird geprüft
2. Verzeichnisse `test_files/` und `logs/` werden erstellt
3. Alte Container werden gestoppt
4. Offizielles unstructured.io Image wird geladen (~2-3 GB)
5. Anwendungs-Layer mit Streamlit wird gebaut
6. Container wird gestartet
7. Health Check wartet auf Streamlit-Bereitschaft

**Dauer:**
- Erster Start: 5-10 Minuten (Image-Download)
- Nachfolgende Starts: 30-60 Sekunden

### Schritt 4: Erfolg überprüfen

```bash
# Container-Status prüfen
docker-compose ps

# Sollte zeigen:
# NAME                    STATE     PORTS
# unstructured-prototype  Up        0.0.0.0:8501->8501/tcp

# Logs anzeigen
docker-compose logs --tail=50

# Health Check manuell
curl http://localhost:8501/_stcore/health
```

### Schritt 5: Anwendung öffnen

```
http://localhost:8501
```

---

## 🔧 Option 2: Manuelles Deployment

### Schritt 1: Verzeichnisse erstellen

```bash
cd /home/amu/project/unstructured.io/deployment
mkdir -p test_files logs
```

### Schritt 2: Docker Image bauen

```bash
# Mit Docker Compose v2 (empfohlen)
docker compose build

# ODER mit Docker Compose v1
docker-compose build
```

**Erwartete Ausgabe:**
```
[+] Building 120.5s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.2kB
 => [internal] load .dockerignore
 => [unstructured-base 1/1] FROM downloads.unstructured.io/...
 => [app 1/4] RUN pip install streamlit==1.28.0...
 => [app 2/4] COPY app_open_source_recovered.py .
 => [app 3/4] COPY pptx_helpers.py .
 => exporting to image
 => => writing image sha256:abc123...
```

### Schritt 3: Container starten

```bash
# Im Hintergrund starten
docker compose up -d

# ODER: Im Vordergrund (mit Live-Logs)
docker compose up
```

### Schritt 4: Warten auf Streamlit

```bash
# Manuell warten (ca. 30-60 Sekunden)
sleep 60

# Health Check
while ! curl -s http://localhost:8501/_stcore/health > /dev/null; do
    echo "Warte auf Streamlit..."
    sleep 5
done
echo "Streamlit ist bereit!"
```

### Schritt 5: Testen

```bash
# Browser öffnen
xdg-open http://localhost:8501  # Linux
# oder manuell im Browser: http://localhost:8501

# Logs live verfolgen
docker compose logs -f
```

---

## 🌐 Option 3: VM-Deployment

### Schritt 1: Code auf VM übertragen

**Siehe detaillierte Anleitung:** `VM-TRANSFER-GUIDE.md`

**Schnellste Methode:**
```bash
# Von deinem lokalen System (WSL)
cd /home/amu/project/unstructured.io
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/
```

**Alternative: Mit rsync (zeigt Fortschritt)**
```bash
rsync -avz --progress deployment/ user@vm-ip:/opt/unstructured-deployment/
```

### Schritt 2: Auf VM einloggen

```bash
ssh user@vm-ip
cd /opt/unstructured-deployment
```

### Schritt 3: Docker prüfen (auf VM)

```bash
# Docker installiert?
docker --version
docker compose version

# Falls nicht installiert:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Schritt 4: Deployment starten (auf VM)

```bash
chmod +x deploy.sh
./deploy.sh
```

### Schritt 5: Firewall konfigurieren (auf VM)

```bash
# Port 8501 öffnen
sudo ufw allow 8501/tcp

# Status prüfen
sudo ufw status
```

### Schritt 6: Von außen zugreifen

```
http://<VM-IP>:8501
```

Beispiel: `http://192.168.1.100:8501`

---

## 🔍 Detaillierte Erklärung: Was passiert beim Build?

### Phase 1: Base Image laden

```dockerfile
FROM downloads.unstructured.io/unstructured-io/unstructured:latest AS unstructured-base
```

**Was wird geladen:**
- Python 3.12 Runtime
- YOLOvX Object Detection Model (~500 MB)
- Table Transformer Model (~300 MB)
- Tesseract OCR (Deutsch + Englisch)
- PaddleOCR
- NLTK Daten
- Poppler-utils, libmagic
- Alle Python-Dependencies von unstructured.io

**Größe:** ~2-3 GB

### Phase 2: Anwendungs-Layer

```dockerfile
FROM unstructured-base AS app
USER root
RUN pip install streamlit plotly pandas
COPY app_open_source_recovered.py .
COPY pptx_helpers.py .
```

**Was wird hinzugefügt:**
- Streamlit Framework
- Plotly (Visualisierungen)
- Pandas (Datenverarbeitung)
- Unsere Anwendungsdateien

**Zusätzliche Größe:** ~500 MB

### Phase 3: Konfiguration

```dockerfile
EXPOSE 8501
ENV STREAMLIT_SERVER_PORT=8501
ENTRYPOINT ["streamlit", "run", "app_open_source_recovered.py"]
```

**Was wird konfiguriert:**
- Port-Freigabe
- Umgebungsvariablen
- Startbefehl

---

## 📊 Docker Compose Details

### docker-compose.yml Struktur

```yaml
version: '3.8'

services:
  unstructured-app:
    build: .
    container_name: unstructured-prototype
    ports:
      - "8501:8501"
    volumes:
      - ./test_files:/app/prototype/test_files
      - ./logs:/app/logs
    environment:
      - TESSDATA_PREFIX=/usr/local/share/tessdata
      - NLTK_DATA=/home/notebook-user/nltk_data
      - HF_HUB_OFFLINE=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Erklärung:**

| Abschnitt | Zweck |
|-----------|-------|
| **ports** | Host-Port 8501 → Container-Port 8501 |
| **volumes** | Persistente Daten: Uploads und Logs |
| **environment** | Unstructured.io Settings |
| **restart** | Auto-Restart bei Crash |
| **healthcheck** | Prüft ob Streamlit läuft |

---

## 🔧 Erweiterte Konfiguration

### Memory Limits setzen

```yaml
# In docker-compose.yml unter service hinzufügen:
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
    reservations:
      cpus: '2.0'
      memory: 4G
```

**Anwenden:**
```bash
docker compose down
docker compose up -d
```

### Port ändern

```yaml
# In docker-compose.yml:
ports:
  - "8080:8501"  # Ändere 8080 zu gewünschtem Port
```

**Firewall anpassen:**
```bash
sudo ufw allow 8080/tcp
```

### Zusätzliche Umgebungsvariablen

```yaml
environment:
  - STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200  # MB
  - STREAMLIT_SERVER_ENABLE_CORS=false
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

---

## 🐛 Troubleshooting Guide

### Problem 1: Container startet nicht

**Symptom:**
```bash
docker compose ps
# Status: Exited (1)
```

**Diagnose:**
```bash
docker compose logs
```

**Häufige Ursachen:**

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `port already in use` | Port 8501 belegt | Port ändern oder Prozess beenden |
| `out of memory` | Zu wenig RAM | Memory Limits erhöhen |
| `permission denied` | User-Rechte fehlen | `sudo usermod -aG docker $USER` |
| `image not found` | Build fehlgeschlagen | `docker compose build --no-cache` |

### Problem 2: Streamlit lädt nicht

**Diagnose:**
```bash
# Health Check
curl http://localhost:8501/_stcore/health

# Sollte zurückgeben:
# { "status": "ok" }

# Falls nicht:
docker compose logs -f | grep -i error
```

**Lösungen:**

1. **Warten:** Erster Start braucht 1-2 Minuten
2. **Neu starten:** `docker compose restart`
3. **Neu bauen:** `docker compose down && docker compose up -d --build`

### Problem 3: Dateien verschwinden

**Ursache:** Volumes nicht korrekt gemountet

**Prüfen:**
```bash
docker inspect unstructured-prototype | grep -A 10 Mounts
```

**Sollte zeigen:**
```json
"Mounts": [
    {
        "Source": "/home/user/deployment/test_files",
        "Destination": "/app/prototype/test_files",
        "Mode": "rw"
    }
]
```

**Lösung:**
```bash
# Volumes neu erstellen
docker compose down -v
docker compose up -d
```

### Problem 4: Performance-Probleme

**Symptom:** Dokument-Verarbeitung sehr langsam

**Diagnose:**
```bash
# CPU und RAM Nutzung prüfen
docker stats unstructured-prototype
```

**Optimierungen:**

1. **Resource Limits erhöhen:**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 16G
   ```

2. **Strategy anpassen:**
   - `hi_res` → `auto` (schneller, weniger genau)
   - OCR deaktivieren falls nicht benötigt

3. **Chunking aktivieren:**
   ```python
   partition(..., chunking_strategy="basic", max_characters=500)
   ```

### Problem 5: "Image pull failed"

**Symptom:**
```
Error: Failed to pull image downloads.unstructured.io/unstructured-io/unstructured:latest
```

**Ursachen:**
- Netzwerk-Probleme
- Docker Registry nicht erreichbar
- Zu wenig Speicherplatz

**Lösungen:**

1. **Retry mit mehr Timeout:**
   ```bash
   DOCKER_CLIENT_TIMEOUT=300 docker compose build
   ```

2. **Alternativer Mirror (falls verfügbar):**
   ```dockerfile
   FROM quay.io/unstructured-io/unstructured:latest
   ```

3. **Manuell pullen:**
   ```bash
   docker pull downloads.unstructured.io/unstructured-io/unstructured:latest
   docker compose build --no-cache
   ```

---

## 📈 Monitoring & Maintenance

### Logs verwalten

```bash
# Logs anzeigen
docker compose logs

# Live-Logs (letzte 100 Zeilen)
docker compose logs -f --tail=100

# Logs in Datei speichern
docker compose logs > deployment_logs_$(date +%Y%m%d).txt

# Logs rotieren (automatisch)
# In docker-compose.yml:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Container-Updates

```bash
# Neue Version holen
docker compose pull

# Neu bauen
docker compose build --no-cache

# Container neu starten
docker compose up -d
```

### Backup erstellen

```bash
# Volumes sichern
tar czf backup_$(date +%Y%m%d).tar.gz test_files/ logs/

# Container-Konfiguration sichern
tar czf config_$(date +%Y%m%d).tar.gz \
    Dockerfile docker-compose.yml requirements.txt \
    app_open_source_recovered.py pptx_helpers.py
```

### Speicherplatz freigeben

```bash
# Ungenutzte Images löschen
docker image prune -a

# Ungenutzte Volumes löschen
docker volume prune

# Alles aufräumen (VORSICHT!)
docker system prune -a --volumes
```

---

## 🚀 Production-Ready Checklist

### Vor dem Go-Live:

- [ ] **SSL/TLS konfiguriert** (Let's Encrypt + nginx)
- [ ] **Reverse Proxy aktiv** (nginx/Traefik)
- [ ] **Firewall-Regeln gesetzt** (nur 80/443 extern)
- [ ] **Resource Limits definiert** (Memory, CPU)
- [ ] **Log-Rotation aktiv** (max-size, max-file)
- [ ] **Backup-Strategie** (täglich, wöchentlich)
- [ ] **Monitoring eingerichtet** (Prometheus/Grafana)
- [ ] **Health Checks funktionieren**
- [ ] **Auto-Restart aktiv** (restart: unless-stopped)
- [ ] **Secrets aus Umgebung** (keine Passwörter im Code)
- [ ] **Update-Strategie** (Blue-Green, Canary)
- [ ] **Dokumentation aktuell**

---

## 📞 Hilfe & Support

### Offizielle Ressourcen

- **Unstructured.io Docs:** https://docs.unstructured.io
- **GitHub Issues:** https://github.com/Unstructured-IO/unstructured/issues
- **Community Slack:** https://unstructured-io.slack.com

### Debugging-Befehle

```bash
# Container-Zustand
docker inspect unstructured-prototype

# Ins Container einloggen
docker exec -it unstructured-prototype bash

# Python-Umgebung prüfen
docker exec -it unstructured-prototype python3 -c "import unstructured; print(unstructured.__version__)"

# Netzwerk-Test
docker exec -it unstructured-prototype curl -I http://localhost:8501
```

---

## 🎉 Erfolgreiches Deployment!

Wenn alles funktioniert, solltest du sehen:

✅ Container läuft: `docker compose ps`  
✅ Health Check: `curl http://localhost:8501/_stcore/health`  
✅ Web-UI: Browser zeigt Streamlit-App  
✅ Dokument-Upload funktioniert  
✅ Alle Formate werden verarbeitet  

**Herzlichen Glückwunsch! 🚀**

---

**Version:** 1.0.0  
**Datum:** 2025-10-29  
**Autor:** Unstructured.io Deployment Team

