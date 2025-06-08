import time
import threading
import logging
from datetime import datetime, time as time_obj
from flask import current_app
from shared.database import db
from shared.socketio import socketio
from .models import Preset, Schedule, IrrigationLog

# Setup logging
logger = logging.getLogger(__name__)

# --- Hardware Initialization ---
try:
    from hardware.pump import Pump
    pump = Pump()
except Exception as e:
    logger.error(f"Could not import hardware pump: {e}. Running in simulated mode.")
    class DummyPump:
        def start(self):
            logger.warning("Running in dummy mode. Pump not started.")
            return True
        def stop(self):
            logger.warning("Running in dummy mode. Pump not stopped.")
            return True
    pump = DummyPump()

# In-memory state for pump and scheduler
pump_running = False
pump_start_time = None
pump_lock = threading.Lock()
scheduler_thread = None
scheduler_running = False

# --- Pump Control ---

def get_pump_duration():
    """Calculates how long the pump has been running."""
    if pump_running and pump_start_time:
        return time.time() - pump_start_time
    return 0

def get_pump_status():
    """Returns the current status of the pump."""
    with pump_lock:
        return {
            "running": pump_running,
            "duration": get_pump_duration()
        }

def start_pump(duration_seconds=None):
    """Manually starts the pump, optionally for a specific duration."""
    global pump_running, pump_start_time
    with pump_lock:
        if pump_running:
            return {"status": "warning", "message": "Pump is already running."}
        
        logger.info("Starting pump manually.")
        pump.start()
        pump_running = True
        pump_start_time = time.time()
        
        # If a duration is specified, schedule a stop
        if duration_seconds:
            def stop_after_duration():
                time.sleep(duration_seconds)
                stop_pump()
            
            duration_thread = threading.Thread(target=stop_after_duration)
            duration_thread.daemon = True
            duration_thread.start()
            
        return {"status": "success", "message": f"Pump started for {duration_seconds}s." if duration_seconds else "Pump started."}

def stop_pump():
    """Manually stops the pump."""
    global pump_running, pump_start_time
    with pump_lock:
        if not pump_running:
            return {"status": "warning", "message": "Pump is not running."}
        
        duration = get_pump_duration()
        logger.info(f"Stopping pump manually after {duration:.2f} seconds.")
        pump.stop()
        pump_running = False
        pump_start_time = None
        
        # Log the manual run
        log_irrigation_run(None, duration)
        
        return {"status": "success", "message": "Pump stopped.", "duration": duration}

# --- Preset and Schedule Management ---

def get_all_presets():
    """Returns all presets with their schedules."""
    return [p.to_dict(include_schedules=True) for p in Preset.query.all()]

def create_preset(data):
    """Creates a new preset."""
    new_preset = Preset(name=data['name'], description=data.get('description'))
    db.session.add(new_preset)
    db.session.commit()
    logger.info(f"Created new preset: {new_preset.name}")
    return new_preset.to_dict()

def update_preset(preset_id, data):
    """Updates an existing preset."""
    preset = Preset.query.get(preset_id)
    if not preset:
        return None
    preset.name = data['name']
    preset.description = data.get('description')
    db.session.commit()
    logger.info(f"Updated preset {preset_id}: {preset.name}")
    return preset.to_dict()

def delete_preset(preset_id):
    """Deletes a preset."""
    preset = Preset.query.get(preset_id)
    if not preset:
        return False
    db.session.delete(preset)
    db.session.commit()
    logger.info(f"Deleted preset {preset_id}")
    return True

def activate_preset(preset_id):
    """Activates a preset and deactivates all others."""
    with pump_lock:
        # Deactivate all other presets
        Preset.query.filter(Preset.id != preset_id).update({'is_active': False})
        # Activate the target preset
        target_preset = Preset.query.get(preset_id)
        if not target_preset:
            return None
        target_preset.is_active = True
        db.session.commit()
    logger.info(f"Activated preset: {target_preset.name}")
    return target_preset.to_dict(include_schedules=True)

def add_schedule_to_preset(preset_id, data):
    """Adds a new schedule to a preset."""
    preset = Preset.query.get(preset_id)
    if not preset:
        return None
    
    new_schedule = Schedule(
        preset_id=preset_id,
        day_of_week=data['day_of_week'],
        start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
        duration_seconds=data['duration_seconds']
    )
    db.session.add(new_schedule)
    db.session.commit()
    logger.info(f"Added new schedule to preset {preset.name}")
    return new_schedule.to_dict()

def delete_schedule(schedule_id):
    """Deletes a schedule."""
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return False
    db.session.delete(schedule)
    db.session.commit()
    logger.info(f"Deleted schedule {schedule_id}")
    return True

# --- Scheduler Logic ---

def scheduler_loop():
    """The main loop for the irrigation scheduler."""
    global scheduler_running
    logger.info("Irrigation scheduler started.")
    while scheduler_running:
        try:
            with current_app.app_context():
                check_schedules()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
        # Check every 60 seconds
        time.sleep(60)
    logger.info("Irrigation scheduler stopped.")

def check_schedules():
    """Checks the active schedule and triggers the pump if needed."""
    with pump_lock:
        if pump_running:
            logger.debug("Scheduler check skipped: pump is already running manually.")
            return

        active_preset = Preset.query.filter_by(is_active=True).first()
        if not active_preset:
            logger.debug("Scheduler check skipped: no active preset.")
            return

        now = datetime.now()
        today_str = now.strftime('%A') # e.g., "Monday"
        
        schedules_today = active_preset.schedules.filter_by(
            day_of_week=today_str, 
            is_active=True
        ).all()

        for schedule in schedules_today:
            # Check if current time is within one minute of the scheduled start time
            if schedule.start_time.hour == now.hour and schedule.start_time.minute == now.minute:
                logger.info(f"Scheduler: Triggering pump for preset '{active_preset.name}' based on schedule.")
                start_pump(duration_seconds=schedule.duration_seconds)
                log_irrigation_run(active_preset.id, schedule.duration_seconds)
                break # Avoid running multiple schedules in the same minute

def log_irrigation_run(preset_id, duration):
    """Logs an irrigation event to the database."""
    log_entry = IrrigationLog(
        preset_id=preset_id,
        duration=duration,
        pump_status=True
    )
    db.session.add(log_entry)
    db.session.commit()
    logger.info(f"Logged irrigation run. Preset ID: {preset_id}, Duration: {duration:.2f}s")


def init_scheduler(app):
    """Initializes and starts the scheduler thread."""
    global scheduler_thread, scheduler_running
    if not scheduler_thread:
        with app.app_context():
            scheduler_running = True
            scheduler_thread = threading.Thread(target=scheduler_loop)
            scheduler_thread.daemon = True
            scheduler_thread.start()
    logger.info("Irrigation scheduler initialized.")

def shutdown_scheduler():
    """Stops the scheduler thread."""
    global scheduler_running
    if scheduler_thread:
        scheduler_running = False
        scheduler_thread.join(timeout=1)
    logger.info("Irrigation scheduler shut down.")