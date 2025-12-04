# app/extensions.py
import os, sys, logging, pymongo
from logging.handlers import RotatingFileHandler
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

cors = CORS()
jwt = JWTManager()
socketio = SocketIO()

def init_logging():
    logger = logging.getLogger()
    if logger.handlers:
        return
    level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    logger.setLevel(level)

    fmt = "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
    formatter = logging.Formatter(fmt)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)

    # konfigurierbare Loggrößen via ENV, mit sinnvollen Defaults
    max_bytes = int(os.environ.get("LOG_MAX_BYTES", 5_000_000))   # ~5 MB
    backup_cnt = int(os.environ.get("LOG_BACKUP_COUNT", 3))       # 3 Rotationsdateien

    log_file = os.path.join(os.path.dirname(__file__), "..", "log.txt")
    file = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_cnt,
        encoding="utf-8",
    )
    file.setFormatter(formatter)
    file.setLevel(level)

    logger.addHandler(console)
    logger.addHandler(file)

def init_db(app):
    """Erzeuge einen globalen MongoClient in app.config['MONGO_CLIENT']."""
    if "MONGO_CLIENT" not in app.config:
        app.config["MONGO_CLIENT"] = pymongo.MongoClient(app.config["MONGO_URI"])
