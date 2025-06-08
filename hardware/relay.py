"""
Relay control module for controlling relay-based devices.
"""
import time
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available")

class Relay:
    """Class for controlling a relay."""
    
    def __init__(self, pin, name=None):
        """Initialize the relay.
        
        Args:
            pin (int): GPIO pin number
            name (str, optional): Name of the relay for identification
        """
        self.pin = pin
        self.name = name or f"Relay-{pin}"
        self.state = False
        
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)  # Relay is typically active LOW
    
    def turn_on(self):
        """Turn on the relay."""
        if GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.LOW)  # Active LOW
        self.state = True
        print(f"Relay {self.name} turned ON")
        return True
    
    def turn_off(self):
        """Turn off the relay."""
        if GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.HIGH)  # Inactive HIGH
        self.state = False
        print(f"Relay {self.name} turned OFF")
        return True
    
    def toggle(self):
        """Toggle the relay state."""
        if self.state:
            return self.turn_off()
        else:
            return self.turn_on()
    
    def get_state(self):
        """Get the current state of the relay."""
        return self.state
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if GPIO_AVAILABLE:
            GPIO.cleanup(self.pin)