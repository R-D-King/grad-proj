from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

class Config:
    # Use absolute path for database
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "instance", "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False