# Release Checklist für GitHub-Veröffentlichung

Verwende diese Checkliste vor der Veröffentlichung auf GitHub.

## ⚠️ Sicherheit (KRITISCH)

- [x] `src/config.json` ist in `.gitignore` enthalten
- [x] `src/config.example.json` existiert (ohne echte Zugangsdaten)
- [ ] `src/config.json` wurde NIEMALS in Git committed (prüfen mit: `git log --all --full-history -- "src/config.json"`)
- [ ] Keine Passwörter, Tokens oder S-PINs im Code
- [ ] `tmp/tokenstore` ist in `.gitignore`
- [ ] Logs enthalten keine sensiblen Daten

**Wenn src/config.json jemals committed wurde:**
```bash
# Git-Historie bereinigen (VORSICHT!)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch src/config.json' \
  --prune-empty --tag-name-filter cat -- --all

# Oder: BFG Repo-Cleaner verwenden (empfohlen)
# https://rtyley.github.io/bfg-repo-cleaner/
```

## 📁 Dateien & Struktur

- [x] `.gitignore` ist vollständig (cache, logs, config, venv)
- [x] Keine `__pycache__/` Verzeichnisse im Repository
- [ ] Keine `.pyc` oder `.pyo` Dateien im Repository
- [ ] `logs/` Verzeichnis leer oder nicht im Repo
- [ ] `tmp/` Verzeichnis leer oder nicht im Repo
- [x] `requirements.txt` ist aktuell

**Prüfen:**
```bash
# Prüfe auf Cache-Dateien
find . -name "*.pyc" -o -name "__pycache__" -type d

# Prüfe auf Log-Dateien
find . -name "*.log"

# Prüfe Git-Status
git status --short
```

## 📖 Dokumentation

### README.md
- [x] Quick Start Anleitung ist klar
- [x] Verweis auf `config.example.json` statt direkte Credentials
- [x] Installations-Schritte sind vollständig
- [x] Claude Desktop Integration gut erklärt
- [x] Troubleshooting-Sektion ist hilfreich
- [ ] Repository URL aktualisiert (aktuell: `<repo-url>`)
- [ ] Badges hinzugefügt (optional): Tests, License, Python Version

### Andere Docs
- [x] `CONTRIBUTING.md` ist aktuell und projektspezifisch
- [x] `CODE_OF_CONDUCT.md` vorhanden
- [x] `LICENSE.txt` vorhanden (MIT)
- [x] `tests/README.md` erklärt Test-Struktur
- [x] `examples/README.md` erklärt Beispiele
- [x] `scripts/README.md` erklärt Skripte

## 🧪 Tests

- [ ] Alle Mock-Tests laufen durch: `./scripts/test.sh --skip-slow`
- [ ] Test-Anzahl ist korrekt (aktuell 197 mock tests erwartet)
- [ ] Keine failing/skipped Tests ohne Grund
- [ ] Real-API Tests optional (erfordern VW-Account)

**Prüfen:**
```bash
./scripts/test.sh --skip-slow -v
# Erwartete Ausgabe: 197 passed
```

## 🔧 Konfiguration

- [x] `src/config.example.json` enthält KEINE echten Zugangsdaten
- [x] Setup-Skript erstellt `config.json` aus Example
- [ ] Alle Pfade sind relativ (keine absoluten Pfade zu deinem System)
- [x] `.gitignore` verhindert Commit von `config.json`

## 🚀 Skripte

- [ ] Alle Shell-Skripte sind ausführbar: `chmod +x scripts/*.sh`
- [ ] Skripte funktionieren auf macOS/Linux
- [ ] Relative Pfade (kein hardcoded `/Users/simon/...`)

**Prüfen:**
```bash
# Test setup script
./scripts/setup.sh

# Test other scripts (mit EXAMPLE config)
./scripts/get_claude_config.sh
```

## 📝 GitHub-Spezifisch

- [ ] Repository-Name ist klar: `weconnect_mvp`
- [ ] Beschreibung ist aussagekräftig
- [ ] Topics/Tags gesetzt (python, mcp, volkswagen, ai, claude)
- [ ] `main` Branch ist default
- [ ] GitHub Actions/CI optional eingerichtet
- [ ] Issue Templates erstellt (optional)
- [ ] Pull Request Template erstellt (optional)

## 🎯 Benutzererfahrung

### Kann ein neuer Nutzer:
- [ ] Das Projekt ohne Vorkenntnisse klonen?
- [ ] Dependencies installieren mit einem Befehl?
- [ ] Die Konfiguration verstehen?
- [ ] Den Server starten?
- [ ] Claude Desktop Integration einrichten?
- [ ] Bei Problemen Hilfe finden (Troubleshooting)?

### Test aus Nutzersicht:
```bash
# In einem neuen Terminal/Verzeichnis
cd /tmp
git clone <your-repo-url> test_install
cd test_install
./scripts/setup.sh
# -> Funktioniert das ohne Fehler?
# -> Ist die Anleitung klar?
```

## 🔍 Finale Überprüfung

```bash
# 1. Git-Status sauber?
git status

# 2. Keine ungewollten Dateien?
git ls-files | grep -E "(config\.json|tokenstore|\.pyc|\.log|__pycache__)"
# -> Sollte NICHTS ausgeben!

# 3. .gitignore funktioniert?
git check-ignore src/config.json tmp/tokenstore
# -> Sollte beide Dateien ausgeben

# 4. Tests laufen?
./scripts/test.sh --skip-slow

# 5. README zeigt keine privaten Daten?
grep -r "simon.gerlach\|5sWq,ie=\|7732" README.md CONTRIBUTING.md
# -> Sollte NICHTS finden!
```

## 📋 Veröffentlichungs-Schritte

1. [ ] Alle Punkte oben abgehakt
2. [ ] Finale Commits gemacht
3. [ ] Tag für Version erstellt: `git tag v1.0.0`
4. [ ] Zu GitHub gepusht: `git push origin main --tags`
5. [ ] GitHub Release erstellt mit Changelog
6. [ ] README auf GitHub überprüft (Markdown-Rendering)
7. [ ] Einen Testuser gebeten, Installation zu testen

## ⚠️ Nach Veröffentlichung

- [ ] `config.json` lokal NICHT löschen (du brauchst sie weiter!)
- [ ] Bei Updates: Nie `config.json` commiten
- [ ] Issues/PRs überwachen
- [ ] Bei Sicherheitsproblemen sofort reagieren

---

## 🆘 Notfall: Credentials wurden committed

**Sofort-Maßnahmen:**
1. ✅ Passwort bei VW WeConnect ändern
2. ✅ S-PIN ändern (falls möglich)
3. ✅ Git-Historie bereinigen (siehe oben)
4. ✅ Force-Push zum Repository
5. ⚠️ Allen Clonern mitteilen, neu zu klonen

**Kontakt VW Support:** Bei Verdacht auf Missbrauch sofort VW kontaktieren.
