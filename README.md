# 🚀 Unstructured.io Streamlit Prototype - Docker Deployment

Ein produktionsreifer Streamlit-Prototyp basierend auf dem **offiziellen unstructured.io Docker Image** mit vollständiger Feature-Unterstützung.

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Voraussetzungen](#-voraussetzungen)
- [Schnellstart](#-schnellstart)
- [Was ist dabei?](#-was-ist-dabei)
- [Unstructured.io Features](#-unstructuredio-features)
- [Nutzung](#-nutzung)
- [Troubleshooting](#-troubleshooting)
- [Dokumentation](#-dokumentation)

---

## ✨ Features

### Streamlit Prototype
- 📄 **Multi-Format Support**: PDF, DOCX, PPTX, Excel, HTML, Markdown, E-Mails, Bilder
- 🎨 **Interaktive UI**: Datei-Upload, Live-Preview, Format-Konvertierung
- 📊 **Export-Formate**: Text, Markdown, HTML, JSON, CSV, Bedrock RAG JSON
- 🖼️ **Bild-Extraktion**: Automatische Extraktion und Download von Bildern aus Dokumenten
- 🤖 **AWS Bedrock Ready**: Optimierte JSON-Struktur für RAG mit Bildunterstützung

### Unstructured.io Open Source Features (automatisch inkludiert)
- ✅ **YOLOvX Object Detection**: Automatische Erkennung von Titeln, Tabellen, Bildern, Listen
- ✅ **Tesseract + PaddleOCR**: Mehrsprachige OCR für gescannte Dokumente
- ✅ **Table Transformer**: Intelligente Tabellen-Extraktion als HTML
- ✅ **Hi-Res Strategy**: Beste Qualität für komplexe Layouts
- ✅ **NLP Pipeline**: Automatische Spracherkennung und Text-Segmentierung
- ✅ **Element Metadata**: Bounding Boxes, Page Numbers, Koordinaten

---

## 🔧 Voraussetzungen

- **Docker** (>= 20.10)
- **Docker Compose** (>= 1.29) oder Docker Compose Plugin
- **Mindestens 8 GB RAM** (empfohlen 16 GB)
- **Mindestens 10 GB freier Speicher** (für Docker Image)

### Installation prüfen:

```bash
docker --version
docker-compose --version  # oder: docker compose version
```

---

## ⚡ Schnellstart

### 1. Deployment starten (automatisch)

```bash
cd /home/amu/project/unstructured.io/deployment
chmod +x deploy.sh
./deploy.sh
```

**Das Script macht:**
1. ✅ Prüft Docker-Installation
2. ✅ Erstellt notwendige Verzeichnisse
3. ✅ Lädt offizielles unstructured.io Base-Image (~2-3 GB)
4. ✅ Baut Anwendungs-Image mit Streamlit
5. ✅ Startet Container
6. ✅ Wartet auf Streamlit-Bereitschaft

**Erster Start:** 5-10 Minuten (Image-Download)  
**Nachfolgende Starts:** 30-60 Sekunden

### 2. Anwendung öffnen

```
http://localhost:8501
```

### 3. Manuelles Deployment (alternativ)

```bash
# Container stoppen (falls läuft)
docker-compose down

# Image bauen
docker-compose build

# Container starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

---

## 📦 Was ist dabei?

### Dateien im Deployment-Ordner

```
deployment/
├── Dockerfile                      # Multi-Stage Build mit offiziellem Base-Image
├── docker-compose.yml              # Orchestrierung + Environment
├── deploy.sh                       # Automatisches Deployment-Script
├── requirements.txt                # Nur Streamlit + Zusatz-Pakete
├── app_open_source_recovered.py    # Hauptanwendung
├── pptx_helpers.py                 # PowerPoint-Hilfsfunktionen
├── README.md                       # Diese Datei
├── DEPLOYMENT-GUIDE.md            # Detaillierte Deployment-Anleitung
├── VM-TRANSFER-GUIDE.md           # Anleitung: Code auf VM übertragen
├── test_files/                     # Upload-Verzeichnis (Volume)
└── logs/                           # Log-Verzeichnis (Volume)
```

### Docker Image Details

**Base Image:**
```
downloads.unstructured.io/unstructured-io/unstructured:latest
```

**Enthält automatisch:**
- ✅ Python 3.12
- ✅ Tesseract OCR (Deutsch + Englisch)
- ✅ PaddleOCR
- ✅ YOLOvX Object Detection Model (vortrainiert)
- ✅ Table Transformer Model (vortrainiert)
- ✅ NLTK Data (punkt_tab, averaged_perceptron_tagger_eng)
- ✅ Poppler-utils (PDF-Rendering)
- ✅ libmagic (Dateityp-Erkennung)
- ✅ Alle unstructured.io Core-Dependencies

**Zusätzlich installiert (in unserem Layer):**
- Streamlit 1.28.0
- Plotly 5.17.0
- Pandas 2.1.1

---

## 🧠 Unstructured.io Features

### YOLOvX Object Detection

**Was ist YOLOvX?**
- Hochmodernes Deep Learning Modell für **Dokumenten-Layout-Analyse**
- Speziell trainiert auf wissenschaftliche Papers, Berichte, Verträge, Formulare
- Erkennt automatisch: Titel, Absätze, Tabellen, Bilder, Fußnoten, Header, Footer

**Was macht es in unserem Prototyp?**
```python
# Automatisch aktiviert bei strategy="hi_res"
elements = partition_pdf(
    filename="document.pdf",
    strategy="hi_res"  # ← YOLOvX wird verwendet
)

# Resultat: Strukturierte Elemente mit Bounding Boxes
[
    Title("Quarterly Report"),
    NarrativeText("This document presents..."),
    Table("<table><tr>...</tr></table>"),
    Image(metadata={"coordinates": ...})
]
```

**Vorteile:**
- ✅ Keine manuelle Konfiguration nötig
- ✅ Funktioniert out-of-the-box für 40+ Dateiformate
- ✅ Bessere Ergebnisse als reine Text-Extraktion
- ✅ Behält semantische Dokumentstruktur

### Processing Strategies

| Strategy | Wann nutzen | YOLOvX | OCR | Geschwindigkeit |
|----------|-------------|---------|-----|-----------------|
| **fast** | Einfache Text-PDFs | ❌ | ❌ | ⚡⚡⚡ |
| **hi_res** | Komplexe Layouts, Tabellen | ✅ | ✅ | ⚡⚡ |
| **ocr_only** | Gescannte Dokumente | ❌ | ✅ | ⚡ |
| **auto** | Automatische Erkennung | 🔀 | 🔀 | ⚡⚡ |

**Im Prototyp eingestellt:**
```python
# app_open_source_recovered.py nutzt standardmäßig:
strategy = "hi_res"  # Beste Qualität
```

### Tesseract + PaddleOCR

**Beide OCR-Engines sind vorinstalliert!**

```python
# Tesseract (Standard für europäische Sprachen)
partition_pdf("scan.pdf", ocr_languages="deu+eng")

# PaddleOCR (besser für asiatische Sprachen)
partition_pdf("scan.pdf", ocr_languages="chi_sim")
```

**Unterstützte Sprachen:**
- ✅ Deutsch (deu)
- ✅ Englisch (eng)
- ✅ Weitere installierbar: `apt-get install tesseract-ocr-fra` (Französisch)

### NLP Features

**Automatisch aktiviert:**
- ✅ Spracherkennung pro Element
- ✅ Text-Segmentierung (Sätze, Absätze)
- ✅ Metadaten-Extraktion (Datum, E-Mail-Adressen)

```python
element.metadata.languages  # ['deu', 'eng']
element.metadata.emphasized_text_tags  # ['b', 'i']
```

---

## 🎯 Nutzung

### Container-Management

```bash
# Container starten
docker-compose up -d

# Logs live anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down

# Container neu starten
docker-compose restart

# Container-Status
docker-compose ps

# In Container einloggen (für Debugging)
docker exec -it unstructured-prototype bash
```

### Volumes

**Persistente Daten:**
```bash
./test_files/   # Hochgeladene Dateien
./logs/         # Anwendungs-Logs
```

**Zugriff vom Host:**
```bash
ls -lah deployment/test_files/
cat deployment/logs/streamlit.log
```

### Port-Änderung

In `docker-compose.yml`:
```yaml
ports:
  - "8080:8501"  # Ändere 8080 zu gewünschtem Port
```

---

## 🐛 Troubleshooting

### Problem: Container startet nicht

```bash
# Logs prüfen
docker-compose logs

# Spezifischer Container
docker logs unstructured-prototype
```

**Häufige Ursachen:**
- Port 8501 bereits belegt → Ändere Port in `docker-compose.yml`
- Zu wenig RAM → Erhöhe Docker-Memory-Limit
- Alter Container läuft noch → `docker-compose down && docker-compose up -d`

### Problem: "Out of memory"

```yaml
# In docker-compose.yml unter service:
deploy:
  resources:
    limits:
      memory: 8G
    reservations:
      memory: 4G
```

### Problem: Streamlit lädt nicht

```bash
# Health Check
curl http://localhost:8501/_stcore/health

# Firewall prüfen
sudo ufw allow 8501/tcp

# Browser-Cache leeren
Ctrl+Shift+R (Hard Reload)
```

### Problem: Dateien verschwinden nach Neustart

**Lösung:** Volumes korrekt gemountet?
```bash
# Prüfen
docker inspect unstructured-prototype | grep Mounts -A 10

# Sollte zeigen:
# "Source": "/home/user/deployment/test_files"
# "Destination": "/app/prototype/test_files"
```

### Problem: "Permission denied" beim deploy.sh

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📚 Dokumentation

### Offizielle Unstructured.io Dokumentation

1. **Supported File Types**: https://docs.unstructured.io/open-source/ingestion/supported-file-types
2. **Chunking**: https://docs.unstructured.io/open-source/core-functionality/chunking
3. **Document Elements**: https://docs.unstructured.io/open-source/concepts/document-elements
4. **PDF Transformation**: https://unstructured.io/blog/mastering-pdf-transformation-strategies-with-unstructured-part-2
5. **Docker Installation**: https://docs.unstructured.io/open-source/installation/docker-installation

### GitHub Repository

- **Official Repo**: https://github.com/Unstructured-IO/unstructured
- **Docker Images**: https://downloads.unstructured.io/unstructured-io/unstructured

### Weitere Guides in diesem Ordner

- `DEPLOYMENT-GUIDE.md` - Detaillierte Deployment-Schritte
- `VM-TRANSFER-GUIDE.md` - Code auf VM übertragen (SCP, rsync, Git)

---

## 🔐 Sicherheit

### Produktions-Deployment

**Wichtig für Production:**

1. **Secrets Management**
   - Keine Passwörter in `docker-compose.yml`
   - Nutze Docker Secrets oder .env-Dateien

2. **Reverse Proxy**
   ```yaml
   # Beispiel: nginx proxy
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
   ```

3. **SSL/TLS**
   - Let's Encrypt für kostenlose Zertifikate
   - `certbot` für automatische Erneuerung

4. **Firewall**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw deny 8501/tcp  # Nur intern erreichbar
   ```

---

## 📊 Performance-Tuning

### Docker Resource Limits

```yaml
# docker-compose.yml
services:
  unstructured-app:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### Streamlit Caching

```python
# Im Code bereits aktiviert:
@st.cache_data
def process_document(file):
    # Caching reduziert Rechenzeit bei wiederholten Uploads
    pass
```

---

## 🚀 VM-Deployment

### Code auf VM übertragen

**Siehe detaillierte Anleitung:** `VM-TRANSFER-GUIDE.md`

**Schnellste Methode:**
```bash
# Von deinem WSL aus
cd /home/amu/project/unstructured.io
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/

# Auf VM: Deployment starten
ssh user@vm-ip "cd /opt/unstructured-deployment && ./deploy.sh"
```

**Fertig!** Die Anwendung läuft auf: `http://vm-ip:8501`

---

## 🎉 Fertig!

Dein Unstructured.io Prototyp läuft jetzt professionell in Docker mit:
- ✅ Offiziellem Base-Image
- ✅ YOLOvX Object Detection
- ✅ Tesseract + PaddleOCR
- ✅ Alle 40+ Dateiformate
- ✅ Production-ready Setup

**Viel Erfolg beim Testen! 🚀**

---

## 📞 Support & Weitere Hilfe

Bei Fragen oder Problemen:

1. **Logs prüfen**: `docker-compose logs -f`
2. **Container-Status**: `docker-compose ps`
3. **Health Check**: `curl http://localhost:8501/_stcore/health`
4. **Offizielle Docs**: https://docs.unstructured.io

### Häufige Fragen

**Q: Brauche ich einen API-Key?**  
A: Nein! Die Open Source Version funktioniert komplett lokal ohne API-Keys.

**Q: Kostet das etwas?**  
A: Nein! Alles ist Open Source und kostenlos nutzbar.

**Q: Kann ich das in Production nutzen?**  
A: Ja! Mit den Sicherheits-Hinweisen oben ist es production-ready.

**Q: Wie groß ist das Docker Image?**  
A: Base-Image: ~2-3 GB, Finales Image: ~3-4 GB

**Q: Wie schnell ist die Verarbeitung?**  
A: PDF (10 Seiten, hi_res): ~10-30 Sekunden, je nach Komplexität

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-10-29  
**Maintainer:** Unstructured.io Community

