from os import environ
from datetime import timedelta

class Config:
    MONGO_URI  = environ.get("MONGO_URI", "mongodb://localhost:2000/WaffenkundeApp")

    # JWT
    JWT_SECRET_KEY            = environ.get("JWT_SECRET_KEY", "dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(minutes=int(environ.get("JWT_ACCESS_MIN", 15)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(environ.get("JWT_REFRESH_DAYS", 30)))

    # Social
    GOOGLE_OAUTH_CLIENT_ID = environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    APPLE_OAUTH_SERVICE_ID = environ.get("APPLE_OAUTH_SERVICE_ID", "")
