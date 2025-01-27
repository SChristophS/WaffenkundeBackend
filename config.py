from dotenv import load_dotenv
import os

load_dotenv()  # Lädt die .env-Datei

class Config:
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    TESTING = os.getenv('TESTING', 'False') == 'True'
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://192.168.178.25:49160/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'exam_app')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
