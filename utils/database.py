# utils/database.py

import logging  # Füge diesen Import hinzu
from pymongo import MongoClient
from config import Config

# MongoDB-Client erstellen
client = MongoClient(Config.MONGODB_URI)
db = client[Config.DATABASE_NAME]

# Verbindung überprüfen
try:
    client.admin.command('ping')
    logging.info("Connected to MongoDB successfully.")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    raise
