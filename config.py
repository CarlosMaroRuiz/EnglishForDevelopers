import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or ''
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY') or ''
    DATABASE_PATH = 'english_tutor.db'

