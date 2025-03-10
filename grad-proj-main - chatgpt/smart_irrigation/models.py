from datetime import datetime, time
from shared.config import db

class IrrigationData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    pump_status = db.Column(db.Boolean)  # حالة المضخة (تشغيل/إيقاف)
    water_level = db.Column(db.Float)  # مستوى المياه
    pump_duration = db.Column(db.Float)  # مدة التشغيل (بالثواني)

# جدول لتخزين جداول الري
class IrrigationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)  # وقت بدء التشغيل
    duration = db.Column(db.Float, nullable=False)  # مدة التشغيل (بالثواني)
    active = db.Column(db.Boolean, default=True)  # هل الجدول نشط؟
    preset_id = db.Column(db.Integer, db.ForeignKey('irrigation_preset.id'))  # مفتاح أجنبي

# جدول لتخزين الـ presets
class IrrigationPreset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # اسم الـ preset (مثل "طماطم")
    schedules = db.relationship('IrrigationSchedule', backref='preset', lazy=True)  # جداول الري المرتبطة