from flask import Blueprint, request, jsonify
from .controllers import get_latest_weather_data, update_weather_data

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/api/weather/current', methods=['GET'])
def current_weather():
    """Get current weather data."""
    return jsonify(get_latest_weather_data())

@weather_bp.route('/api/weather/update', methods=['POST'])
def update_weather():
    """Update weather data (protected endpoint for sensors)."""
    data = request.json
    return jsonify(update_weather_data(data))