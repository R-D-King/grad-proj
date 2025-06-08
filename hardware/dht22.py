import time
import board
import adafruit_dht

class DHT22Sensor:
    """DHT22 temperature and humidity sensor interface."""
    
    def __init__(self, pin=26, max_retries=3):
        """Initialize the DHT22 sensor.
        
        Args:
            pin: GPIO pin number (default: 26)
            max_retries: Maximum number of retries for failed readings
        """
        self.pin = pin
        self.max_retries = max_retries
        self.dht_device = None
        
        try:
            # Use the board module to get the correct pin
            dht_pin = getattr(board, f"D{pin}")
            self.dht_device = adafruit_dht.DHT22(dht_pin, use_pulseio=False)
            # Test reading to verify connection
            self.read()
        except (ImportError, ValueError, RuntimeError) as e:
            print(f"Error initializing DHT22 sensor: {e}")
    
    def read(self):
        """Read temperature and humidity from the sensor."""
        # Try to read with retries
        for attempt in range(self.max_retries):
            try:
                temperature = self.dht_device.temperature
                humidity = self.dht_device.humidity
                
                # Validate readings
                if temperature is not None and humidity is not None:
                    return {'temperature': temperature, 'humidity': humidity}
                
            except RuntimeError as e:
                # DHT sensor errors are common, just retry
                if attempt < self.max_retries - 1:
                    print(f"DHT reading error (attempt {attempt+1}/{self.max_retries}): {e}")
                    time.sleep(2.0)  # DHT sensors need 2 seconds between readings
                else:
                    print(f"Failed to read DHT after {self.max_retries} attempts: {e}")
                    # Return None values on failure
                    return {'temperature': None, 'humidity': None}
            
            except Exception as e:
                print(f"Unexpected error reading DHT: {e}")
                return {'temperature': None, 'humidity': None}
    
    def cleanup(self):
        """Clean up resources."""
        if self.dht_device:
            try:
                self.dht_device.exit()
                print("DHT22 sensor resources released")
            except Exception as e:
                print(f"Error cleaning up DHT22 sensor: {e}")
