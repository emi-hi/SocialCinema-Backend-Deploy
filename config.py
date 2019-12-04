from os import environ
import os
import dotenv

dotenv.load_dotenv()
DB_NAME = os.getenv('DB_NAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
SQLALCHEMY_DATABASE = os.getenv('heroku_db')


class Config:
  TESTING = environ.get('TESTING')
  FLASK_DEBUG = environ.get('FLASK_DEBUG')
  SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE
  SQLALCHEMY_TRACK_MODIFICATIONS = False
