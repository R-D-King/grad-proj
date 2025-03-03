from flask_sqlalchemy import SQLAlchemy

# تعريف db
db = SQLAlchemy()

# إعدادات التطبيق
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'  # مسار قاعدة البيانات
    SQLALCHEMY_TRACK_MODIFICATIONS = False