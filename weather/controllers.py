from datetime import datetime
from shared.database import db
from shared.socketio import socketio
from .models import WeatherData

def get_latest_weather_data():
    """Get the latest weather data."""
    data = WeatherData.query.order_by(WeatherData.timestamp.desc()).first()
    if data:
        return data.to_dict()
    return {
        'temperature': 0,
        'humidity': 0,
        'soil_moisture': 0,
        'wind_speed': 0,
        'pressure': 0,
        'timestamp': datetime.now().isoformat()
    }

def update_weather_data(data):
    """Update weather data with new readings."""
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