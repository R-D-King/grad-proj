from flask_socketio import SocketIO
from datetime import datetime
from smart_irrigation.models import IrrigationPreset, IrrigationSchedule, IrrigationData
from shared.config import db
from flask import current_app

# Global variables
pump_status = {'status': False}
water_level = {'level': 75}
pump_start_time = None
running_preset_id = None
running_schedule_id = None
weather_data = {
    'temperature': 25,
    'humidity': 60,
    'soil_moisture': 45,
    'wind_speed': 10,
    'pressure': 1013
}

# Initialize socketio instance
socketio = SocketIO()
flask_app = None

# Track which schedules have already run today
schedules_run_today = set()

# Add a global variable to track if the schedule checker is running
schedule_checker_running = False

@socketio.on('connect')
def handle_connect():
    """Handle client connection and start schedule checker"""
    global schedule_checker_running
    
    print("Client connected")
    
    # Start background task to check schedules if not already running
    if not schedule_checker_running:
        print("Starting schedule checker")
        schedule_checker_running = True
        
        def schedule_checker():
            while True:
                print(f"Checking schedules at {datetime.now().strftime('%H:%M:%S')}")
                check_schedules()
                socketio.sleep(10)  # Check every 10 seconds
        
        socketio.start_background_task(schedule_checker)
    
    # Send initial data including running preset
    socketio.emit('weather_data', weather_data)
    socketio.emit('pump_status', pump_status)
    socketio.emit('water_level', water_level)
    
    # Send running preset info
    preset_name = None
    if running_preset_id is not None:
        with flask_app.app_context():
            preset = IrrigationPreset.query.get(running_preset_id)
            if preset:
                preset_name = preset.name
    
    socketio.emit('running_preset', {
        'id': running_preset_id, 
        'name': preset_name if preset_name else 'Manual Control' if pump_status['status'] else None
    })

@socketio.on('start_pump')
def handle_start_pump():
    global pump_status, pump_start_time, running_preset_id
    pump_status['status'] = True
    pump_start_time = datetime.now()
    running_preset_id = None  # Manual start, no preset
    socketio.emit('pump_status', pump_status)
    socketio.emit('running_preset', {'id': None, 'name': 'Manual Control'})
    
    # Log pump start in database using SQLAlchemy
    with flask_app.app_context():
        irrigation_data = IrrigationData(
            pump_status=True,
            water_level=water_level['level'],
            pump_duration=0
        )
        db.session.add(irrigation_data)
        db.session.commit()

@socketio.on('stop_pump')
def handle_stop_pump():
    global pump_status, pump_start_time, running_preset_id, running_schedule_id
    pump_status['status'] = False
    
    # Calculate duration if pump was started
    duration = 0
    if pump_start_time:
        duration = int((datetime.now() - pump_start_time).total_seconds())
        pump_start_time = None
    
    # Reset running preset
    running_preset_id = None
    running_schedule_id = None
    socketio.emit('pump_status', pump_status)
    socketio.emit('running_preset', {'id': None, 'name': None})
    
    # Log pump stop in database with duration using SQLAlchemy
    with flask_app.app_context():
        irrigation_data = IrrigationData(
            pump_status=False,
            water_level=water_level['level'],
            pump_duration=duration
        )
        db.session.add(irrigation_data)
        db.session.commit()

# Function to check schedules and run pump
def check_schedules():
    """Check if any scheduled irrigation should start"""
    global pump_status, pump_start_time, running_preset_id, running_schedule_id, schedules_run_today
    
    # Don't interfere if pump is already running
    if pump_status['status']:
        return
        
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    
    # Reset schedules_run_today at midnight
    if current_time == "00:00":
        schedules_run_today.clear()
        print("Cleared schedules_run_today at midnight")
    
    with flask_app.app_context():
        # Get active preset
        active_preset = IrrigationPreset.query.filter_by(active=True).first()
        if not active_preset:
            return
        
        # Check schedules for active preset
        for schedule in active_preset.schedules:
            if not schedule.active:
                continue
                
            schedule_time = schedule.start_time.strftime("%H:%M")
            schedule_id = schedule.id
            
            # Create a unique key for this schedule run
            schedule_run_key = f"{schedule_id}_{current_date}_{schedule_time}"
            
            # Check if it's time to run this schedule and it hasn't run yet today at this time
            if schedule_time == current_time and schedule_run_key not in schedules_run_today:
                print(f"Starting scheduled irrigation for preset {active_preset.name} at {current_time}")
                
                # Mark this schedule as run today at this time
                schedules_run_today.add(schedule_run_key)
                
                # Start pump
                pump_status['status'] = True
                pump_start_time = datetime.now()
                running_preset_id = active_preset.id
                running_schedule_id = schedule.id
                
                socketio.emit('pump_status', pump_status)
                socketio.emit('running_preset', {'id': active_preset.id, 'name': active_preset.name})
                
                # Log pump start in database
                irrigation_data = IrrigationData(
                    pump_status=True,
                    water_level=water_level['level'],
                    pump_duration=0
                )
                db.session.add(irrigation_data)
                db.session.commit()
                
                # Schedule pump stop after duration
                def stop_pump_after_duration():
                    global pump_status, pump_start_time, running_preset_id, running_schedule_id
                    
                    print(f"Stopping scheduled irrigation after {schedule.duration} seconds")
                    pump_status['status'] = False
                    
                    # Calculate actual duration
                    actual_duration = float(schedule.duration)
                    if pump_start_time:
                        actual_duration = (datetime.now() - pump_start_time).total_seconds()
                        pump_start_time = None
                    
                    running_preset_id = None
                    running_schedule_id = None
                    
                    socketio.emit('pump_status', pump_status)
                    socketio.emit('running_preset', {'id': None, 'name': None})
                    
                    with flask_app.app_context():
                        # Log in database with actual duration
                        irrigation_data = IrrigationData(
                            pump_status=False,
                            water_level=water_level['level'],
                            pump_duration=actual_duration
                        )
                        db.session.add(irrigation_data)
                        db.session.commit()
                        
                        # Emit schedule update
                        socketio.emit('schedule_updated', {
                            'id': schedule.id,
                            'start_time': schedule.start_time.strftime('%H:%M'),
                            'duration': schedule.duration,
                            'active': schedule.active,
                            'preset_id': active_preset.id,
                            'running': False
                        })
                
                # Schedule the stop function
                duration = int(schedule.duration)
                socketio.start_background_task(lambda: socketio.sleep(duration) or stop_pump_after_duration())
                
                # Emit schedule update
                socketio.emit('schedule_updated', {
                    'id': schedule.id,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'duration': schedule.duration,
                    'active': schedule.active,
                    'preset_id': active_preset.id,
                    'running': True
                })
                
                # Only run one schedule at a time
                break

def init_app(app):
    """Initialize socketio with the Flask app"""
    global flask_app
    flask_app = app
    socketio.init_app(app)
    return socketio