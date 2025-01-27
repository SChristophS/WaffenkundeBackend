#!/bin/bash
# Aktiviert die virtuelle Umgebung
echo "Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Starte die App im Hintergrund
echo "Starte die Anwendung..."
python app.py &
APP_PID=$!

# Warten, damit die App vollständig gestartet ist (z. B. 5 Sekunden)
echo "Warte auf den Start der App..."
sleep 5

# Führt die Tests aus
echo "Führe Tests aus..."
python test_startup.py
if [ $? -ne 0 ]; then
    echo "Tests fehlgeschlagen. Beende die App..."
    kill $APP_PID
    exit 1
fi

# Tests erfolgreich, App bleibt laufen
echo "Tests erfolgreich. App läuft weiter mit PID: $APP_PID"
wait $APP_PID
