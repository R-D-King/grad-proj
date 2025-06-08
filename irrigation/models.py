from datetime import datetime
from shared.database import db
from sqlalchemy.orm import validates

class Preset(db.Model):
    """Represents a plant with a specific irrigation schedule."""
    __tablename__ = 'presets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedules = db.relationship('Schedule', backref='preset', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self, include_schedules=False):
        """Converts the preset to a dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'schedules': []
        }
        if include_schedules:
            data['schedules'] = [s.to_dict() for s in self.schedules]
        return data

class Schedule(db.Model):
    """Represents a single irrigation event in a preset's schedule."""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    preset_id = db.Column(db.Integer, db.ForeignKey('presets.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # e.g., "Monday"
    start_time = db.Column(db.Time, nullable=False)  # Time of day for irrigation
    duration_seconds = db.Column(db.Integer, nullable=False) # Duration in seconds
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        """Converts the schedule to a dictionary."""
        return {
            'id': self.id,
            'preset_id': self.preset_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'duration_seconds': self.duration_seconds,
            'is_active': self.is_active
        }

class PumpLog(db.Model):
    """Model for pump action logs."""
    __tablename__ = 'pump_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # 'start', 'stop', etc.
    duration = db.Column(db.Float, nullable=True)  # Duration in seconds if action is 'stop'
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'action': self.action,
            'duration': self.duration,
            'timestamp': self.timestamp.isoformat()
        }

class IrrigationLog(db.Model):
    """Model for irrigation log entries."""
    __tablename__ = 'irrigation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    preset_id = db.Column(db.Integer, db.ForeignKey('presets.id'), nullable=True)
    duration = db.Column(db.Float, nullable=True)
    pump_status = db.Column(db.Boolean, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    preset = db.relationship('Preset')

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'preset_id': self.preset_id,
            'preset_name': self.preset.name if self.preset else 'Manual',
            'duration': self.duration,
            'pump_status': self.pump_status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }