from datetime import datetime
from shared.config import db

class IrrigationData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    pump_status = db.Column(db.Boolean)  # حالة المضخة (تشغيل/إيقاف)
    water_level = db.Column(db.Float)  # مستوى المياه
    pump_duration = db.Column(db.Float)  # مدة التشغيل (بالثواني)