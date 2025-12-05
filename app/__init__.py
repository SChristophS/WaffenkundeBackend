# app/__init__.py
import os
import logging
from datetime import timedelta
from flask import Flask, request, jsonify

from config import Config
from .extensions import cors, jwt, socketio, init_logging, init_db
from .metrics import init_metrics

# Blueprints
from .blueprints.auth import auth_bp
from .blueprints.games import games_bp
from .blueprints.analytics import analytics_bp
from .blueprints.feedback import feedback_bp
from .blueprints.friends import friends_bp

# Socket.IO
from .sockets import register_socketio_handlers

# JWT-Utils
from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt,
    create_access_token,
    decode_token,
)

def create_app() -> Flask:
    init_logging()
    log = logging.getLogger(__name__)

    app = Flask(__name__)
    app.config.from_object(Config)

    # --- JWT Secret aus ENV setzen (oder DEV-Default) ---
    secret_from_env = os.environ.get("JWT_SECRET_KEY")
    if not secret_from_env:
        log.warning("⚠️ JWT_SECRET_KEY nicht in Env gesetzt – nehme DEV-Default!")
        secret_from_env = "dev-secret"
    app.config["JWT_SECRET_KEY"] = secret_from_env
    log.info(f"🔑 JWT_SECRET_KEY length={len(secret_from_env)}")

    # --- Konsistenz-Check mit .jwt_secret ---
    secret_file = os.path.join(os.path.dirname(__file__), "..", ".jwt_secret")
    if os.path.exists(secret_file):
        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                expected_secret = f.read().strip()
            if expected_secret != secret_from_env:
                log.critical(
                    "❌ JWT_SECRET_KEY MISMATCH!\n"
                    f"ENV:  {secret_from_env}\n"
                    f"FILE: {expected_secret}"
                )
                raise SystemExit("JWT_SECRET_KEY mismatch – Server stoppt!")
        except Exception as e:
            log.warning(f"⚠️ Konnte .jwt_secret nicht lesen: {e}")
    else:
        try:
            with open(secret_file, "w", encoding="utf-8") as f:
                f.write(secret_from_env)
            log.info("📝 .jwt_secret erstellt.")
        except Exception as e:
            log.warning(f"⚠️ Konnte .jwt_secret nicht schreiben: {e}")

    # --- CORS (vor Register der Blueprints ok) ---
    origins_env = os.environ.get("CORS_ORIGINS", "").strip()

    if origins_env == "*":
        # Vollständig offen (DEV / Debug). In diesem Modus erlauben wir kein
        # Credential-Sharing, damit Access-Control-Allow-Origin="*" gesetzt werden kann.
        cors.init_app(
            app,
            supports_credentials=False,
            origins="*",
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["Content-Disposition"],
        )
        log.info("CORS: origins='*' (ohne Credentials)")
    else:
        origins = [o.strip() for o in origins_env.split(",") if o.strip()]
        if not origins:
            origins = ["http://localhost:8080", "http://127.0.0.1:8080"]

        cors.init_app(
            app,
            supports_credentials=True,
            origins=origins,
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["Content-Disposition"],
        )
        log.info("CORS: origins=%s", origins)

    # --- JWT MANAGER INITIALISIEREN (muss vor Startup-Test passieren!) ---
    jwt.init_app(app)

    # --- Mongo verbinden ---
    init_db(app)

    # --- JWT Startup-Test (jetzt mit init_app + App-Kontext) ---
    from flask import current_app
    with app.app_context():
        try:
            test_token = create_access_token(
                identity="startup-check",
                expires_delta=timedelta(seconds=30),
            )
            decoded = decode_token(test_token)
            if decoded.get("sub") != "startup-check":
                raise ValueError("Decoded Token-Sub mismatch")
            log.info("✅ JWT Startup-Test erfolgreich – Secret stimmt und Token verifizierbar.")
        except Exception as e:
            log.critical(f"❌ JWT Startup-Test fehlgeschlagen: {e}")
            raise SystemExit("JWT Startup-Test fehlgeschlagen – Server stoppt!")

    # --- Feedback-Admins loggen (nur Info) ---
    app.config["FEEDBACK_ADMINS"] = os.environ.get("FEEDBACK_ADMINS", "")
    log.info("FEEDBACK_ADMINS=%s", app.config["FEEDBACK_ADMINS"])

    # --- Prometheus-Metriken initialisieren ---
    try:
        init_metrics(app)
        log.info("Prometheus-Metriken aktiviert – /metrics Endpoint verfügbar.")
    except Exception as e:
        log.warning(f"⚠️ Konnte Prometheus-Metriken nicht initialisieren: {e}")

    # --- Blueprints registrieren ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(friends_bp)



    # --- Socket.IO ---
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
        ping_timeout=25,
        ping_interval=10,
    )
    register_socketio_handlers(socketio)

    # --- Request/Response Logging + sanfte JWT-Validierung ---
    @app.before_request
    def _log_req():
        lg = logging.getLogger("req")
        ah = request.headers.get("Authorization", "")
        tok_preview = ah.split()[1][:15] + "..." if ah.startswith("Bearer ") else None
        lg.info(
            "⇢ %s %s  auth=%s token=%s",
            request.method, request.path,
            ("yes" if tok_preview else "no"),
            tok_preview,
        )
        try:
            verify_jwt_in_request(optional=True)
            payload = get_jwt()
            if payload:
                lg.info(
                    "JWT ok: sub=%s type=%s exp=%s",
                    payload.get("sub"),
                    payload.get("type"),
                    payload.get("exp"),
                )
        except Exception as e:
            lg.warning("JWT verification failed: %s", e)

    @app.after_request
    def _log_resp(resp):
        logging.getLogger("req").info("⇠ %s (%s %s)", resp.status, request.method, request.path)
        return resp

    # --- JWT Fehlerhandler ---
    @jwt.unauthorized_loader
    def _unauthorized(reason: str):
        logging.getLogger("req").warning(
            "401 unauthorized_loader: Token fehlt oder ist fehlerhaft im Format (%s)", reason
        )
        return jsonify(msg="missing or malformed token", detail=reason), 401

    @jwt.invalid_token_loader
    def _invalid(reason: str):
        # Unterscheide typische Fehler
        log = logging.getLogger("req")
        if "Signature verification failed" in reason:
            log.error("422 invalid_token_loader: ❌ Signatur ungültig – evtl. altes Token oder Secret geändert")
        elif "Not enough segments" in reason:
            log.error("422 invalid_token_loader: ❌ Token-Struktur fehlerhaft")
        else:
            log.error("422 invalid_token_loader: ❌ Sonstiger JWT-Fehler: %s", reason)
        return jsonify(msg="invalid token", detail=reason), 422

    @jwt.expired_token_loader
    def _expired(jwt_header, jwt_payload):
        logging.getLogger("req").warning(
            "401 expired_token_loader: Token abgelaufen – sub=%s exp=%s",
            jwt_payload.get("sub"), jwt_payload.get("exp")
        )
        return jsonify(msg="token expired"), 401

    @jwt.needs_fresh_token_loader
    def _needs_fresh(jwt_header, jwt_payload):
        return jsonify(msg="fresh token required"), 401

    @jwt.revoked_token_loader
    def _revoked(jwt_header, jwt_payload):
        logging.getLogger("req").warning(
            "401 revoked_token_loader: Token widerrufen – sub=%s", jwt_payload.get("sub")
        )
        return jsonify(msg="token revoked"), 401


    # --- Health ---
    @app.get("/health")
    def health():
        from .utils import _now
        return {"ok": True, "time": _now()}

    # --- Favicon (404 vermeiden) ---
    @app.get("/favicon.ico")
    def favicon():
        # Leere Antwort, Browser hört auf zu meckern
        return "", 204

    return app
