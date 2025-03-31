from datetime import datetime
from shared.config import db

class IrrigationPreset(db.Model):
    __tablename__ = 'irrigation_presets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with schedules
    schedules = db.relationship('IrrigationSchedule', backref='preset', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<IrrigationPreset {self.name}>'

class IrrigationSchedule(db.Model):
    __tablename__ = 'irrigation_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Float, nullable=False)  # Duration in seconds
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Foreign key to preset
    preset_id = db.Column(db.Integer, db.ForeignKey('irrigation_presets.id'), nullable=False)
    
    def __repr__(self):
        return f'<IrrigationSchedule {self.start_time} for {self.duration}s>'

class IrrigationData(db.Model):
    __tablename__ = 'irrigation_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    pump_status = db.Column(db.Boolean, default=False)
    water_level = db.Column(db.Float, default=0)  # Water level in percentage
    pump_duration = db.Column(db.Float, default=0)  # Duration in seconds
    
    def __repr__(self):
        return f'<IrrigationData {self.timestamp} - Pump: {self.pump_status}, Level: {self.water_level}%>'

# Add the WeatherData model to your existing models file
class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    pressure = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'soil_moisture': self.soil_moisture,
            'wind_speed': self.wind_speed,
            'pressure': self.pressure
        }