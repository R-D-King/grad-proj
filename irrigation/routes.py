from flask import Blueprint, jsonify, request, session
from datetime import datetime
# Import the controller functions properly
from .controllers import (
    get_all_presets, get_preset_details, create_preset, 
    activate_preset, delete_preset, create_schedule, 
    update_schedule, delete_schedule, start_pump, stop_pump,
    log_irrigation_event, get_water_level, check_schedule_time
)

irrigation_bp = Blueprint('irrigation', __name__)

@irrigation_bp.route('/api/irrigation/presets', methods=['GET'])
def presets():
    """Get all irrigation presets."""
    return jsonify(get_all_presets())

@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>', methods=['GET'])
def preset_details(preset_id):
    """Get details for a specific preset."""
    return jsonify(get_preset_details(preset_id))

@irrigation_bp.route('/api/irrigation/preset', methods=['POST'])
def create_new_preset():
    """Create a new irrigation preset."""
    data = request.json
    return jsonify(create_preset(data))

@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>/activate', methods=['POST'])
def activate_preset_route(preset_id):
    """Activate a specific preset."""
    return jsonify(activate_preset(preset_id))

@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>', methods=['DELETE'])
def delete_preset_route(preset_id):
    """Delete a preset."""
    return jsonify(delete_preset(preset_id))

@irrigation_bp.route('/api/irrigation/schedule', methods=['POST'])
def create_new_schedule():
    """Create a new schedule."""
    data = request.json
    return jsonify(create_schedule(data))

@irrigation_bp.route('/api/irrigation/schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule_route(schedule_id):
    """Update an existing schedule."""
    data = request.json
    return jsonify(update_schedule(schedule_id, data))

@irrigation_bp.route('/api/irrigation/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule_route(schedule_id):
    """Delete a schedule."""
    return jsonify(delete_schedule(schedule_id))

@irrigation_bp.route('/api/irrigation/pump/start', methods=['POST'])
def start_pump_route():
    """API endpoint to start the irrigation pump."""
    return jsonify(start_pump())

@irrigation_bp.route('/api/irrigation/pump/stop', methods=['POST'])
def stop_pump_route():
    """API endpoint to stop the irrigation pump."""
    return jsonify(stop_pump())

@irrigation_bp.route('/api/schedule/<int:schedule_id>/should-run', methods=['GET'])
def check_schedule_time_route(schedule_id):
    """Check if a schedule should run based on current time."""
    return jsonify(check_schedule_time(schedule_id))


@irrigation_bp.route('/api/irrigation/manual', methods=['POST'])
def manual_irrigation():
    """API endpoint to manually control irrigation."""
    data = request.json
    
    # Start irrigation
    if data.get('action') == 'start':
        # Store the start time in the session
        session['irrigation_start_time'] = datetime.now().timestamp()
        session['preset_id'] = data.get('preset_id')
        session.modified = True  # Ensure session is saved
        
        print(f"Starting irrigation with preset_id: {data.get('preset_id')}")  # Debug print
        print(f"Start time saved in session: {session.get('irrigation_start_time')}")  # Debug print
        
        # Start the pump - this will create a log entry for pump start
        start_pump()
        
        return jsonify({
            'status': 'success',
            'message': 'Irrigation started'
        })
    
    # Stop irrigation
    elif data.get('action') == 'stop':
        # Calculate the actual duration if we have a start time
        calculated_duration = 0
        if 'irrigation_start_time' in session:
            start_time = session.get('irrigation_start_time')
            calculated_duration = datetime.now().timestamp() - start_time
            print(f"Calculated duration: {calculated_duration} seconds")  # Debug print
        else:
            print("No start time in session")  # Debug print
        
        # Use the calculated duration or the provided elapsed_time
        final_duration = data.get('elapsed_time')
        if final_duration is None:
            final_duration = calculated_duration
        
        print(f"Final duration to log: {final_duration}")  # Debug print
        
        # Get preset_id from session or request
        preset_id = session.get('preset_id') or data.get('preset_id')
        print(f"Using preset_id: {preset_id}")  # Debug print
        
        # Stop the pump - this will create a log entry with duration
        stop_pump()
        
        # Clean up session
        session.pop('irrigation_start_time', None)
        session.pop('preset_id', None)
        session.modified = True  # Ensure session is saved
        
        return jsonify({
            'status': 'success',
            'message': 'Irrigation stopped'
        })
    
    return jsonify({
        'status': 'error',
        'message': 'Invalid action'
    }), 400
