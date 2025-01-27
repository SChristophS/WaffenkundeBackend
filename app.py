from datetime import datetime, date
import logging

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from flask.json.provider import DefaultJSONProvider
from bson import ObjectId  # Für ObjectId -> str, falls nötig

from config import Config
from utils.logging_config import configure_logging
from resources.auth import Register, Login
from resources.questions import QuestionsList
from resources.lexicon import LexiconList


# 1) Neuen JSON-Provider definieren, der Datums- und ObjectId-Felder automatisch umwandelt
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        # Datumsfelder in ISO-Strings konvertieren
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()  # z. B. "2025-01-28T15:04:16.286Z"

        # Optional: ObjectId -> String
        if isinstance(obj, ObjectId):
            return str(obj)

        # Falls kein Spezialfall, Standardverhalten
        return super().default(obj)


# 2) Flask-App erstellen
app = Flask(__name__)
app.config.from_object(Config)

# 3) Custom JSON Provider registrieren (statt app.json_encoder = ...)
app.json_provider_class = CustomJSONProvider

# JWT initialisieren
jwt = JWTManager(app)

# CORS erlauben
CORS(app)

# RESTful-API
api = Api(app)

# Logging
configure_logging(app.config['DEBUG'])


# Exception-Handler
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled Exception: {e}")
    return jsonify({'success': False, 'message': 'An internal server error occurred'}), 500


# Routen/Resources
api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(QuestionsList, '/api/questions')
api.add_resource(LexiconList, '/api/lexicon')


if __name__ == '__main__':
    # Debug=True => Flask-Neustart bei Codeänderungen, dev-Server
    app.run(host='0.0.0.0', port=5000, debug=True)
