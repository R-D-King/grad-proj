from flask import Blueprint, jsonify, request
from .utils import get_formatted_server_time

shared_bp = Blueprint('shared', __name__)

# Add logging control for this endpoint
@shared_bp.route('/api/server-time/display', methods=['GET'])
def server_time_display():
    """API endpoint to get the formatted server time."""
    return jsonify({
        'formatted_time': get_formatted_server_time()
    }), 200, {'Access-Control-Allow-Origin': '*', 'X-No-Log': 'true'}