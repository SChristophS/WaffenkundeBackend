import os
from os import environ
from datetime import timedelta

class Config:
    # ➜ Stelle sicher, dass in MONGO_URI die DB enthalten ist (siehe .env unten).
    MONGO_URI  = environ.get("MONGO_URI", "mongodb://localhost:2000/WaffenkundeApp")

    # JWT
    JWT_SECRET_KEY = environ.get("JWT_SECRET_KEY", "dev-secret")


    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(minutes=int(environ.get("JWT_ACCESS_MIN", 15)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(environ.get("JWT_REFRESH_DAYS", 30)))

    JWT_TOKEN_LOCATION = ["headers", "query_string"]  # Header ODER Query
    JWT_QUERY_STRING_NAME = "access"                  # ?access=...
    JWT_HEADER_TYPE = "Bearer"                        # (Standard, optional)
    
    # Flask/Session Secret
    SECRET_KEY = environ.get("SECRET_KEY", "dev-secret")

    # Admin-Whitelist für Feedback-UI/API (kommagetrennt)
    FEEDBACK_ADMINS = environ.get("FEEDBACK_ADMINS", "")   # z.B. "alice,bob"

    # CORS (optional, Komma-getrennt)
    CORS_ORIGINS = environ.get("CORS_ORIGINS", "*")

    # Logging-Level (optional)
    LOG_LEVEL = environ.get("LOG_LEVEL", "DEBUG")

    # Social
    GOOGLE_OAUTH_CLIENT_ID = environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    APPLE_OAUTH_SERVICE_ID = environ.get("APPLE_OAUTH_SERVICE_ID", "")
