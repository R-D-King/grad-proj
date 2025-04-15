from datetime import datetime
from shared.database import db
from shared.socketio import socketio
from .models import WeatherData

# Import the sensor controller
from hardware.sensor_controller import SensorController

# Initialize the sensor controller with simulation mode based on environment
# This will be set to False on Raspberry Pi
import platform
import os

# Get configuration from environment or use defaults
UI_UPDATE_INTERVAL = int(os.environ.get('UI_UPDATE_INTERVAL', 1))  # 1 second default
DB_UPDATE_INTERVAL = int(os.environ.get('DB_UPDATE_INTERVAL', 60))  # 60 seconds default

simulation_mode = platform.system() != "Linux"
sensor_controller = SensorController(
    simulation=simulation_mode,
    ui_update_interval=UI_UPDATE_INTERVAL,
    db_update_interval=DB_UPDATE_INTERVAL
)

def init_app(app):
    """Initialize the weather controller with the app context."""
    # Set the socketio instance for the sensor controller
    sensor_controller.set_socketio(socketio)
    
    # Set the Flask app instance for the sensor controller
    sensor_controller.set_app(app)
    
    # Start sensor monitoring with configured intervals
    sensor_controller.start_monitoring()

def get_latest_weather_data():
    """Get the latest weather data."""
    # First try to get data from the database
    data = WeatherData.query.order_by(WeatherData.timestamp.desc()).first()
    
    if data:
        return data.to_dict()
    
    # If no data in database, use sensor readings
    sensor_data = sensor_controller.get_latest_readings()
    return {
        'temperature': sensor_data.get('temperature', 0),
        'humidity': sensor_data.get('humidity', 0),
        'soil_moisture': sensor_data.get('soil_moisture', 0),
        'wind_speed': 0,  # We don't have a wind sensor
        'pressure': 0,    # We don't have a pressure sensor
        'timestamp': sensor_data.get('timestamp', datetime.now().isoformat())
    }

def update_weather_data(data=None):
    """Update weather data with new readings (API endpoint)."""
    if data is None:
        # If no data provided, get from sensors
        sensor_data = sensor_controller.get_latest_readings()
        data = {
            'temperature': sensor_data.get('temperature', 0),
            'humidity': sensor_data.get('humidity', 0),
            'soil_moisture': sensor_data.get('soil_moisture', 0),
            'wind_speed': 0,  # We don't have a wind sensor
            'pressure': 0     # We don't have a pressure sensor
        }
    
    # Create new weather data entry
    weather_data = WeatherData(
        temperature=data.get('temperature', 0),
        humidity=data.get('humidity', 0),
        soil_moisture=data.get('soil_moisture', 0),
        wind_speed=data.get('wind_speed', 0),
        pressure=data.get('pressure', 0)
    )
    db.session.add(weather_data)
    db.session.commit()
    
    # Emit the new data to connected clients
    socketio.emit('weather_update', weather_data.to_dict())
    
    return weather_data.to_dict()