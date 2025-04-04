"""
Relay control module for switching devices on and off.
"""
import logging
import time

# Set up logging
logger = logging.getLogger(__name__)

class Relay:
    """
    Class to control a relay for switching devices on and off.
    
    In production, this interfaces with GPIO pins on a Raspberry Pi
    or similar device. For development, it simulates the behavior.
    """
    
    def __init__(self, pin, name="Relay", active_high=True, simulation=True):
        """
        Initialize the relay.
        
        Args:
            pin (int): GPIO pin number
            name (str): Name of the relay for logging
            active_high (bool): True if relay is activated by HIGH signal
            simulation (bool): True to run in simulation mode
        """
        self.pin = pin
        self.name = name
        self.active_high = active_high
        self.simulation = simulation
        self.state = False
        
        if not simulation:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(pin, GPIO.OUT)
                self._set_state(False)  # Initialize to OFF
                logger.info(f"Initialized {name} on pin {pin}")
            except ImportError:
                logger.warning("RPi.GPIO not available, falling back to simulation mode")
                self.simulation = True
        
    def _set_state(self, state):
        """Set the physical state of the relay."""
        if not self.simulation:
            output = state if self.active_high else not state
            self.GPIO.output(self.pin, output)
        self.state = state
    
    def on(self):
        """Turn the relay on."""
        logger.info(f"Turning {self.name} ON")
        self._set_state(True)
        return True
        
    def off(self):
        """Turn the relay off."""
        logger.info(f"Turning {self.name} OFF")
        self._set_state(False)
        return True
    
    def toggle(self):
        """Toggle the relay state."""
        if self.state:
            return self.off()
        else:
            return self.on()
    
    def get_state(self):
        """Get the current state of the relay."""
        return self.state
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if not self.simulation:
            self.GPIO.cleanup(self.pin)
            logger.info(f"Cleaned up {self.name} on pin {self.pin}")