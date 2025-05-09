"""
Relay control module for controlling relay-based devices.
"""
import time
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

class Relay:
    """Class for controlling a relay."""
    
    def __init__(self, pin, name=None, simulation=False):
        """Initialize the relay.
        
        Args:
            pin (int): GPIO pin number
            name (str, optional): Name of the relay for identification
            simulation (bool): Whether to use simulated relay
        """
        self.pin = pin
        self.name = name or f"Relay-{pin}"
        self.simulation = simulation
        self.state = False
        
        if not simulation and GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)  # Relay is typically active LOW
    
    def turn_on(self):
        """Turn on the relay."""
        if not self.simulation and GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.LOW)  # Active LOW
        self.state = True
        return True
    
    def turn_off(self):
        """Turn off the relay."""
        if not self.simulation and GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.HIGH)  # Inactive HIGH
        self.state = False
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
        if not self.simulation and GPIO_AVAILABLE:
            GPIO.cleanup(self.pin)