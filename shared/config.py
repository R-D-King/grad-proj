from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()  # إنشاء كائن SQLAlchemy

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'  # قاعدة بيانات SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False