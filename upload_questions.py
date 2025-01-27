import os
import json
import logging
from pymongo import MongoClient
from datetime import datetime
from config import Config  # Stelle sicher, dass Config korrekt importiert wird

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# MongoDB-Client und Verbindung
client = MongoClient(Config.MONGODB_URI)
db = client[Config.DATABASE_NAME]

def upload_questions():
    """Lädt die lokale questions.json in die MongoDB hoch, inklusive Versionskontrolle."""
    try:
        # Lokale JSON-Datei laden
        data_file = os.path.join(os.getcwd(), "data", "questions.json")
        if not os.path.exists(data_file):
            logging.error(f"Die Datei {data_file} wurde nicht gefunden.")
            return

        with open(data_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)

        # Letzte Version in der MongoDB finden
        last_version_doc = db.questions.find_one(sort=[("version", -1)])
        new_version = (last_version_doc["version"] + 1) if last_version_doc else 1

        # Prüfen, ob questions_data eine Liste (mehrere Fragen) oder ein einzelnes Objekt ist.
        if isinstance(questions_data, list):
            # Wenn die JSON-Datei ein Array enthält, laden wir mehrere Dokumente hoch.
            for doc in questions_data:
                doc["version"] = new_version
                doc["uploaded_at"] = datetime.utcnow()
            # Alle auf einmal einfügen
            db.questions.insert_many(questions_data)
            logging.info(f"Erfolgreich hochgeladen! Neue Version: {new_version} "
                         f"(Array mit {len(questions_data)} Fragen)")
        elif isinstance(questions_data, dict):
            # Wenn es ein einzelnes JSON-Objekt ist, laden wir genau ein Dokument hoch.
            questions_data["version"] = new_version
            questions_data["uploaded_at"] = datetime.utcnow()
            db.questions.insert_one(questions_data)
            logging.info(f"Erfolgreich hochgeladen! Neue Version: {new_version} "
                         "(einzelnes JSON-Objekt)")
        else:
            logging.error("questions.json hat kein erwartetes Format (weder Array noch Objekt).")

    except Exception as e:
        logging.error(f"Fehler beim Hochladen der Fragen: {e}")

if __name__ == "__main__":
    upload_questions()
