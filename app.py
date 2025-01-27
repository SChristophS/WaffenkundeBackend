from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils.logging_config import configure_logging
from resources.auth import Register, Login
from resources.questions import QuestionsList
from resources.lexicon import LexiconList
import logging

# Flask-App-Instanz erstellen
app = Flask(__name__)
app.config.from_object(Config)

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

# Main-Block
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
