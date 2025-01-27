from datetime import datetime, date
from bson import ObjectId
import logging

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Wichtig: Ergänzung
from flask_restful.representations import json
from json import JSONEncoder

from config import Config
from utils.logging_config import configure_logging
from resources.auth import Register, Login
from resources.questions import QuestionsList
from resources.lexicon import LexiconList

# Hier definierst du den Encoder für Flask-RESTful:
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Diese Zeile sagt Flask-RESTful: nutze unseren Encoder
json.settings["cls"] = CustomJSONEncoder


app = Flask(__name__)
app.config.from_object(Config)

# JWT initialisieren
jwt = JWTManager(app)

# CORS erlauben
CORS(app)

# Logging
configure_logging(app.config['DEBUG'])

# Flask-RESTful-API initialisieren (NACH dem Encoder-Setup)
api = Api(app)

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Exception: {e}")
    return jsonify({'success': False, 'message': 'An internal server error occurred'}), 500

# Routen
api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(QuestionsList, '/api/questions')
api.add_resource(LexiconList, '/api/lexicon')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
