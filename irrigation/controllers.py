import time
import threading
import logging  # Add this import
from datetime import datetime
import eventlet
from flask import current_app
from shared.database import db
from hardware.relay import Relay
from hardware.water_level import WaterLevelSensor
from .models import Preset, PumpLog, IrrigationLog

# Set up logging
logger = logging.getLogger(__name__)

# Initialize hardware
pump = Relay(pin=17, name="Water Pump", simulation=True)
water_level_sensor = WaterLevelSensor(simulation=True)

# Global variables for pump state
pump_running = False
pump_start_time = None
pump_lock = threading.Lock()

def get_pump_status():
    """Get the current status of the irrigation pump."""
    with pump_lock:
        return {
            "running": pump_running,
            "start_time": pump_start_time.isoformat() if pump_start_time else None,
            "duration": get_pump_duration() if pump_running else 0
        }

def get_pump_duration():
    """Get the current duration of the pump running in seconds."""
    if not pump_running or not pump_start_time:
        return 0
    
    return (datetime.now() - pump_start_time).total_seconds()

def get_water_level():
    """Get the current water level."""
    level = water_level_sensor.get_level()
    return {
        "level": level,
        "status": "OK" if level > 20 else "LOW"
    }

def log_pump_action(action, duration=None):
    """Log pump actions to the database."""
    log = PumpLog(
        action=action,
        duration=duration if action == 'stop' else None,
        timestamp=datetime.now()
    )
    db.session.add(log)
    db.session.commit()

def log_irrigation_event(preset_id=None, duration=None, pump_status=None, water_level=None):
    """Log irrigation events to the database."""
    log = IrrigationLog(
        preset_id=preset_id,
        duration=duration,
        water_used=calculate_water_used(duration) if duration else None,
        pump_status=pump_status,
        water_level=water_level,
        timestamp=datetime.now()
    )
    db.session.add(log)
    db.session.commit()

def calculate_water_used(duration):
    """Calculate water used based on duration."""
    # Assuming a flow rate of 2 liters per minute
    flow_rate = 2.0 / 60.0  # liters per second
    return duration * flow_rate if duration else 0

def start_pump(preset_id=None):
    """Start the irrigation pump."""
    global pump_running, pump_start_time
    
    with pump_lock:
        if pump_running:
            return {"status": "warning", "message": "Water Pump already running", "runtime": get_pump_duration(), "pump_status": pump.get_state()}
        
        # Check water level
        water_level = get_water_level()
        if water_level['level'] < 20:
            return {"status": "error", "message": "Water level too low", "water_level": water_level}
        
        # Start the pump
        pump.on()
        pump_running = True
        pump_start_time = datetime.now()
        
        # Log pump start in database
        log_pump_action("start")
        
        # Log the irrigation event
        log_irrigation_event(preset_id=preset_id, pump_status=True, water_level=water_level['level'])
        
        return {
            "status": "success", 
            "message": "Water Pump started", 
            "runtime": 0,
            "pump_status": pump.get_state()
        }

def stop_pump():
    """Stop the irrigation pump."""
    global pump_running, pump_start_time, pump_duration
    
    with pump_lock:
        if not pump_running:
            return {"status": "warning", "message": "Water Pump was not running", "runtime": 0, "pump_status": pump.get_status()}
        
        # Get the current duration before stopping
        current_duration = get_pump_duration()
        
        # Stop the pump
        pump.off()
        pump_running = False
        pump_start_time = None
        
        # Log pump stop in database with duration
        log_pump_action("stop", current_duration)
        
        # Log the irrigation event with duration
        log_irrigation_event(duration=current_duration, pump_status=False, water_level=get_water_level()['level'])
        
        return {
            "status": "success", 
            "message": "Water Pump stopped", 
            "runtime": current_duration,
            "pump_status": pump.get_state()
        }

def get_presets():
    """Get all irrigation presets."""
    presets = Preset.query.all()
    return [preset.to_dict(include_schedules=True) for preset in presets]

def get_preset(preset_id):
    """Get a specific irrigation preset."""
    preset = Preset.query.get(preset_id)
    if preset:
        return preset.to_dict(include_schedules=True)
    return None

def create_preset(data):
    """Create a new irrigation preset."""
    preset = Preset(
        name=data.get('name', 'New Preset'),
        active=data.get('active', False),
        duration=data.get('duration', 300),
        water_level=data.get('water_level', 50),
        auto_start=data.get('auto_start', False)
    )
    db.session.add(preset)
    db.session.commit()
    return preset.to_dict()

def update_preset(preset_id, data):
    """Update an existing irrigation preset."""
    preset = Preset.query.get(preset_id)
    if not preset:
        return None
    
    if 'name' in data:
        preset.name = data['name']
    if 'active' in data:
        preset.active = data['active']
    if 'duration' in data:
        preset.duration = data['duration']
    if 'water_level' in data:
        preset.water_level = data['water_level']
    if 'auto_start' in data:
        preset.auto_start = data['auto_start']
    
    db.session.commit()
    return preset.to_dict()

def delete_preset(preset_id):
    """Delete an irrigation preset."""
    preset = Preset.query.get(preset_id)
    if not preset:
        return False
    
    db.session.delete(preset)
    db.session.commit()
    return True

def get_irrigation_logs(limit=50):
    """Get recent irrigation logs."""
    logs = IrrigationLog.query.order_by(IrrigationLog.timestamp.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]