# 🚀 Quick Start: VM-Deployment via GitHub

**Schnellste Methode, um den Code auf deine VM zu bekommen!**

---

## ✅ Voraussetzungen

- [x] Du nutzt bereits GitHub
- [x] Du hast SSH-Zugriff zur VM
- [x] Docker ist auf der VM installiert

---

## 🎯 Methode 1: Automatisches Script (Empfohlen)

### 1. Script ausführbar machen

```bash
cd /home/amu/project/unstructured.io/deployment
chmod +x deploy-to-vm-github.sh
```

### 2. Script starten

```bash
./deploy-to-vm-github.sh
```

**Das Script fragt nach:**
- GitHub Username
- Repository Name
- Branch (default: main)
- VM IP-Adresse
- VM Benutzer

**Dann macht es automatisch:**
1. ✅ Pusht Code zu GitHub
2. ✅ Testet SSH-Verbindung
3. ✅ Klont/Updated Repository auf VM
4. ✅ Startet Deployment

**Dauer:** ~2-3 Minuten

---

## ⚡ Methode 2: Manuelle Befehle

### Schritt 1: Code zu GitHub pushen

```bash
cd /home/amu/project/unstructured.io

# Status prüfen
git status

# Deployment-Ordner hinzufügen
git add deployment/

# Commit
git commit -m "Add Docker deployment with unstructured.io"

# Push
git push origin main
```

### Schritt 2: Auf VM deployen

```bash
# Auf VM einloggen
ssh user@vm-ip

# Repository klonen (erste Mal)
cd /opt
git clone https://github.com/<username>/<repo>.git

# Oder: Update holen (wenn schon geklont)
cd /opt/<repo>
git pull origin main

# Ins Deployment-Verzeichnis
cd deployment

# Deploy-Script ausführbar machen
chmod +x deploy.sh

# Deployment starten
./deploy.sh
```

### Schritt 3: Anwendung öffnen

```
http://<vm-ip>:8501
```

---

## 🔄 Updates einspielen (später)

### Wenn du Änderungen am Code machst:

```bash
# === VON DEINEM WSL AUS ===

# 1. Änderungen pushen
cd /home/amu/project/unstructured.io
git add deployment/
git commit -m "Update configuration"
git push origin main

# 2. VM updaten (remote)
ssh user@vm-ip "cd /opt/<repo> && git pull && cd deployment && docker-compose down && docker-compose up -d --build"
```

**Oder auf VM direkt:**
```bash
ssh user@vm-ip
cd /opt/<repo>
git pull
cd deployment
docker-compose down
docker-compose up -d --build
```

---

## 🔐 GitHub SSH-Keys einrichten (Optional aber empfohlen)

**Für einfacheren Zugriff ohne Passwort:**

### Auf VM:

```bash
# 1. SSH-Key generieren
ssh-keygen -t ed25519 -C "vm@example.com"

# 2. Public Key anzeigen
cat ~/.ssh/id_ed25519.pub
```

### Auf GitHub:

1. Gehe zu: https://github.com/settings/keys
2. Klicke "New SSH key"
3. Füge den Public Key ein
4. Speichern

### Testen:

```bash
ssh -T git@github.com
# Sollte zeigen: "Hi <username>! You've successfully authenticated..."
```

### Repository mit SSH klonen:

```bash
# Statt HTTPS:
git clone https://github.com/<user>/<repo>.git

# Nutze SSH:
git clone git@github.com:<user>/<repo>.git
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" beim Git-Klonen auf VM

```bash
# Lösung: SSH-Keys für GitHub einrichten (siehe oben)
# Oder: Repository ist privat → Zugriffsrechte prüfen
```

### Problem: "Repository not found"

```bash
# Prüfen:
# 1. GitHub URL korrekt?
# 2. Repository öffentlich oder hast du Zugriff?
# 3. Auf GitHub eingeloggt?

# Testen:
git ls-remote https://github.com/<user>/<repo>.git
```

### Problem: SSH zur VM schlägt fehl

```bash
# Testen:
ssh -v user@vm-ip

# Firewall prüfen:
sudo ufw allow 22/tcp

# SSH-Service prüfen:
sudo systemctl status ssh
```

### Problem: Git push funktioniert nicht

```bash
# Branch prüfen:
git branch

# Remote prüfen:
git remote -v

# Force push (VORSICHT - überschreibt Remote):
git push -f origin main
```

---

## 📊 Vorteile dieser Methode

| Vorteil | Beschreibung |
|---------|--------------|
| ✅ **Professionell** | Standard in der Industrie |
| ✅ **Versionskontrolle** | Alle Änderungen nachvollziehbar |
| ✅ **Backup** | Code automatisch gesichert |
| ✅ **Team-Ready** | Kollegen können auch deployen |
| ✅ **Einfache Updates** | Nur `git pull` nötig |
| ✅ **CI/CD Ready** | Kann automatisiert werden |

---

## 🎯 Zusammenfassung

**Einfachster Weg für dich:**

```bash
# === EINMALIG ===

# 1. Von WSL: Code pushen
cd /home/amu/project/unstructured.io
git add deployment/
git commit -m "Add deployment"
git push origin main

# 2. Auf VM: Klonen & deployen
ssh user@vm-ip
cd /opt
git clone https://github.com/<user>/<repo>.git
cd <repo>/deployment
chmod +x deploy.sh
./deploy.sh

# === FÜR UPDATES ===

# Lokal: Pushen
git add . && git commit -m "Update" && git push

# VM: Pullen & neu deployen
ssh user@vm-ip "cd /opt/<repo> && git pull && cd deployment && docker-compose up -d --build"
```

**Fertig! 🎉**

---

## 📞 Hilfe

- **GitHub Docs:** https://docs.github.com
- **Git Basics:** https://git-scm.com/book/en/v2
- **SSH Keys:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-10-29

