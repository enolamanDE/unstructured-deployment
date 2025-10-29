# 📦 Code auf VM übertragen - Beste Methoden

## 🏆 Empfohlene Methode #1: GitHub (Beste Wahl für dich!)

**Du nutzt bereits GitHub?** Perfekt! Das ist die professionellste und einfachste Methode.

### Vorteile von GitHub:
- ✅ **Versionskontrolle** - Alle Änderungen nachvollziehbar
- ✅ **Team-Arbeit** - Andere können auch deployen
- ✅ **Einfache Updates** - Nur `git pull` auf VM
- ✅ **Backup** - Code ist automatisch gesichert
- ✅ **Professionell** - Standard in der Industrie

### Schritt-für-Schritt Anleitung:

#### 1. Code ins GitHub-Repository pushen (von deinem WSL)

```bash
cd /home/amu/project/unstructured.io

# Git-Status prüfen
git status

# Deployment-Ordner zum Repository hinzufügen
git add deployment/

# Commit mit aussagekräftiger Nachricht
git commit -m "Add Docker deployment with official unstructured.io image

- Multi-stage Dockerfile with official base image
- docker-compose.yml with health checks
- Automated deploy.sh script
- Complete documentation (README, DEPLOYMENT-GUIDE, etc.)
- All features: YOLOvX, Tesseract, PaddleOCR, Table Transformer"

# Zu GitHub pushen
git push origin main
# oder falls anderer Branch:
# git push origin <dein-branch-name>
```

#### 2. Auf VM: Repository klonen und deployen

```bash
# Auf VM einloggen
ssh user@vm-ip

# Ins gewünschte Verzeichnis wechseln
cd /opt  # oder ~/

# Repository klonen
git clone https://github.com/<dein-username>/<dein-repo>.git

# ODER falls du bereits SSH-Keys für GitHub hast:
git clone git@github.com:<dein-username>/<dein-repo>.git

# Ins Deployment-Verzeichnis wechseln
cd <dein-repo>/deployment

# Deploy-Script ausführbar machen
chmod +x deploy.sh

# Deployment starten
./deploy.sh
```

#### 3. Fertig! Anwendung läuft auf VM

```
http://<vm-ip>:8501
```

### ⚡ Alles in einem Befehl (von lokal):

```bash
# Vom WSL aus - Push + VM-Deployment in einem Schritt:
cd /home/amu/project/unstructured.io && \
git add deployment/ && \
git commit -m "Add Docker deployment setup" && \
git push origin main && \
ssh user@vm-ip "cd /opt && git clone https://github.com/<user>/<repo>.git && cd <repo>/deployment && chmod +x deploy.sh && ./deploy.sh"
```

### 🔄 Updates auf VM einspielen (später)

**Wenn du Änderungen am Code machst:**

```bash
# 1. Lokal: Änderungen pushen
cd /home/amu/project/unstructured.io
git add deployment/
git commit -m "Update deployment configuration"
git push origin main

# 2. Auf VM: Updates holen
ssh user@vm-ip
cd /opt/<dein-repo>
git pull origin main
cd deployment
docker-compose down
docker-compose up -d --build
```

### 🔐 GitHub mit SSH-Keys (empfohlen)

**Für einfacheren Zugriff ohne Passwort-Eingabe:**

```bash
# Auf VM: SSH-Key für GitHub generieren
ssh user@vm-ip
ssh-keygen -t ed25519 -C "vm-deployment@example.com"
cat ~/.ssh/id_ed25519.pub

# Den angezeigten Public Key kopieren und zu GitHub hinzufügen:
# 1. Gehe zu: https://github.com/settings/keys
# 2. Klicke "New SSH key"
# 3. Füge den Key ein
# 4. Speichern

# Testen:
ssh -T git@github.com
# Sollte zeigen: "Hi <username>! You've successfully authenticated..."
```

---

## 🎯 Alternative Methode #2: SCP (Secure Copy)

**Wenn du schnell mal etwas testen willst ohne Git:**

### Kompletten deployment-Ordner kopieren

```bash
# Von deinem WSL aus:
cd /home/amu/project/unstructured.io

# Kompletten Ordner auf VM kopieren
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/
```

**Beispiel:**
```bash
scp -r deployment/ admin@192.168.1.100:/home/admin/unstructured-deployment/
```

**Was passiert:**
- ✅ Alle 8 Dateien werden kopiert
- ✅ Ordnerstruktur bleibt erhalten
- ✅ Berechtigungen bleiben (auch deploy.sh ist ausführbar)
- ⏱️ Dauert ca. 10-30 Sekunden

---

## 🔐 SSH-Zugriff vorbereiten (falls noch nicht gemacht)

### 1. SSH-Key erstellen (empfohlen - kein Passwort nötig)

```bash
# SSH-Key generieren (falls noch nicht vorhanden)
ssh-keygen -t rsa -b 4096 -C "deine-email@example.com"

# Key auf VM kopieren
ssh-copy-id user@vm-ip

# Testen
ssh user@vm-ip
```

### 2. Mit Passwort (einfacher Start)

```bash
# Einfach mit Passwort
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/
# Passwort eingeben wenn gefragt
```

---

## 📋 Schritt-für-Schritt: Komplette Übertragung

### Methode A: Ein Befehl (schnellste Variante)

```bash
cd /home/amu/project/unstructured.io && \
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/
```

### Methode B: Mit Fortschrittsanzeige

```bash
cd /home/amu/project/unstructured.io && \
rsync -avz --progress deployment/ user@vm-ip:/opt/unstructured-deployment/
```

**Vorteile von rsync:**
- ✅ Zeigt Fortschrittsbalken
- ✅ Nur geänderte Dateien werden übertragen
- ✅ Kann unterbrochene Übertragungen fortsetzen

### Methode C: Als ZIP-Archiv (für langsame Verbindungen)

```bash
# 1. ZIP erstellen
cd /home/amu/project/unstructured.io
zip -r deployment.zip deployment/

# 2. ZIP auf VM kopieren
scp deployment.zip user@vm-ip:/tmp/

# 3. Auf VM: Entpacken
ssh user@vm-ip
cd /opt
unzip /tmp/deployment.zip
mv deployment unstructured-deployment
cd unstructured-deployment
chmod +x deploy.sh
```

---

## 🌐 Weitere Methoden

### Option 3: rsync (für wiederholte Updates)

**Vorteile:**
- ✅ Nur geänderte Dateien werden übertragen
- ✅ Fortschrittsanzeige
- ✅ Kann unterbrochene Übertragungen fortsetzen

```bash
cd /home/amu/project/unstructured.io
rsync -avz --progress deployment/ user@vm-ip:/opt/unstructured-deployment/
```

### Option 4: ZIP-Archiv (für langsame Verbindungen)

1. **FileZilla installieren** (Windows/Linux)
2. **Verbindung konfigurieren:**
   - Host: `sftp://vm-ip`
   - Port: 22
   - Benutzer: `user`
   - Passwort: `dein-passwort`
3. **Links:** Navigiere zu `/home/amu/project/unstructured.io/deployment/`
4. **Rechts:** Navigiere zu `/opt/unstructured-deployment/`
5. **Drag & Drop:** Ziehe den deployment-Ordner nach rechts

### Option 4: WinSCP (Windows-Tool)

Ähnlich wie FileZilla, aber speziell für Windows optimiert.

---

## 🔧 Nach der Übertragung: Deployment starten

```bash
# 1. Auf VM einloggen
ssh user@vm-ip

# 2. Ins Verzeichnis wechseln
cd /opt/unstructured-deployment

# 3. Script ausführbar machen (falls nötig)
chmod +x deploy.sh

# 4. Dateien prüfen
ls -lah

# 5. Deployment starten
./deploy.sh
```

---

## ⚡ Schnellste Methode - Alles in einem Befehl

```bash
# Von deinem WSL aus - komplette Übertragung + Deployment:
cd /home/amu/project/unstructured.io && \
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/ && \
ssh user@vm-ip "cd /opt/unstructured-deployment && chmod +x deploy.sh && ./deploy.sh"
```

**Das macht:**
1. ✅ Kopiert alle Dateien
2. ✅ Macht deploy.sh ausführbar
3. ✅ Startet das Deployment
4. ⏱️ Alles in ca. 2-5 Minuten fertig!

---

## 🔍 Übertragung überprüfen

```bash
# Auf VM: Dateien prüfen
ssh user@vm-ip "ls -lah /opt/unstructured-deployment/"

# Sollte zeigen:
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - deploy.sh (mit x-Flag!)
# - app_open_source_recovered.py
# - pptx_helpers.py
# - README.md
# - DEPLOYMENT-GUIDE.md
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied"

```bash
# Lösung 1: Mit sudo
ssh user@vm-ip "sudo mkdir -p /opt/unstructured-deployment"
ssh user@vm-ip "sudo chown user:user /opt/unstructured-deployment"
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/

# Lösung 2: In Home-Verzeichnis
scp -r deployment/ user@vm-ip:~/unstructured-deployment/
```

### Problem: "Connection refused"

```bash
# Prüfen ob SSH läuft
ssh user@vm-ip

# Firewall-Port öffnen (auf VM)
sudo ufw allow 22/tcp
```

### Problem: "No route to host"

```bash
# VM-IP prüfen
ping vm-ip

# Netzwerk-Verbindung testen
ssh -v user@vm-ip
```

### Problem: Dateien zu groß / Langsame Übertragung

```bash
# Nur essenzielle Dateien kopieren (ohne pptx_helpers.py cache)
cd /home/amu/project/unstructured.io/deployment
tar czf - Dockerfile docker-compose.yml requirements.txt deploy.sh \
  app_open_source_recovered.py pptx_helpers.py README.md | \
  ssh user@vm-ip "cd /opt && tar xzf - && mv . unstructured-deployment"
```

---

## 📊 Methoden-Vergleich

| Methode | Geschwindigkeit | Schwierigkeit | Empfohlen für |
|---------|----------------|---------------|---------------|
| **🏆 GitHub** | ⚡⚡⚡ Schnell | ⭐⭐ Mittel | **Erste Wahl! (Du nutzt es bereits)** |
| **SCP** | ⚡⚡⚡ Schnell | ⭐ Einfach | Schnelle Tests |
| **rsync** | ⚡⚡⚡ Schnell | ⭐⭐ Mittel | Wiederholte Updates |
| **ZIP** | ⚡ Langsam | ⭐ Einfach | Langsame Verbindung |
| **FileZilla** | ⚡⚡ Mittel | ⭐ Sehr einfach | GUI-Liebhaber |

---

## 🎯 Meine Empfehlung für dich:

### ✅ Nutze GitHub (da du es bereits hast!)

**Einmalig einrichten:**
```bash
# 1. Von deinem WSL aus
cd /home/amu/project/unstructured.io
git add deployment/
git commit -m "Add Docker deployment setup"
git push origin main

# 2. Auf VM
ssh user@vm-ip
cd /opt
git clone https://github.com/<user>/<repo>.git
cd <repo>/deployment
chmod +x deploy.sh
./deploy.sh
```

**Für Updates später:**
```bash
# Lokal: Änderungen pushen
git add . && git commit -m "Update" && git push

# VM: Updates holen und neu deployen
ssh user@vm-ip "cd /opt/<repo> && git pull && cd deployment && docker-compose up -d --build"
```

### Warum GitHub die beste Wahl ist:
1. ✅ **Professionell** - Standard in der Industrie
2. ✅ **Versionskontrolle** - Jede Änderung nachvollziehbar
3. ✅ **Backup** - Code ist gesichert
4. ✅ **Team-Ready** - Kollegen können auch deployen
5. ✅ **Einfache Updates** - Nur `git pull` nötig
6. ✅ **Du nutzt es bereits** - Keine neue Tool lernen

---

## 🚀 Schnellstart mit GitHub

```bash
# === VON DEINEM WSL AUS ===
cd /home/amu/project/unstructured.io
scp -r deployment/ user@vm-ip:/opt/unstructured-deployment/

# 2. Deployment starten
ssh user@vm-ip "cd /opt/unstructured-deployment && ./deploy.sh"

# 3. Testen
# Im Browser: http://vm-ip:8501
```

**Fertig in 3 Befehlen!** 🚀

---

## 💡 Pro-Tipps

### Tipp 1: Alias für schnelle Updates

In `~/.bashrc` oder `~/.zshrc`:
```bash
alias vm-deploy='cd /home/amu/project/unstructured.io && \
  rsync -avz deployment/ user@vm-ip:/opt/unstructured-deployment/ && \
  ssh user@vm-ip "cd /opt/unstructured-deployment && docker-compose up -d --build"'
```

Dann einfach:
```bash
vm-deploy
```

### Tipp 2: SSH-Config für einfacheren Zugriff

In `~/.ssh/config`:
```
Host myvm
    HostName 192.168.1.100
    User admin
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

Dann einfach:
```bash
scp -r deployment/ myvm:/opt/unstructured-deployment/
ssh myvm
```

### Tipp 3: Watch-Modus für Entwicklung

```bash
# Automatisch bei Änderungen neu deployen
watch -n 60 'rsync -avz deployment/ user@vm-ip:/opt/unstructured-deployment/'
```

---

## 📞 Schnelle Hilfe

**Brauchst du Hilfe?** Hier die häufigsten Fragen:

**Q: Welche VM-IP habe ich?**
```bash
# Auf der VM
hostname -I
```

**Q: Welcher User?**
```bash
# Auf der VM
whoami
```

**Q: Funktioniert SSH?**
```bash
ssh user@vm-ip
# Wenn das klappt, kannst du auch SCP nutzen!
```

**Q: Kann ich das rückgängig machen?**
```bash
# Auf VM: Alles löschen
ssh user@vm-ip "sudo rm -rf /opt/unstructured-deployment"
```

---

🎉 **Bereit? Dann leg los mit SCP - der schnellsten Methode!**

