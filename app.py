from flask import Flask, jsonify, make_response
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging

# 1) Deine CustomEncoder und output_json einfügen
from datetime import datetime, date
from bson import ObjectId
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data, cls=CustomJSONEncoder), code)
    resp.headers.extend(headers or {})
    return resp

# 2) Jetzt Flask app erstellen
app = Flask(__name__)
...

# JWT, CORS etc.
jwt = JWTManager(app)
CORS(app)

# 3) API erzeugen und representation überschreiben
api = Api(app)
api.representations['application/json'] = output_json

# 4) Dann deine Routen / Resources hinzufügen
...

# 5) Errorhandler
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled Exception: {e}")
    return jsonify({'success': False, 'message': 'Internal Server Error'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
