@echo off
:: Virtuelle Umgebung erstellen
if exist "venv" (
    echo Virtuelle Umgebung existiert bereits. Lösche alte Umgebung...
    rd /s /q venv
)

echo Erstelle neue virtuelle Umgebung...
python -m venv venv

if not exist "venv" (
    echo Fehler beim Erstellen der virtuellen Umgebung.
    pause
    exit /b
)

:: Virtuelle Umgebung aktivieren
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate

:: Pip aktualisieren
echo Aktualisiere pip...
python -m pip install --upgrade pip

:: Abhängigkeiten installieren
echo Installiere Abhängigkeiten aus requirements.txt...
pip install -r requirements.txt

:: Bestätigung
echo Virtuelle Umgebung ist bereit und alle Abhängigkeiten wurden installiert.
pause
