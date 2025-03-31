from flask import jsonify
from shared.database import db
from shared.socketio import socketio
from .models import Preset, Schedule, IrrigationLog
from datetime import datetime

# Global variable to track pump start time
pump_start_time = None

def get_all_presets():
    """Get all irrigation presets."""
    presets = Preset.query.all()
    return [preset.to_dict() for preset in presets]

def get_preset_details(preset_id):
    """Get details for a specific preset."""
    preset = Preset.query.get_or_404(preset_id)
    return preset.to_dict(include_schedules=True)

def create_preset(data):
    """Create a new irrigation preset."""
    preset = Preset(name=data['name'])
    db.session.add(preset)
    db.session.commit()
    return preset.to_dict()

def activate_preset(preset_id):
    """Activate a specific preset."""
    # Deactivate all presets
    Preset.query.update({Preset.active: False})
    
    # Activate the selected preset
    preset = Preset.query.get_or_404(preset_id)
    preset.active = True
    db.session.commit()
    
    # Notify clients via WebSocket
    socketio.emit('preset_activated', {'preset_id': preset_id, 'name': preset.name})
    
    return preset.to_dict()

def delete_preset(preset_id):
    """Delete a preset."""
    preset = Preset.query.get_or_404(preset_id)
    db.session.delete(preset)
    db.session.commit()
    return {'status': 'success', 'message': f'Preset {preset_id} deleted'}

def create_schedule(data):
    """Create a new schedule."""
    schedule = Schedule(
        start_time=data['start_time'],
        duration=data['duration'],
        preset_id=data['preset_id']
    )
    db.session.add(schedule)
    db.session.commit()
    return schedule.to_dict()

def update_schedule(schedule_id, data):
    """Update an existing schedule."""
    schedule = Schedule.query.get_or_404(schedule_id)
    schedule.start_time = data['start_time']
    schedule.duration = data['duration']
    schedule.active = data['active']
    db.session.commit()
    return schedule.to_dict()

def delete_schedule(schedule_id):
    """Delete a schedule."""
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    return {'status': 'success', 'message': f'Schedule {schedule_id} deleted'}

def start_pump():
    """Start the irrigation pump."""
    # Store the start time in a global variable
    global pump_start_time
    pump_start_time = datetime.now()
    
    # Logic to start the pump would go here
    # For now, just log the event and notify clients
    log = IrrigationLog(pump_status=True, water_level=get_water_level())
    db.session.add(log)
    db.session.commit()
    
    socketio.emit('pump_status', {'status': 'running'})
    return {'status': 'success', 'message': 'Pump started'}

def stop_pump():
    """Stop the irrigation pump."""
    # Calculate duration if we have a start time
    global pump_start_time
    duration = None
    if pump_start_time:
        duration = (datetime.now() - pump_start_time).total_seconds()
        pump_start_time = None
    
    # Logic to stop the pump would go here
    # For now, just log the event and notify clients
    log = IrrigationLog(pump_status=False, water_level=get_water_level(), duration=duration)
    db.session.add(log)
    db.session.commit()
    
    socketio.emit('pump_status', {'status': 'stopped'})
    return {'status': 'success', 'message': 'Pump stopped'}

def check_schedule_time(schedule_id):
    """Check if a schedule should run based on current time."""
    schedule = Schedule.query.get_or_404(schedule_id)
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Simple time comparison
    should_run = schedule.start_time == current_time and schedule.active
    
    return {'should_run': should_run}


from irrigation.models import IrrigationLog

def log_irrigation_event(preset_id=None, duration=None, water_used=None, pump_status=None, water_level=None):
    """
    Log an irrigation event to the database.
    """
    try:
        # Ensure duration is properly converted to a float
        if duration is not None:
            try:
                duration = float(duration)
                print(f"Logging irrigation event with duration: {duration}")  # Debug print
            except (ValueError, TypeError):
                print(f"Invalid duration value: {duration}, defaulting to 0")  # Debug print
                duration = 0.0
        else:
            print("Duration is None, defaulting to 0")  # Debug print
            duration = 0.0
        
        # Create a new irrigation log entry
        log_entry = IrrigationLog(
            preset_id=preset_id,
            duration=duration,
            water_used=water_used,
            pump_status=pump_status,
            water_level=water_level,
            timestamp=datetime.now()
        )
        
        # Debug print the log entry before saving
        print(f"Log entry before save: preset_id={log_entry.preset_id}, duration={log_entry.duration}, pump_status={log_entry.pump_status}")
        
        # Add and commit to the database
        db.session.add(log_entry)
        db.session.commit()
        
        # Debug print after save
        print(f"Successfully logged irrigation event with ID: {log_entry.id}, duration: {log_entry.duration}")
        return True
    except Exception as e:
        print(f"Error logging irrigation event: {e}")
        db.session.rollback()
        return False

def get_water_level():
    """
    Get the current water level from the sensor or return a default value.
    This is a placeholder function that should be implemented with actual sensor reading.
    """
    try:
        # In a real implementation, this would read from a sensor
        # For now, return a default value (e.g., 75% water level)
        return 75.0
    except Exception as e:
        print(f"Error getting water level: {e}")
        # Return a default value if there's an error
        return 50.0