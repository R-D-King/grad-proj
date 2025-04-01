from flask import jsonify
from shared.database import db
from shared.socketio import socketio
from .models import Preset, Schedule, IrrigationLog
from datetime import datetime
from datetime import datetime
import time
import threading
import json
from flask import current_app
from shared.database import db
from .models import IrrigationPreset, PumpLog

# Global variables for pump status
pump_running = False
pump_start_time = None  # This should be a float timestamp, not a datetime
pump_duration = 0
pump_timer_thread = None
pump_lock = threading.Lock()

def get_pump_status():
    """Get the current pump status."""
    global pump_running
    return pump_running

def get_water_level():
    """Get the current water level (simulated)."""
    # In a real system, this would read from a sensor
    return 75  # Simulated 75% water level

def start_pump():
    """Start the irrigation pump."""
    global pump_running, pump_start_time, pump_timer_thread
    
    with pump_lock:
        if pump_running:
            return {"status": "warning", "message": "Pump is already running"}
        
        pump_running = True
        # Store as float timestamp instead of datetime
        pump_start_time = time.time()
        
        # Start a thread to track pump duration
        if pump_timer_thread is None or not pump_timer_thread.is_alive():
            pump_timer_thread = threading.Thread(target=pump_timer, daemon=True)
            pump_timer_thread.start()
        
        # Log pump start in database
        log_pump_action("start")
        
        return {"status": "success", "message": "Pump started successfully"}

def stop_pump():
    """Stop the irrigation pump."""
    global pump_running, pump_start_time, pump_duration
    
    with pump_lock:
        if not pump_running:
            return {"status": "warning", "message": "Pump already stopped"}
        
        pump_running = False
        
        # Calculate final duration
        if pump_start_time:
            # Handle both cases: datetime object or float timestamp
            if isinstance(pump_start_time, datetime):
                pump_duration = int((datetime.now() - pump_start_time).total_seconds())
            else:
                # It's a float timestamp
                pump_duration = int(time.time() - pump_start_time)
            
            # Reset start time
            pump_start_time = None
        
        # Log pump stop in database
        log_pump_action("stop")
        
        return {"status": "success", "message": "Pump stopped successfully"}

def pump_timer():
    """Thread function to track pump duration."""
    global pump_running, pump_start_time, pump_duration
    
    while True:
        with pump_lock:
            if pump_running and pump_start_time:
                pump_duration = int(time.time() - pump_start_time)
        
        time.sleep(1)  # Update every second

def get_pump_duration():
    """Get the current pump running duration in seconds."""
    global pump_running, pump_start_time, pump_duration
    
    with pump_lock:
        if not pump_running or not pump_start_time:
            return pump_duration
        
        # Calculate current duration based on start time
        if isinstance(pump_start_time, datetime):
            # If it's a datetime object
            current_duration = int((datetime.now() - pump_start_time).total_seconds())
        else:
            # If it's a float timestamp
            current_duration = int(time.time() - pump_start_time)
        
        return current_duration

def log_pump_action(action):
    """Log pump actions to the database."""
    log = PumpLog(
        action=action,
        timestamp=datetime.now()
    )
    db.session.add(log)
    db.session.commit()

def get_all_presets():
    """Get all irrigation presets."""
    presets = IrrigationPreset.query.all()
    return [preset.to_dict() for preset in presets]

def create_preset(data):
    """Create a new irrigation preset."""
    if 'name' not in data:
        return {"status": "error", "message": "Preset name is required"}
    
    preset = IrrigationPreset(
        name=data['name'],
        duration=data.get('duration', 300),  # Default 5 minutes
        water_level=data.get('water_level', 50),  # Default 50%
        active=False
    )
    
    db.session.add(preset)
    db.session.commit()
    
    return {"status": "success", "message": f"Preset '{data['name']}' created", "preset": preset.to_dict()}

def delete_preset(preset_id):
    """Delete a preset."""
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return {"status": "error", "message": "Preset not found"}
    
    preset_name = preset.name
    db.session.delete(preset)
    db.session.commit()
    
    return {"status": "success", "message": f"Preset '{preset_name}' deleted"}

def activate_preset(preset_id):
    """Activate a specific preset."""
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return {"status": "error", "message": "Preset not found"}
    
    # Deactivate all other presets
    IrrigationPreset.query.update({"active": False})
    
    # Activate this preset
    preset.active = True
    db.session.commit()
    
    # Apply the preset settings (start pump if needed)
    if preset.auto_start:
        start_pump()
    
    return {"status": "success", "message": f"Preset '{preset.name}' activated", "name": preset.name}

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

def add_schedule(preset_id, data):
    """Add a new schedule to a preset."""
    from .models import Preset, Schedule
    from shared.config import db
    
    # Get the preset
    preset = Preset.query.get_or_404(preset_id)
    
    # Create a new schedule
    schedule = Schedule(
        preset_id=preset_id,
        start_time=data['start_time'],
        duration=data['duration'],
        active=True
    )
    
    # Add to database
    db.session.add(schedule)
    db.session.commit()
    
    # Return the schedule data
    return schedule.to_dict()

# Alias for backward compatibility
create_schedule = add_schedule

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

# Global variable to track pump status
pump_running = False
pump_start_time = None

def start_pump():
    """Start the irrigation pump."""
    global pump_running, pump_start_time
    
    # Only start if not already running
    if not pump_running:
        pump_running = True
        pump_start_time = datetime.now()
        
        # Logic to start the pump would go here
        # For now, just log the event and notify clients
        log = IrrigationLog(pump_status=True, water_level=get_water_level())
        db.session.add(log)
        db.session.commit()
        
        # Emit event with additional data for better client handling
        socketio.emit('pump_status', {
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'water_level': get_water_level()
        })
        return {'status': 'success', 'message': 'Pump started'}
    
    return {'status': 'warning', 'message': 'Pump already running'}

def stop_pump():
    """Stop the irrigation pump."""
    global pump_running, pump_start_time
    
    # Only stop if currently running
    if pump_running:
        pump_running = False
        
        # Calculate duration if we have a start time
        duration = None
        if pump_start_time:
            duration = (datetime.now() - pump_start_time).total_seconds()
            pump_start_time = None
        
        # Logic to stop the pump would go here
        # For now, just log the event and notify clients
        log = IrrigationLog(
            pump_status=False, 
            water_level=get_water_level(),
            duration=duration
        )
        db.session.add(log)
        db.session.commit()
        
        socketio.emit('pump_status', {'status': 'stopped'})
        return {'status': 'success', 'message': 'Pump stopped'}
    
    return {'status': 'warning', 'message': 'Pump already stopped'}

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