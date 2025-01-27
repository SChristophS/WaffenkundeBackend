# utils/validations.py

import re
from bson.objectid import ObjectId
from flask import current_app

def is_valid_name(name):
    return bool(name and name.strip())

def is_valid_object_id(oid):
    return ObjectId.is_valid(oid)

def allowed_file(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_password(password):
    # Passwort muss mindestens 8 Zeichen, eine Zahl und ein Sonderzeichen enthalten
    return len(password) >= 8 and any(char.isdigit() for char in password) and any(not char.isalnum() for char in password)
