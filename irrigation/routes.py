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
    from .controllers import get_presets
    return jsonify(get_presets())

# Change this route to match the frontend call (plural 'presets' instead of singular 'preset')
@irrigation_bp.route('/api/irrigation/presets/<int:preset_id>', methods=['GET'])
def get_preset(preset_id):
    """Get a specific irrigation preset."""
    from .controllers import get_preset
    preset = get_preset(preset_id)
    if preset:
        return jsonify(preset)
    return jsonify({"error": "Preset not found"}), 404

@irrigation_bp.route('/api/irrigation/presets', methods=['POST'])
def create_preset():
    """Create a new irrigation preset."""
    from .controllers import create_preset as controller_create_preset
    data = request.json
    result = controller_create_preset(data)
    return jsonify(result)

# Keep your existing delete route with plural 'presets'
@irrigation_bp.route('/api/irrigation/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset_route(preset_id):
    """Delete a preset."""
    from .controllers import delete_preset
    return jsonify(delete_preset(preset_id))

# Add a new route that handles the singular 'preset' form for backward compatibility
@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>', methods=['DELETE'])
def delete_preset_singular_route(preset_id):
    """Delete a preset (singular route for backward compatibility)."""
    from .controllers import delete_preset
    return jsonify(delete_preset(preset_id))

# Fix the duplicate endpoint function name by renaming this function
# Change this route to use plural 'presets' instead of singular 'preset'
# Update the existing activate route to use plural 'presets'
@irrigation_bp.route('/api/irrigation/presets/<int:preset_id>/activate', methods=['POST'])
def activate_preset_endpoint(preset_id):
    """Activate a specific preset."""
    from .controllers import activate_preset
    return jsonify(activate_preset(preset_id))

# Add a backward compatibility route for the singular form
@irrigation_bp.route('/api/irrigation/preset/<int:preset_id>/activate', methods=['POST'])
def activate_preset_singular_endpoint(preset_id):
    """Activate a specific preset (singular route for backward compatibility)."""
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
