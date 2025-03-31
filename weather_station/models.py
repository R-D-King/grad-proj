from datetime import datetime
from shared.config import db

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)  # درجة الحرارة
    humidity = db.Column(db.Float)  # رطوبة الجو
    soil_moisture = db.Column(db.Float)  # رطوبة التربة
    wind_speed = db.Column(db.Float)  # سرعة الرياح
    pressure = db.Column(db.Float)  # ضغط الجو