import requests
from utils.database import client
from config import Config
import logging
import sys
import locale

# Setze Standard-Encoding auf UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_database_connection():
    """Testet, ob die Datenbank erreichbar ist."""
    try:
        logging.info("Überprüfe die Verbindung zur Datenbank...")
        client.admin.command("ping")
        logging.info("✅ Verbindung zur Datenbank erfolgreich.")
        return True
    except Exception as e:
        logging.error(f"❌ Verbindung zur Datenbank fehlgeschlagen: {e}")
        return False


def test_api_endpoints():
    """Testet die Erreichbarkeit der API-Endpunkte."""
    base_url = "http://127.0.0.1:5000"

    # Beispiel-Daten
    test_register_data = {
        "username": "testuser",
        "password": "Test@1234",
        "email": "testuser@example.com"
    }
    test_login_data = {
        "username": "testuser",
        "password": "Test@1234"
    }

    endpoints = [
        {"url": "/api/questions", "method": "GET"},
        {"url": "/api/lexicon", "method": "GET"},
        {"url": "/api/register", "method": "POST", "data": test_register_data},
        {"url": "/api/login", "method": "POST", "data": test_login_data},
    ]

    success = True
    for endpoint in endpoints:
        try:
            logging.info(f"Teste API-Endpunkt: {base_url}{endpoint['url']}")
            if endpoint["method"] == "GET":
                response = requests.get(f"{base_url}{endpoint['url']}")
            elif endpoint["method"] == "POST":
                response = requests.post(f"{base_url}{endpoint['url']}", json=endpoint.get("data", {}))

            if response.status_code in [200, 201]:
                logging.info(f"✅ API {endpoint['url']} ist erreichbar. Status: {response.status_code}")
            else:
                logging.error(f"❌ API {endpoint['url']} nicht erreichbar. Status: {response.status_code}")
                success = False
        except Exception as e:
            logging.error(f"❌ Fehler beim Testen von {endpoint['url']}: {e}")
            success = False

    return success




if __name__ == "__main__":
    logging.info("Starte Start-Up Tests...")

    # Test: Datenbankverbindung
    db_ok = test_database_connection()

    # Test: API-Endpunkte
    logging.info("Warte, bis der Server startet (5 Sekunden)...")
    import time

    time.sleep(5)
    api_ok = test_api_endpoints()

    # Gesamtergebnis
    if db_ok and api_ok:
        logging.info("✅ Alle Tests erfolgreich. Die Anwendung ist bereit.")
    else:
        logging.error("❌ Ein oder mehrere Tests sind fehlgeschlagen.")
