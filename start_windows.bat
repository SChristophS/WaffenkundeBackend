chcp 65001 >nul
@echo off
REM Aktiviert die virtuelle Umgebung
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate

REM Starte die App im Hintergrund
echo Starte die Anwendung...
start /B python app.py
set APP_PID=%!

REM Warten, damit die App vollständig gestartet ist (z. B. 5 Sekunden)
echo Warte auf den Start der App...
timeout /t 5 > nul

REM Führt die Tests aus
echo Führe Tests aus...
python test_startup.py
if %errorlevel% neq 0 (
    echo Tests fehlgeschlagen. Beende die App...
    taskkill /PID %APP_PID% /F
    pause
    exit /b %errorlevel%
)

REM Tests erfolgreich, App bleibt laufen
echo Tests erfolgreich. App läuft weiter...
pause
