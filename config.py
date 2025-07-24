import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:123_silky_123@localhost:5432/wordlookup')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    HF_TOKEN = os.getenv("HF_TOKEN")
