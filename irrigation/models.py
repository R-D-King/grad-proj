from datetime import datetime
from shared.database import db

class Preset(db.Model):
    """Model for irrigation presets with schedules."""
    __tablename__ = 'presets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=False)
    duration = db.Column(db.Integer, default=300)  # Duration in seconds
    water_level = db.Column(db.Integer, default=50)  # Water level threshold in percentage
    auto_start = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedules = db.relationship('Schedule', backref='preset', lazy=True, cascade="all, delete-orphan")
    irrigation_logs = db.relationship('IrrigationLog', backref='preset', lazy=True)
    
    def to_dict(self, include_schedules=False):
        result = {
            'id': self.id,
            'name': self.name,
            'active': self.active,
            'duration': self.duration,
            'water_level': self.water_level,
            'auto_start': self.auto_start,
            'created_at': self.created_at.isoformat()
        }
        
        if include_schedules:
            result['schedules'] = [schedule.to_dict() for schedule in self.schedules]
        else:
            result['schedules'] = []
            
        return result

class Schedule(db.Model):
    """Model for irrigation schedules."""
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
    duration = db.Column(db.Float, nullable=True)  # Duration in seconds
    water_used = db.Column(db.Float, nullable=True)  # Amount of water used in liters
    pump_status = db.Column(db.Boolean, nullable=True)  # True if pump was running
    water_level = db.Column(db.Float, nullable=True)  # Water level percentage
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