#!/bin/bash
# Prüfen, ob eine virtuelle Umgebung existiert und löschen, falls vorhanden
if [ -d "venv" ]; then
    echo "Virtuelle Umgebung existiert bereits. Lösche alte Umgebung..."
    rm -rf venv
fi

# Neue virtuelle Umgebung erstellen
echo "Erstelle neue virtuelle Umgebung..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo "Fehler beim Erstellen der virtuellen Umgebung."
    exit 1
fi

# Virtuelle Umgebung aktivieren
echo "Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Pip aktualisieren
echo "Aktualisiere pip..."
python3 -m pip install --upgrade pip

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten aus requirements.txt..."
pip install -r requirements.txt

# Bestätigung
echo "Virtuelle Umgebung ist bereit und alle Abhängigkeiten wurden installiert."
