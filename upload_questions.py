import os
import json
import logging
from pymongo import MongoClient
from datetime import datetime
from config import Config  # Stelle sicher, dass Config korrekt importiert wird

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# MongoDB-Client erstellen
client = MongoClient(Config.MONGODB_URI)
db = client[Config.DATABASE_NAME]

def upload_questions():
    """
    Lädt die lokale questions.json in die MongoDB hoch, inklusive Versionskontrolle.
    - Bewahrt die ursprüngliche 'version' aus der JSON als 'original_version'.
    - Vergibt zusätzlich eine fortlaufende version (Integer).
    - Setzt 'uploaded_at' auf die aktuelle UTC-Zeit.
    """
    try:
        # 1) JSON-Datei suchen
        data_file = os.path.join(os.getcwd(), "data", "questions.json")
        if not os.path.exists(data_file):
            logging.error(f"Die Datei {data_file} wurde nicht gefunden.")
            return

        # 2) JSON laden
        with open(data_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)

        # 3) Höchste version in der DB finden
        last_version_doc = db.questions.find_one(sort=[("version", -1)])
        new_version = (last_version_doc["version"] + 1) if last_version_doc else 1

        # 4) Prüfen, ob questions_data eine Liste oder ein einzelnes Objekt ist
        if isinstance(questions_data, list):
            # Hier wäre ein Array -> insert_many
            for doc in questions_data:
                # Bewahre original_version (falls vorhanden)
                if "version" in doc:
                    doc["original_version"] = doc["version"]
                # Überschreibe version durch int
                doc["version"] = new_version
                # Aktualisiere 'uploaded_at'
                doc["uploaded_at"] = datetime.utcnow()

            db.questions.insert_many(questions_data)
            logging.info(
                f"Erfolgreich hochgeladen! Neue Version: {new_version} "
                f"(Array mit {len(questions_data)} Elementen)"
            )

        elif isinstance(questions_data, dict):
            # Einzelnes Objekt -> insert_one
            # Bewahre original_version (falls im JSON vorhanden)
            if "version" in questions_data:
                questions_data["original_version"] = questions_data["version"]

            # Fortlaufende Version -> int
            questions_data["version"] = new_version
            questions_data["uploaded_at"] = datetime.utcnow()

            db.questions.insert_one(questions_data)
            logging.info(
                f"Erfolgreich hochgeladen! Neue Version: {new_version} "
                "(einzelnes JSON-Objekt)"
            )

        else:
            logging.error(
                "questions.json hat kein erwartetes Format (weder Array noch Objekt)."
            )

    except Exception as e:
        logging.error(f"Fehler beim Hochladen der Fragen: {e}")

if __name__ == "__main__":
    upload_questions()
