from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
import json
import os
import sqlite3
import csv
import io
from datetime import datetime, timedelta
from smart_irrigation.models import IrrigationPreset, IrrigationSchedule, IrrigationData, WeatherData
from shared.config import db
from time_utils import time_utils

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key'
# Use the config from shared.config
app.config.from_object('shared.config.Config')

# Ensure instance directory exists
instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app)

# Add a route to get server time
@app.route('/api/server-time')
def get_server_time():
    """Return the current server time"""
    now = datetime.now()
    return jsonify({
        'timestamp': now.timestamp(),
        'formatted': now.strftime('%Y-%m-%d %H:%M:%S'),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S')
    })

# Add these new routes for server time functionality

@app.route('/api/server-time/formatted')
def get_formatted_server_time():
    """Return formatted server time"""
    now = datetime.now()
    return jsonify({
        'formatted_time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%Y-%m-%d')
    })

app.register_blueprint(time_utils)

@app.route('/api/schedule/<int:schedule_id>/should-run')
def should_schedule_run(schedule_id):
    """Check if a schedule should run based on current server time"""
    from time_utils import is_time_to_run_schedule
    
    with app.app_context():
        schedule = IrrigationSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'should_run': False})
        
        should_run = is_time_to_run_schedule(schedule)
        return jsonify({'should_run': should_run})

# Create database tables using SQLAlchemy
with app.app_context():
    db.create_all()

# Sample data for testing
weather_data = {
    'temperature': 25,
    'humidity': 60,
    'soil_moisture': 45,
    'wind_speed': 10,
    'pressure': 1013
}

pump_status = {
    'status': False
}

water_level = {
    'level': 75
}

# Helper function to convert row to dict
def dict_factory(cursor, row):
    """Convert database row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

# API Routes for Irrigation System
@app.route('/api/irrigation/presets', methods=['GET'])
def get_presets():
    """Get all irrigation presets"""
    with app.app_context():
        presets = IrrigationPreset.query.all()
        result = []
        
        for preset in presets:
            preset_data = {
                'id': preset.id,
                'name': preset.name,
                'active': preset.active,
                'schedules': []
            }
            
            # Get schedules ordered by start_time
            for schedule in sorted(preset.schedules, key=lambda s: s.start_time):
                schedule_data = {
                    'id': schedule.id,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'duration': schedule.duration,
                    'active': schedule.active,
                    'preset_id': preset.id,
                    'running': False  # Default to not running
                }
                preset_data['schedules'].append(schedule_data)
            
            result.append(preset_data)
        
        return jsonify(result)

@app.route('/api/irrigation/preset', methods=['POST'])
def create_preset():
    data = request.json
    
    with app.app_context():
        # Create new preset
        preset = IrrigationPreset(
            name=data['name'],
            active=False
        )
        
        db.session.add(preset)
        db.session.commit()
        
        # Prepare response
        preset_data = {
            'id': preset.id,
            'name': preset.name,
            'active': preset.active,
            'schedules': []
        }
        
        socketio.emit('preset_updated', preset_data)
        return jsonify(preset_data)

@app.route('/api/irrigation/preset/<int:preset_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_preset(preset_id):
    with app.app_context():
        preset = IrrigationPreset.query.get(preset_id)
        
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        if request.method == 'GET':
            preset_data = {
                'id': preset.id,
                'name': preset.name,
                'active': preset.active,
                'schedules': []
            }
            
            # Get schedules ordered by start_time
            for schedule in sorted(preset.schedules, key=lambda s: s.start_time):
                schedule_data = {
                    'id': schedule.id,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'duration': schedule.duration,
                    'active': schedule.active,
                    'preset_id': preset.id,
                    'running': False  # Default to not running
                }
                preset_data['schedules'].append(schedule_data)
            
            return jsonify(preset_data)
            
        elif request.method == 'PUT':
            data = request.json
            preset.name = data['name']
            db.session.commit()
            
            preset_data = {
                'id': preset.id,
                'name': preset.name,
                'active': preset.active,
                'schedules': []
            }
            
            # Get schedules
            for schedule in sorted(preset.schedules, key=lambda s: s.start_time):
                schedule_data = {
                    'id': schedule.id,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'duration': schedule.duration,
                    'active': schedule.active,
                    'preset_id': preset.id,
                    'running': False
                }
                preset_data['schedules'].append(schedule_data)
            
            socketio.emit('preset_updated', preset_data)
            return jsonify(preset_data)
            
        elif request.method == 'DELETE':
            db.session.delete(preset)
            db.session.commit()
            
            socketio.emit('preset_deleted', {'id': preset_id})
            return jsonify({'success': True})

@app.route('/api/irrigation/preset/<int:preset_id>/activate', methods=['POST'])
def activate_preset(preset_id):
    with app.app_context():
        # Deactivate all presets
        IrrigationPreset.query.update({'active': False})
        
        # Activate the selected preset
        preset = IrrigationPreset.query.get(preset_id)
        if preset:
            preset.active = True
            db.session.commit()
            
            socketio.emit('preset_activated', {'id': preset_id})
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Preset not found'}), 404

@app.route('/api/irrigation/schedule', methods=['POST'])
def create_schedule():
    data = request.json
    preset_id = data['preset_id']
    
    with app.app_context():
        # Check if preset exists
        preset = IrrigationPreset.query.get(preset_id)
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        # Parse time string to Time object
        time_parts = data['start_time'].split(':')
        start_time = datetime.now().replace(
            hour=int(time_parts[0]), 
            minute=int(time_parts[1]), 
            second=0, 
            microsecond=0
        ).time()
        
        # Create new schedule
        schedule = IrrigationSchedule(
            start_time=start_time,
            duration=float(data['duration']),
            active=True,
            preset_id=preset_id
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        # Prepare response
        schedule_data = {
            'id': schedule.id,
            'start_time': schedule.start_time.strftime('%H:%M'),
            'duration': schedule.duration,
            'active': schedule.active,
            'preset_id': preset_id,
            'running': False
        }
        
        socketio.emit('schedule_updated', schedule_data)
        return jsonify(schedule_data)

@app.route('/api/irrigation/schedule/<int:schedule_id>', methods=['PUT', 'DELETE'])
def manage_schedule(schedule_id):
    with app.app_context():
        schedule = IrrigationSchedule.query.get(schedule_id)
        
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404
        
        preset_id = schedule.preset_id
        
        if request.method == 'PUT':
            data = request.json
            
            # Parse time string to Time object if provided
            if 'start_time' in data:
                time_parts = data['start_time'].split(':')
                start_time = datetime.now().replace(
                    hour=int(time_parts[0]), 
                    minute=int(time_parts[1]), 
                    second=0, 
                    microsecond=0
                ).time()
                schedule.start_time = start_time
            
            if 'duration' in data:
                schedule.duration = float(data['duration'])
                
            if 'active' in data:
                schedule.active = data['active']
            
            db.session.commit()
            
            # Prepare response
            schedule_data = {
                'id': schedule.id,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'duration': schedule.duration,
                'active': schedule.active,
                'preset_id': preset_id,
                'running': False  # Reset running state on update
            }
            
            socketio.emit('schedule_updated', schedule_data)
            return jsonify(schedule_data)
            
        elif request.method == 'DELETE':
            db.session.delete(schedule)
            db.session.commit()
            
            socketio.emit('schedule_deleted', {'id': schedule_id, 'preset_id': preset_id})
            return jsonify({'success': True})

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection and start schedule checker"""
    # Start background task to check schedules
    def schedule_checker():
        while True:
            check_schedules()
            socketio.sleep(60)  # Check every minute
    
    socketio.start_background_task(schedule_checker)
    
    # Send initial data including running preset
    socketio.emit('weather_data', weather_data)
    socketio.emit('pump_status', pump_status)
    socketio.emit('water_level', water_level)
    
    # Send running preset info
    preset_name = None
    if running_preset_id is not None:
        with app.app_context():
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
    with app.app_context():
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
    with app.app_context():
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
    global pump_status, pump_start_time, running_preset_id, running_schedule_id
    
    if pump_status['status'] and running_preset_id is None:
        return  # Don't interfere if pump is manually running
        
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    with app.app_context():
        # Get active preset
        active_preset = IrrigationPreset.query.filter_by(active=True).first()
        if not active_preset:
            return
        
        # Check schedules for active preset
        for schedule in active_preset.schedules:
            schedule_time = schedule.start_time.strftime("%H:%M")
            
            # Check if it's time to run this schedule
            if schedule_time == current_time and schedule.active:
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
                    
                    with app.app_context():
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

# Start background task to check schedules
# Add these global variables at the top of your file, after initializing pump_status
pump_start_time = None
running_preset_id = None
running_schedule_id = None

@socketio.on('connect')
def start_schedule_checker(auth=None):  # Add auth parameter with default value
    def schedule_checker():
        while True:
            check_schedules()
            socketio.sleep(60)  # Check every minute
    
    socketio.start_background_task(schedule_checker)
    
    # Send initial data including running preset
    socketio.emit('weather_data', weather_data)
    socketio.emit('pump_status', pump_status)
    socketio.emit('water_level', water_level)
    
    # Send running preset info
    preset_name = None
    if running_preset_id is not None:
        with app.app_context():
            preset = IrrigationPreset.query.get(running_preset_id)
            if preset:
                preset_name = preset.name
    
    socketio.emit('running_preset', {
        'id': running_preset_id, 
        'name': preset_name if preset_name else 'Manual Control' if pump_status['status'] else None
    })

# Reports API
@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    data = request.json
    report_type = data['report_type']
    
    # Use provided dates or default to last 7 days
    if data.get('start_date') and data.get('end_date'):
        start_date = data['start_date']
        end_date = data['end_date']
    else:
        # Default to last 7 days
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    with app.app_context():
        if report_type == 'weather':
            # Use SQLAlchemy to query weather data
            from smart_irrigation.models import WeatherData
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
            
            report_data = WeatherData.query.filter(
                WeatherData.timestamp.between(start_datetime, end_datetime)
            ).order_by(WeatherData.timestamp).all()
            
            # Convert to dict for JSON serialization
            report_data = [{
                'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': item.temperature,
                'humidity': item.humidity,
                'soil_moisture': item.soil_moisture,
                'wind_speed': item.wind_speed,
                'pressure': item.pressure
            } for item in report_data]
        else:
            # Use SQLAlchemy to query irrigation data
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
            
            report_data = IrrigationData.query.filter(
                IrrigationData.timestamp.between(start_datetime, end_datetime)
            ).order_by(IrrigationData.timestamp).all()
            
            # Convert to dict for JSON serialization
            report_data = [{
                'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'pump_status': item.pump_status,
                'water_level': item.water_level,
                'duration': item.pump_duration
            } for item in report_data]
    
    # If no data in database yet, return empty array instead of sample data
    if not report_data:
        # Commented out sample data generation
        """
        # Generate sample data
        sample_data = []
        for i in range(10):
            timestamp = f"2025-03-{20+i} 12:00:00"
            if report_type == 'weather':
                sample_data.append({
                    'timestamp': timestamp,
                    'temperature': 20 + i,
                    'humidity': 50 + i,
                    'soil_moisture': 40 + i,
                    'wind_speed': 5 + (i % 5),
                    'pressure': 1010 + i
                })
            else:
                sample_data.append({
                    'timestamp': timestamp,
                    'pump_status': i % 2 == 0,
                    'water_level': 70 + (i % 20),
                    'duration': 60 + (i * 10)
                })
        return jsonify(sample_data)
        """
        # Return empty array when no data is available
        return jsonify([])
    
    return jsonify(report_data)

@app.route('/api/reports/download')
def download_report():
    """Generate and download a CSV report"""
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    options = json.loads(request.args.get('options'))
    
    # Use provided dates or default to last 7 days
    if not start_date or not end_date:
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    with app.app_context():
        if report_type == 'weather':
            # Use SQLAlchemy to query weather data
            from smart_irrigation.models import WeatherData
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
            
            query_data = WeatherData.query.filter(
                WeatherData.timestamp.between(start_datetime, end_datetime)
            ).order_by(WeatherData.timestamp).all()
            
            # Convert to dict for processing
            report_data = [{
                'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': item.temperature,
                'humidity': item.humidity,
                'soil_moisture': item.soil_moisture,
                'wind_speed': item.wind_speed,
                'pressure': item.pressure
            } for item in query_data]
        else:
            # Use SQLAlchemy to query irrigation data
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
            
            query_data = IrrigationData.query.filter(
                IrrigationData.timestamp.between(start_datetime, end_datetime)
            ).order_by(IrrigationData.timestamp).all()
            
            # Convert to dict for processing
            report_data = [{
                'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'pump_status': item.pump_status,
                'water_level': item.water_level,
                'duration': item.pump_duration
            } for item in query_data]
    
    # If no data, return a special response that will trigger a popup instead of an error page
    if not report_data:
        return jsonify({
            'status': 'no_data',
            'message': 'No data available for the selected period. Please try a different date range.'
        }), 200  # Return 200 OK status instead of 404
    
    # Create CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['Date/Time']
    if report_type == 'weather':
        if options.get('temperature'): headers.append('Temperature (°C)')
        if options.get('humidity'): headers.append('Humidity (%)')
        if options.get('soil_moisture'): headers.append('Soil Moisture (%)')
        if options.get('wind_speed'): headers.append('Wind Speed (km/h)')
        if options.get('pressure'): headers.append('Pressure (hPa)')
    else:
        if options.get('pump_status'): headers.append('Pump Status')
        if options.get('water_level'): headers.append('Water Level (%)')
        if options.get('duration'): headers.append('Duration (s)')
    
    writer.writerow(headers)
    
    # Write data
    for item in report_data:
        row = [item['timestamp']]
        if report_type == 'weather':
            if options.get('temperature'): row.append(item['temperature'])
            if options.get('humidity'): row.append(item['humidity'])
            if options.get('soil_moisture'): row.append(item['soil_moisture'])
            if options.get('wind_speed'): row.append(item['wind_speed'])
            if options.get('pressure'): row.append(item['pressure'])
        else:
            if options.get('pump_status'): row.append('Running' if item['pump_status'] else 'Stopped')
            if options.get('water_level'): row.append(item['water_level'])
            if options.get('duration'): row.append(item['duration'])
        
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{report_type}_report_{start_date}_to_{end_date}.csv'
    )

@app.route('/api/irrigation/preset/<int:preset_id>/run', methods=['POST'])
def run_preset(preset_id):
    global pump_status, pump_start_time, running_preset_id, running_schedule_id
    
    with app.app_context():
        # Check if preset exists
        preset = IrrigationPreset.query.get(preset_id)
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        # Get the first active schedule for this preset
        schedule = IrrigationSchedule.query.filter_by(
            preset_id=preset_id, 
            active=True
        ).order_by(IrrigationSchedule.start_time).first()
        
        if not schedule:
            return jsonify({'error': 'No active schedules found for this preset'}), 400
        
        # Stop any running pump
        if pump_status['status']:
            handle_stop_pump()
        
        # Start pump with this preset
        pump_status['status'] = True
        pump_start_time = datetime.now()
        running_preset_id = preset_id
        running_schedule_id = schedule.id
        
        socketio.emit('pump_status', pump_status)
        socketio.emit('running_preset', {'id': preset_id, 'name': preset.name})
        
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
            
            with app.app_context():
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
                    'preset_id': preset_id,
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
            'preset_id': preset_id,
            'running': True
        })
        
        return jsonify({'success': True, 'preset_id': preset_id, 'duration': duration})

# Add this route after the run_preset route
@app.route('/api/irrigation/manual', methods=['POST'])
def manual_control():
    global pump_status, pump_start_time, running_preset_id, running_schedule_id
    
    data = request.json
    new_status = data.get('status', False)
    
    # If turning on
    if new_status and not pump_status['status']:
        pump_status['status'] = True
        pump_start_time = datetime.now()
        running_preset_id = None  # Manual control
        running_schedule_id = None
        
        socketio.emit('pump_status', pump_status)
        socketio.emit('running_preset', {'id': None, 'name': 'Manual Control'})
        
        # Log pump start in database
        with app.app_context():
            irrigation_data = IrrigationData(
                pump_status=True,
                water_level=water_level['level'],
                pump_duration=0
            )
            db.session.add(irrigation_data)
            db.session.commit()
            
    # If turning off
    elif not new_status and pump_status['status']:
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
        
        # Log pump stop in database with duration
        with app.app_context():
            irrigation_data = IrrigationData(
                pump_status=False,
                water_level=water_level['level'],
                pump_duration=duration
            )
            db.session.add(irrigation_data)
            db.session.commit()
    
    return jsonify({'status': pump_status['status']})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')