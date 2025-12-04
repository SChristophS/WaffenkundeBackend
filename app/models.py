# app/models.py
# -*- coding: utf-8 -*-
"""
User-/Auth-Model-Helfer für pymongo.
- Argon2id Hashing
- Idempotente Index-Erstellung
- Reine pymongo-Signaturen (db: Database)
"""

from __future__ import annotations
import logging
import datetime as dt
from typing import Optional

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from argon2.low_level import Type

log = logging.getLogger(__name__)

# Argon2id ist eine gute Wahl
ph = PasswordHasher(type=Type.ID)


# ───────── Intern: Collections + Indizes ─────────────────────────

def _users(db: Database) -> Collection:
    """
    Gibt die User-Collection zurück und stellt sicher, dass
    notwendige Indizes existieren (idempotent).
    """
    col = db["users"]
    try:
        # schneller Login über name
        col.create_index([("name", ASCENDING)], unique=True, name="name_1")
        # Social-Subs (optional, sparse+unique => mehrere fehlende Werte erlaubt)
        col.create_index("googleSub", unique=True, sparse=True, name="googleSub_1")
        col.create_index("appleSub", unique=True, sparse=True, name="appleSub_1")
    except Exception as e:
        log.warning("Index-Erstellung users fehlgeschlagen: %s", e)
    return col


# ───────── Public API ─────────────────────────────────────────────

def ensure_user_indexes(db: Database) -> None:
    """
    Kann beim App-Start aufgerufen werden, um Indizes sicherzustellen.
    """
    _ = _users(db)  # löst create_index() aus


def utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def create_user(
    db: Database,
    name: str,
    *,
    email: Optional[str] = None,
    password: Optional[str] = None,
    google_sub: Optional[str] = None,
    apple_sub: Optional[str] = None,
) -> dict:
    """
    Erstellt einen neuen User.
    - name wird lower+trim gespeichert (unique)
    - Passwort wird mit Argon2id gehasht, falls angegeben
    - googleSub / appleSub werden nur gesetzt, wenn nicht None
    Gibt das gespeicherte Dokument ohne pwHash zurück.
    """
    if not name:
        raise ValueError("Username is required")

    doc = {
        "name": name.lower().strip(),
        "email": email,
        "fcmTokens": [],  # optional für Push
        "created": utcnow_iso(),
    }

    if password:
        doc["pwHash"] = ph.hash(password)
    else:
        doc["pwHash"] = None

    if google_sub is not None:
        doc["googleSub"] = google_sub
    if apple_sub is not None:
        doc["appleSub"] = apple_sub

    res = _users(db).insert_one(doc)
    doc["_id"] = res.inserted_id

    # sensible Felder nicht rausgeben
    doc.pop("pwHash", None)
    return doc


def verify_password(db: Database, name: str, password: str) -> bool:
    """
    Prüft Klartext-Passwort gegen gespeicherten Argon2id-Hash.
    Gibt False zurück, wenn User fehlt oder kein Hash gesetzt ist.
    """
    if not name or not password:
        return False

    user = _users(db).find_one({"name": name.lower().strip()})
    if not user or not user.get("pwHash"):
        return False

    try:
        ph.verify(user["pwHash"], password)
        # Optional: Rehash falls Parameter geändert wurden:
        # if ph.check_needs_rehash(user["pwHash"]):
        #     _users(db).update_one({"_id": user["_id"]}, {"$set": {"pwHash": ph.hash(password)}})
        return True
    except VerifyMismatchError:
        return False
    except Exception as e:
        log.error("Fehler beim Verifizieren von %s: %s", name, e)
        return False


def get_user_by_sub(db: Database, provider: str, sub: str) -> Optional[dict]:
    """
    Liefert User anhand Social-Login-Sub (google / apple).
    Entfernt pwHash vor Rückgabe.
    """
    if not provider or not sub:
        return None
    field = "googleSub" if provider.lower() == "google" else "appleSub"
    user = _users(db).find_one({field: sub})
    if user:
        user.pop("pwHash", None)
    return user


def find_user_by_name(db: Database, name: str) -> Optional[dict]:
    """
    Liefert User anhand des Namens (case-insensitive).
    Entfernt pwHash vor Rückgabe.
    """
    if not name:
        return None
    user = _users(db).find_one({"name": name.lower().strip()})
    if user:
        user.pop("pwHash", None)
    return user


def add_fcm_token(db: Database, username: str, token: str) -> None:
    """
    Fügt FCM-Token hinzu (ohne Duplikate).
    """
    if not username or not token:
        return
    _users(db).update_one(
        {"name": username.lower().strip()},
        {"$addToSet": {"fcmTokens": token}},
    )


def remove_fcm_token(db: Database, username: str, token: str) -> None:
    """
    Entfernt FCM-Token.
    """
    if not username or not token:
        return
    _users(db).update_one(
        {"name": username.lower().strip()},
        {"$pull": {"fcmTokens": token}},
    )
