# Backend API Dokumentation

## Beschreibung
Das Backend dient als API-Server für die ExamApp. Es bietet Endpunkte für Benutzerauthentifizierung, das Abrufen von Fragen und Lexikoneinträgen.

---

## **Installation und Start**

### **Schritt 1: Projekt klonen**
1. Öffne ein Terminal auf deinem Raspberry Pi.
2. Klone das Repository mit:
   ```bash
   git clone https://github.com/SChristophS/WAA_WaffenkundeBackend
   cd <REPOSITORY_NAME>
   ```

---

### **Schritt 2: Virtuelle Umgebung erstellen und aktivieren**
1. **Virtuelle Umgebung erstellen:**
   ```bash
   python3 -m venv venv
   ```
2. **Virtuelle Umgebung aktivieren:**
   ```bash
   source venv/bin/activate
   ```

---

### **Schritt 3: Abhängigkeiten installieren**
1. Stelle sicher, dass du in der virtuellen Umgebung bist:
   ```bash
   source venv/bin/activate
   ```
2. Installiere die Abhängigkeiten:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

### **Schritt 4: Server starten**
1. **Starte den Server:**
   ```bash
   python app.py
   ```
2. Der Server ist standardmäßig unter folgender URL erreichbar:
   ```
   http://127.0.0.1:5000
   ```

---

### **Schritt 5: Alternative Skripte**
Zur Vereinfachung sind Skripte für die Installation und den Start enthalten.

#### **Installation**
```bash
./install_linux.sh
```

#### **Start**
```bash
./start_linux.sh
```

Stelle sicher, dass die Skripte ausführbar sind:
```bash
chmod +x install_linux.sh start_linux.sh
```

---

## **API-Endpunkte**

### **1. Registrierung**
- **POST** `/api/register`

#### **Beispielanfrage**
```json
{
  "username": "testuser",
  "password": "Test1234!",
  "email": "test@example.com"
}
```

#### **Beispielantwort**
**Erfolg (201):**
```json
{
  "message": "User registered successfully"
}
```
**Fehler (400):**
```json
{
  "message": "Username already exists"
}
```

---

### **2. Login**
- **POST** `/api/login`

#### **Beispielanfrage**
```json
{
  "username": "testuser",
  "password": "Test1234!"
}
```

#### **Beispielantwort**
**Erfolg (200):**
```json
{
  "access_token": "<JWT_TOKEN>"
}
```
**Fehler (401):**
```json
{
  "message": "Invalid username or password"
}
```

---

### **3. Fragen abrufen**
- **GET** `/api/questions`

#### **Beispielanfrage**
Keine Nutzlast erforderlich.

#### **Beispielantwort**
**Erfolg (200):**
```json
{
  "questions": [
    {
      "id": "1",
      "question": "Was ist die Hauptstadt von Frankreich?",
      "answerOptions": ["Berlin", "Paris", "Madrid"],
      "correctIndex": 1,
      "references": ["Geographie"]
    }
  ]
}
```

---

### **4. Lexikon abrufen**
- **GET** `/api/lexicon`

#### **Beispielanfrage**
Keine Nutzlast erforderlich.

#### **Beispielantwort**
**Erfolg (200):**
```json
{
  "lexicon": [
    {
      "term": "Geographie",
      "definition": "Die Wissenschaft, die sich mit der Erde und ihren Eigenschaften beschäftigt."
    }
  ]
}
```

---

## **Test-Szenarien**

### **1. Tests implementieren**
Alle Tests werden in der Datei `test_startup.py` ausgeführt. Die Ergebnisse werden in eine separate Log-Datei geschrieben.

#### **Datenbankverbindung testen**
```python
def test_database_connection():
    try:
        logging.info("Überprüfe die Verbindung zur Datenbank...")
        client.admin.command("ping")
        logging.info("✅ Verbindung zur Datenbank erfolgreich.")
        return True
    except Exception as e:
        logging.error(f"❌ Verbindung zur Datenbank fehlgeschlagen: {e}")
        return False
```

#### **API-Endpunkte testen**
```python
def test_api_endpoints():
    endpoints = [
        {"url": "/api/questions", "method": "GET"},
        {"url": "/api/lexicon", "method": "GET"},
        {"url": "/api/register", "method": "POST", "data": {"username": "test", "password": "Test1234!", "email": "test@example.com"}},
        {"url": "/api/login", "method": "POST", "data": {"username": "test", "password": "Test1234!"}}
    ]
    for endpoint in endpoints:
        ...  # Teste jeden Endpunkt und logge das Ergebnis
```

#### **Log-Datei**
Passe die `logging`-Konfiguration so an, dass Ergebnisse in eine Datei geschrieben werden:
```python
logging.basicConfig(
    filename='test_results.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
```

#### **Test ausführen**
```bash
python test_startup.py
```

---

## **Git-Befehle für das Raspberry Pi-Setup**
1. Repository klonen:
   ```bash
   git clone <REPOSITORY_URL>
   cd <REPOSITORY_NAME>
   ```

2. Änderungen vom Remote-Repository abrufen:
   ```bash
   git pull origin main
   ```

3. Falls du Änderungen machen möchtest:
   ```bash
   git add .
   git commit -m "Beschreibung der Änderung"
   git push origin main
   ```

---

## **Zukünftige Erweiterungen**
- Hinzufügen von mehr API-Endpunkten.
- Schutz der Endpunkte durch JWT.
- Verbesserung der Tests mit Unit- und Integration-Tests.
