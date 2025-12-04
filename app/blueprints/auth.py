# app/blueprints/auth.py
import logging
from datetime import timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import check_password_hash, generate_password_hash

import pymongo

log = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _users_col():
    mongo = current_app.config["MONGO_CLIENT"]
    return mongo.get_default_database()["users"]


def _normalize_username(val: str | None) -> str:
    return (val or "").strip().lower()


def _verify_password(user_doc: dict, plain_pw: str) -> bool:
    """
    Unterstützt:
      - user_doc["passwordHash"] (werkzeug / pbkdf2 / bcrypt etc.)
      - Fallback: user_doc["password"] im Klartext (Altbestand)
    """
    if not plain_pw:
        return False

    # neue/empfohlene Variante
    pw_hash = user_doc.get("passwordHash")
    if isinstance(pw_hash, str) and pw_hash:
        try:
            return check_password_hash(pw_hash, plain_pw)
        except Exception:
            # Falls ein fremdes Hash-Format o.Ä. drin ist
            log.warning("login: check_password_hash Exception (vermutlich unbekanntes Hash-Format)")
            return False

    # Fallback für wirklich alte Datensätze (Klartext in DB)
    legacy_plain = user_doc.get("password")
    if isinstance(legacy_plain, str) and legacy_plain:
        return legacy_plain == plain_pw

    return False


@auth_bp.post("/login")
def login():
    dbu = _users_col()

    body = request.get_json(silent=True) or {}
    # akzeptiere beides
    username = _normalize_username(body.get("username") or body.get("name"))
    password = body.get("password") or ""

    if not username or not password:
        return jsonify(msg="missing username or password"), 400

    user = dbu.find_one({"username": username})
    if not user:
        log.info("login 401: user not found (username=%s)", username)
        return jsonify(msg="invalid credentials"), 401

    if not _verify_password(user, password):
        log.info("login 401: password mismatch (username=%s, fields=%s)",
                 username, [k for k in user.keys() if k != "password"])
        return jsonify(msg="invalid credentials"), 401

    # OK → Tokens erstellen
    # Laufzeiten aus Config nutzen falls gesetzt
    acc_expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", timedelta(minutes=15))
    refr_expires = current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=30))

    access = create_access_token(identity=username, expires_delta=acc_expires)
    refresh = create_refresh_token(identity=username, expires_delta=refr_expires)

    log.info("login 200: success (username=%s)", username)
    return jsonify(access=access, refresh=refresh), 200


@auth_bp.post("/register")
def register():
    dbu = _users_col()
    body = request.get_json(silent=True) or {}

    username = _normalize_username(body.get("username") or body.get("name"))
    password = (body.get("password") or "").strip()
    email = (body.get("email") or "").strip()

    if not username or not password:
        return jsonify(msg="missing username or password"), 400

    if dbu.find_one({"username": username}):
        return jsonify(msg="user exists"), 409

    pw_hash = generate_password_hash(password)

    dbu.insert_one({
        "username": username,
        "email": email or None,
        "passwordHash": pw_hash,
        # Alt-Feld NICHT weiter befüllen, damit wir migrieren
        "createdAt": current_app.config.get("NOW_FN", lambda: None)() or None,
    })

    # Direkt Tokens geben (optional)
    acc_expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    refr_expires = current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES")
    access = create_access_token(identity=username, expires_delta=acc_expires)
    refresh = create_refresh_token(identity=username, expires_delta=refr_expires)

    log.info("register 201: created (username=%s)", username)
    return jsonify(access=access, refresh=refresh), 201


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    acc_expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    new_access = create_access_token(identity=identity, expires_delta=acc_expires)
    log.info("refresh 200: new access for %s", identity)
    return jsonify(access=new_access), 200
