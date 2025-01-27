from datetime import date, datetime
from flask.json.provider import DefaultJSONProvider
import logging

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from utils.logging_config import configure_logging
from resources.auth import Register, Login
from resources.questions import QuestionsList
from resources.lexicon import LexiconList

# 1) Neue JSON-Provider-Klasse definieren
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        # Alle datetime- und date-Objekte in ISO-Strings umwandeln
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # Ansonsten ruft er den Standard-Serializer von Flask auf
        return super().default(obj)

# 2) Flask-App erstellen
app = Flask(__name__)
app.config.from_object(Config)

# 3) Neuen Provider registrieren (anstatt app.json_encoder = ...)
app.json_provider_class = CustomJSONProvider

# JWT initialisieren
jwt = JWTManager(app)

# Cross-Origin Resource Sharing
CORS(app)

# Flask-RESTful API
api = Api(app)

# Logging konfigurieren
configure_logging(app.config['DEBUG'])

# Fehlerbehandlung registrieren
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled Exception: {e}")
    return jsonify({'success': False, 'message': 'An internal server error occurred'}), 500

# API-Ressourcen hinzufügen
api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(QuestionsList, '/api/questions')
api.add_resource(LexiconList, '/api/lexicon')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
