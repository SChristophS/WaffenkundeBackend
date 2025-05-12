# models.py

import datetime
from pymongo import ASCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type

# Initialisiere den Password Hasher (Argon2id ist eine gute Wahl)
ph = PasswordHasher(type=Type.ID)

def _users(db: Database) -> Collection:
    """
    Gibt die User-Collection zurück und stellt sicher,
    dass die notwendigen Indizes existieren.
    create_index ist idempotent (erstellt nur, wenn nicht vorhanden oder Optionen gleich sind).
    """
    col = db["users"]
    try:
        # Index für schnellen Login über Namen (unique)
        col.create_index([("name", ASCENDING)], unique=True, name="name_1")
        # Sparse Unique Index für Google ID (erlaubt mehrere null/fehlende Einträge)
        col.create_index("googleSub", unique=True, sparse=True, name="googleSub_1")
        # Sparse Unique Index für Apple ID (erlaubt mehrere null/fehlende Einträge)
        col.create_index("appleSub", unique=True, sparse=True, name="appleSub_1")
    except Exception as e:
        # Optional: Loggen, falls beim Index-Erstellen etwas schiefgeht
        print(f"Error creating indexes for users collection: {e}")
    return col

def create_user(db: Database, name: str, *, email: str | None = None,
                password: str | None = None,
                google_sub: str | None = None,
                apple_sub: str | None = None) -> dict:
    """
    Erstellt einen neuen User in der DB. Hash das Passwort, falls gegeben.
    Speichert googleSub/appleSub nur, wenn sie nicht None sind.
    Gibt das erstellte User-Dokument zurück (ohne Passwort-Hash).
    """
    if not name:
        raise ValueError("Username is required")

    # Basisdokument für den neuen Benutzer
    doc = {
        "name": name.lower().strip(),
        "email": email,
        "fcmTokens": [], # Liste für Firebase Cloud Messaging Tokens
        "created": datetime.datetime.utcnow().isoformat(),
    }

    # Passwort hashen und hinzufügen, falls vorhanden
    if password:
        # Hier könnte man Längenprüfung etc. hinzufügen, falls nicht schon in API-Route geschehen
        doc["pwHash"] = ph.hash(password)
    else:
        # Setze pwHash auf None, wenn kein Passwort angegeben wurde (wichtig für verify_password)
        doc["pwHash"] = None

    # --- FIX: googleSub und appleSub nur hinzufügen, wenn sie nicht None sind ---
    if google_sub is not None:
        doc["googleSub"] = google_sub
    if apple_sub is not None:
        doc["appleSub"] = apple_sub
    # -----------------------------------------------------------------------

    try:
        # Versuche, den Benutzer einzufügen
        result = _users(db).insert_one(doc)
        doc["_id"] = result.inserted_id # Füge die DB-ID für die Rückgabe hinzu
        # Entferne sensible Daten vor der Rückgabe an den API-Caller
        if "pwHash" in doc:
            del doc["pwHash"]
        return doc
    except Exception as e:
         # Hier könnte man spezifischere Fehler fangen (z.B. DuplicateKeyError für 'name')
         # und entsprechende HTTP-Fehler in der API-Route zurückgeben.
         # Fürs Erste werfen wir den Fehler weiter.
        raise e


def verify_password(db: Database, name: str, password: str) -> bool:
    """ Prüft Usernamen und Passwort gegen den Hash in der DB. """
    if not name or not password:
        return False
    user = _users(db).find_one({"name": name.lower().strip()})
    # User existiert nicht oder hat keinen Passwort-Hash gesetzt
    if not user or not user.get("pwHash"):
        return False
    try:
        # Verifiziert das Passwort gegen den gespeicherten Hash
        ph.verify(user["pwHash"], password)
        # Optional: Prüfen, ob der Hash aktualisiert werden muss (Argon2-Parameter geändert?)
        # if ph.check_needs_rehash(user["pwHash"]):
        #     new_hash = ph.hash(password)
        #     _users(db).update_one({"_id": user["_id"]}, {"$set": {"pwHash": new_hash}})
        return True
    except VerifyMismatchError:
        # Passwort stimmt nicht überein
        return False
    except Exception as e:
        # Andere Fehler beim Verifizieren (sollte nicht passieren, aber sicher ist sicher)
        print(f"Error during password verification for user {name}: {e}")
        return False


def get_user_by_sub(db: Database, provider: str, sub: str) -> dict | None:
    """ Findet einen User anhand des Social Login Subs (googleSub oder appleSub). """
    if not provider or not sub:
        return None
    # Bestimme das Feld basierend auf dem Provider
    field = "googleSub" if provider == "google" else "appleSub"
    # Suche den User
    user = _users(db).find_one({field: sub})
    # Entferne sensible Daten vor der Rückgabe
    if user and "pwHash" in user:
        del user["pwHash"]
    return user

def find_user_by_name(db: Database, name: str) -> dict | None:
    """ Findet einen User anhand seines Namens (case-insensitive). """
    if not name:
        return None
    user = _users(db).find_one({"name": name.lower().strip()})
    # Entferne sensible Daten vor der Rückgabe
    if user and "pwHash" in user:
        del user["pwHash"]
    return user

# --- Optional: Funktionen zum Hinzufügen/Entfernen von FCM Tokens ---
def add_fcm_token(db: Database, username: str, token: str):
    """ Fügt einen FCM Token zum User hinzu, wenn er noch nicht existiert. """
    if not username or not token:
        return
    _users(db).update_one(
        {"name": username.lower()},
        {"$addToSet": {"fcmTokens": token}} # $addToSet verhindert Duplikate
    )

def remove_fcm_token(db: Database, username: str, token: str):
    """ Entfernt einen FCM Token vom User. """
    if not username or not token:
        return
    _users(db).update_one(
        {"name": username.lower()},
        {"$pull": {"fcmTokens": token}}
    )