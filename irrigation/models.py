from datetime import datetime
from shared.database import db

class Preset(db.Model):
    __tablename__ = 'presets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedules = db.relationship('Schedule', backref='preset', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self, include_schedules=False):
        result = {
            'id': self.id,
            'name': self.name,
            'active': self.active,
            'created_at': self.created_at.isoformat()
        }
        
        if include_schedules:
            result['schedules'] = [schedule.to_dict() for schedule in self.schedules]
        else:
            result['schedules'] = []
            
        return result

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(8), nullable=False)  # Format: HH:MM:SS
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    active = db.Column(db.Boolean, default=True)
    preset_id = db.Column(db.Integer, db.ForeignKey('presets.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time,
            'duration': self.duration,
            'active': self.active,
            'preset_id': self.preset_id
        }

class IrrigationLog(db.Model):
    """Model for irrigation log entries."""
    __tablename__ = 'irrigation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    preset_id = db.Column(db.Integer, db.ForeignKey('presets.id'), nullable=True)  # Changed from 'irrigation_presets.id'
    duration = db.Column(db.Float, nullable=True)
    water_used = db.Column(db.Float, nullable=True)
    pump_status = db.Column(db.Boolean, nullable=True)
    water_level = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'preset_id': self.preset_id,
            'duration': self.duration,
            'water_used': self.water_used,
            'pump_status': self.pump_status,
            'water_level': self.water_level,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }