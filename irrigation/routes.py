from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from . import controllers

irrigation_bp = Blueprint('irrigation', __name__)

@irrigation_bp.route('/api/irrigation/status', methods=['GET'])
def get_irrigation_status():
    """Get the current irrigation system status."""
    from .controllers import get_pump_status, get_water_level
    
    return jsonify({
        'pump_status': get_pump_status(),
        'water_level': get_water_level()
    })

@irrigation_bp.route('/api/irrigation/pump/start', methods=['POST'])
def start_pump_route():
    data = request.json or {}
    duration = data.get('duration')
    result = controllers.start_pump(duration_seconds=duration)
    return jsonify(result)

@irrigation_bp.route('/api/irrigation/pump/stop', methods=['POST'])
def stop_pump_route():
    result = controllers.stop_pump()
    return jsonify(result)

@irrigation_bp.route('/api/irrigation/pump/status', methods=['GET'])
def pump_status_route():
    status = controllers.get_pump_status()
    return jsonify(status)

@irrigation_bp.route('/api/presets', methods=['GET'])
def get_presets_route():
    presets = controllers.get_all_presets()
    return jsonify(presets)

@irrigation_bp.route('/api/presets', methods=['POST'])
def create_preset_route():
    data = request.json
    preset = controllers.create_preset(data)
    return jsonify(preset), 201

@irrigation_bp.route('/api/presets/<int:preset_id>', methods=['PUT'])
def update_preset_route(preset_id):
    data = request.json
    preset = controllers.update_preset(preset_id, data)
    if preset:
        return jsonify(preset)
    return jsonify({'message': 'Preset not found'}), 404

@irrigation_bp.route('/api/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset_route(preset_id):
    if controllers.delete_preset(preset_id):
        return jsonify({'message': 'Preset deleted successfully'})
    return jsonify({'message': 'Preset not found'}), 404

@irrigation_bp.route('/api/presets/<int:preset_id>/activate', methods=['POST'])
def activate_preset_route(preset_id):
    preset = controllers.activate_preset(preset_id)
    if preset:
        return jsonify(preset)
    return jsonify({'message': 'Preset not found'}), 404

@irrigation_bp.route('/api/presets/<int:preset_id>/schedules', methods=['POST'])
def add_schedule_route(preset_id):
    data = request.json
    schedule = controllers.add_schedule_to_preset(preset_id, data)
    if schedule:
        return jsonify(schedule), 201
    return jsonify({'message': 'Preset not found'}), 404

@irrigation_bp.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule_route(schedule_id):
    if controllers.delete_schedule(schedule_id):
        return jsonify({'message': 'Schedule deleted successfully'})
    return jsonify({'message': 'Schedule not found'}), 404

@irrigation_bp.route('/api/irrigation/pump/duration', methods=['GET'])
def get_pump_duration():
    """Get the current pump duration."""
    from .controllers import get_pump_duration
    
    duration_seconds = get_pump_duration()
    
    # Format the duration in a more readable way (HH:MM:SS)
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    # Return both seconds and formatted time
    return jsonify({
        'seconds': duration_seconds,
        'formatted': formatted_time
    })

@irrigation_bp.route('/api/irrigation/pump/run', methods=['POST'])
def run_pump_for_duration_route():
    """Run the pump for a specific duration."""
    from .controllers import run_pump_for_duration
    data = request.json
    duration = data.get('duration', 0)
    return jsonify(run_pump_for_duration(duration))

@irrigation_bp.route('/api/irrigation/schedule', methods=['POST'])
def create_schedule():
    """Create a new irrigation schedule."""
    from .controllers import create_schedule as controller_create_schedule
    data = request.json
    return jsonify(controller_create_schedule(data))

@irrigation_bp.route('/api/irrigation/schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an existing schedule."""
    from .controllers import update_schedule as controller_update_schedule
    data = request.json
    return jsonify(controller_update_schedule(schedule_id, data))

@irrigation_bp.route('/api/irrigation/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule."""
    from .controllers import delete_schedule
    return jsonify(delete_schedule(schedule_id))
