from flask import Blueprint, jsonify, request, current_app
from datetime import datetime

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
def start_pump():
    """Start the irrigation pump."""
    from .controllers import start_pump as controller_start_pump
    result = controller_start_pump()
    return jsonify(result)

@irrigation_bp.route('/api/irrigation/pump/stop', methods=['POST'])
def stop_pump():
    """Stop the irrigation pump."""
    from .controllers import stop_pump as controller_stop_pump
    result = controller_stop_pump()
    return jsonify(result)

@irrigation_bp.route('/api/irrigation/presets', methods=['GET'])
def get_presets():
    """Get all irrigation presets."""
    from .controllers import get_all_presets
    return jsonify(get_all_presets())

@irrigation_bp.route('/api/irrigation/presets', methods=['POST'])
def create_preset():
    """Create a new irrigation preset."""
    from .controllers import create_preset as controller_create_preset
    data = request.json
    result = controller_create_preset(data)
    return jsonify(result)

@irrigation_bp.route('/api/irrigation/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset_route(preset_id):
    """Delete a preset."""
    from .controllers import delete_preset
    return jsonify(delete_preset(preset_id))

# Fix the duplicate endpoint function name by renaming this function
@irrigation_bp.route('/api/irrigation/presets/<int:preset_id>/activate', methods=['POST'])
def activate_preset_endpoint(preset_id):  # Changed from activate_preset_route
    """Activate a specific preset."""
    from .controllers import activate_preset
    return jsonify(activate_preset(preset_id))

# Add a new endpoint to get pump duration
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
