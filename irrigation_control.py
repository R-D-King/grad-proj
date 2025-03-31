from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from smart_irrigation.models import IrrigationPreset, IrrigationSchedule, IrrigationData
from shared.config import db
from socket_handlers import socketio, pump_status, water_level, pump_start_time, running_preset_id, running_schedule_id

irrigation_bp = Blueprint('irrigation', __name__)
flask_app = None

def init_app(app):
    """Store the Flask app instance for later use"""
    global flask_app
    flask_app = app
    return irrigation_bp

@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_preset(preset_id):
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

@irrigation_bp.route('/api/irrigation/preset', methods=['POST'])
def create_preset():
    data = request.json
    
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

@irrigation_bp.route('/api/irrigation/schedule', methods=['POST'])
def create_schedule():
    data = request.json
    preset_id = data['preset_id']
    
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

@irrigation_bp.route('/api/irrigation/schedule/<int:schedule_id>', methods=['PUT', 'DELETE'])
def manage_schedule(schedule_id):
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

@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>/run', methods=['POST'])
def run_preset(preset_id):
    global pump_status, pump_start_time, running_preset_id, running_schedule_id
    
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
        from socket_handlers import handle_stop_pump
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
        
        with current_app.app_context():
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

@irrigation_bp.route('/api/irrigation/manual', methods=['POST'])
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
        irrigation_data = IrrigationData(
            pump_status=False,
            water_level=water_level['level'],
            pump_duration=duration
        )
        db.session.add(irrigation_data)
        db.session.commit()
    
    return jsonify({'status': pump_status['status']})


@irrigation_bp.route('/api/irrigation/presets', methods=['GET'])
def get_presets():
    """Get all irrigation presets"""
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


@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>/activate', methods=['POST'])
def activate_preset(preset_id):
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