from flask import Blueprint, jsonify, current_app
from datetime import datetime

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/api/server-time', methods=['GET'])
def get_server_time():
    """Get the current server time."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({"time": current_time})

@shared_bp.route('/api/server-time/display', methods=['GET'])
def get_server_time_display():
    """Get the current server time formatted for display."""
    now = datetime.now()
    # Format time in 24-hour format consistently on the server side
    formatted_time = now.strftime('%H:%M:%S')
    return jsonify({
        'formatted_time': formatted_time,
        'timestamp': now.isoformat()
    })