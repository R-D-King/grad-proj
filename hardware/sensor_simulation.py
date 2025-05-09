import random
import time
import logging

logger = logging.getLogger(__name__)

class SimulatedSensor:
    """Base class for simulated sensors."""
    
    def __init__(self, sensor_type, min_value=0, max_value=100, default_value=None, variation=5.0):
        """Initialize a simulated sensor.
        
        Args:
            sensor_type: Type of sensor being simulated
            min_value: Minimum possible value
            max_value: Maximum possible value
            default_value: Default value to start with (if None, will use middle of range)
            variation: Maximum variation per reading (percentage of range)
        """
        self.sensor_type = sensor_type
        self.min_value = min_value
        self.max_value = max_value
        self.default_value = default_value if default_value is not None else (min_value + max_value) / 2
        self.variation = variation
        self.current_value = self.default_value
        
        logger.info(f"Initialized simulated {sensor_type} sensor with range {min_value}-{max_value}")
    
    def read(self):
        """Read a simulated value."""
        # Calculate the maximum change allowed
        value_range = self.max_value - self.min_value
        max_change = (value_range * self.variation) / 100.0
        
        # Generate a random change
        change = random.uniform(-max_change, max_change)
        
        # Apply the change to the current value
        self.current_value += change
        
        # Ensure the value stays within the allowed range
        self.current_value = max(self.min_value, min(self.max_value, self.current_value))
        
        # Return the current value
        return self.current_value

class SimulatedDHT:
    """Simulated DHT22 temperature and humidity sensor."""
    
    def __init__(self, temp_min=18.0, temp_max=30.0, humid_min=30.0, humid_max=80.0):
        """Initialize the simulated DHT sensor.
        
        Args:
            temp_min: Minimum temperature value
            temp_max: Maximum temperature value
            humid_min: Minimum humidity value
            humid_max: Maximum humidity value
        """
        self.temp_sensor = SimulatedSensor('temperature', temp_min, temp_max)
        self.humid_sensor = SimulatedSensor('humidity', humid_min, humid_max)
    
    def read(self):
        """Read simulated temperature and humidity values."""
        temperature = self.temp_sensor.read()
        humidity = self.humid_sensor.read()
        return temperature, humidity

class SimulatedSoilMoisture:
    """Simulated soil moisture sensor."""
    
    def __init__(self, min_value=0.0, max_value=100.0):
        """Initialize the simulated soil moisture sensor.
        
        Args:
            min_value: Minimum moisture value (0%)
            max_value: Maximum moisture value (100%)
        """
        self.sensor = SimulatedSensor('soil_moisture', min_value, max_value)
    
    def read(self):
        """Read simulated soil moisture value."""
        return self.sensor.read()