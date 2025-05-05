from datetime import datetime
from shared.database import db

class WeatherData(db.Model):
    """Model for weather data."""
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    soil_moisture = db.Column(db.Float, nullable=True)
    pressure = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'soil_moisture': self.soil_moisture,
            'pressure': self.pressure,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }