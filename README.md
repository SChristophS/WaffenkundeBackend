## WaffenkundeApp Backend – Deployment & Docker

Dieses Projekt ist ein Flask‑/Socket.IO‑Backend für die WaffenkundeApp mit MongoDB als Datenbank.

### 1. Wichtige Umgebungsvariablen

Die Konfiguration erfolgt primär über Umgebungsvariablen (z.B. via `.env` und `docker-compose.yml`).

- **MONGO_URI**  
  Verbindungs-URI zur MongoDB inkl. Datenbankname.  
  - Docker (Standard): `mongodb://mongo:27017/WaffenkundeApp`  
  - Native Installation: z.B. `mongodb://localhost:27017/WaffenkundeApp`

- **JWT_SECRET_KEY**  
  Langer, zufälliger Secret‑Key für JWT-Signatur. **Muss in Produktion gesetzt werden!**  
  Beispiel:  
  `JWT_SECRET_KEY=bitte-hier-einen-langen-zufaelligen-secret-key-eintragen`

- **SECRET_KEY**  
  Flask-Session-Secret für sichere Cookies und CSRF‑Schutz. Ebenfalls lang & zufällig.  
  Beispiel:  
  `SECRET_KEY=bitte-hier-einen-langen-flask-session-secret-key-eintragen`

- **FEEDBACK_ADMINS**  
  Komma-separierte Liste von Usernamen, die Zugriff auf die Feedback-Admin-API haben.  
  Beispiel:  
  `FEEDBACK_ADMINS=christoph,max`

- **CORS_ORIGINS**  
  Erlaubte Origins für CORS (Frontend-URLs).  
  Beispiele:  
  - Entwicklung: `CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080`  
  - Produktion: `CORS_ORIGINS=https://deine-frontend-domain.de`

- **LOG_LEVEL**  
  Logging-Level: `DEBUG`, `INFO`, `WARNING`, `ERROR`.  
  Empfehlung:  
  - DEV: `DEBUG`  
  - PROD: `INFO` oder `WARNING`

- **LOG_MAX_BYTES**  
  Maximale Dateigröße pro Logfile in Bytes (Rotation). Default im Code: `5_000_000` (~5 MB).

- **LOG_BACKUP_COUNT**  
  Anzahl der Log-Rotationsdateien, die aufbewahrt werden. Default im Code: `3`.

- **PORT**  
  Port, auf dem das Backend im Container/Prozess lauscht. Standard: `2001`.


### 2. Betrieb mit Docker & docker-compose

#### 2.1. Vorbereitung

1. Im Projektverzeichnis eine `.env` anlegen (nicht committen!) und mit obigen Variablen füllen, z.B.:

   ```bash
   MONGO_URI=mongodb://mongo:27017/WaffenkundeApp
   JWT_SECRET_KEY=ein-langer-geheimer-jwt-key
   SECRET_KEY=ein-langer-flask-session-key
   FEEDBACK_ADMINS=christoph,max
   CORS_ORIGINS=https://deine-frontend-domain.de
   LOG_LEVEL=INFO
   LOG_MAX_BYTES=5000000
   LOG_BACKUP_COUNT=5
   PORT=2001
   ```

2. Stelle sicher, dass Docker und docker-compose auf dem Server installiert sind.

#### 2.2. Start mit docker-compose

Im Projektverzeichnis:

```bash
docker-compose build
docker-compose up -d
```

Damit werden zwei Services gestartet:

- `mongo` (MongoDB, Port 27017 – optional nach außen gemappt)
- `backend` (Gunicorn + eventlet, Port 2001 → nach außen auf 2001 gemappt)

#### 2.3. Healthcheck

Nach dem Start kannst du prüfen, ob das Backend erreichbar ist:

```bash
curl http://localhost:2001/health
```

Antwort sollte z.B. sein:

```json
{"ok": true, "time": "..."}
```


### 3. Manuelles (nicht-Docker) Setup (optional)

Falls du lokal ohne Docker testen möchtest:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

export MONGO_URI="mongodb://localhost:27017/WaffenkundeApp"
export JWT_SECRET_KEY="ein-langer-geheimer-key"
export SECRET_KEY="ein-langer-flask-session-key"

python run.py
```

Dann ist das Backend unter `http://localhost:2001` erreichbar.


### 4. Hinweise für das Flutter-Frontend

- In der Flutter-App sollte die API-Basis-URL auf die Adresse des Backends zeigen, z.B.:
  - Entwicklung: `http://10.0.2.2:2001` (Android-Emulator) oder `http://localhost:2001` (Web/Desktop).
  - Produktion (hinter Reverse-Proxy): `https://api.deine-frontend-domain.de`.
- Der `Authorization`-Header muss bei geschützten Endpoints gesetzt werden:
  - `Authorization: Bearer <access-token>`


