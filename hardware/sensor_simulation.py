"""
Module for simulating sensor readings when hardware is not available.
"""
import random
import time
from datetime import datetime

class SimulatedDHT:
    """Simulates a DHT22 temperature and humidity sensor."""
    
    def __init__(self, base_temp=22.0, base_humidity=50.0):
        """Initialize the simulated sensor with base values."""
        self.base_temp = base_temp
        self.base_humidity = base_humidity
        self.last_update = time.time()
    
    def read(self):
        """Simulate reading temperature and humidity values."""
        # Add some random variation
        current_time = time.time()
        time_diff = current_time - self.last_update
        
        # More variation if more time has passed (max ±3 degrees/percent)
        max_variation = min(3.0, time_diff / 60.0)
        
        temperature = self.base_temp + random.uniform(-max_variation, max_variation)
        humidity = self.base_humidity + random.uniform(-max_variation, max_variation)
        
        # Ensure humidity stays in valid range
        humidity = max(0, min(100, humidity))
        
        self.last_update = current_time
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'timestamp': datetime.now().isoformat()
        }

class SimulatedSoilMoisture:
    """Simulates a soil moisture sensor."""
    
    def __init__(self, base_moisture=60.0):
        """Initialize the simulated sensor with base moisture value."""
        self.base_moisture = base_moisture
        self.last_update = time.time()
        self.trend = 0  # -1 for decreasing, 0 for stable, 1 for increasing
        self.trend_duration = 0
    
    def read(self):
        """Simulate reading soil moisture values."""
        current_time = time.time()
        time_diff = current_time - self.last_update
        
        # Change trend occasionally
        if self.trend_duration <= 0:
            self.trend = random.choice([-1, 0, 0, 1])  # More likely to be stable
            self.trend_duration = random.randint(5, 20)  # Trend lasts for 5-20 readings
        self.trend_duration -= 1
        
        # Calculate moisture change based on trend and time difference
        change_rate = 0.05 * time_diff  # % change per second
        if self.trend == -1:
            # Decreasing (drying out)
            change = -change_rate
        elif self.trend == 1:
            # Increasing (getting wetter)
            change = change_rate
        else:
            # Stable with small random fluctuations
            change = random.uniform(-0.2, 0.2) * change_rate
        
        # Update moisture level
        self.base_moisture += change
        
        # Ensure moisture stays in valid range
        self.base_moisture = max(0, min(100, self.base_moisture))
        
        self.last_update = current_time
        
        return {
            'moisture': round(self.base_moisture, 1),
            'raw_value': int(1023 * (1 - self.base_moisture / 100)),  # Simulate raw ADC value
            'timestamp': datetime.now().isoformat()
        }