import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://user:password@localhost/mqc_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

