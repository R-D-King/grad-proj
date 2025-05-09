import logging
import time
from shared.config import Config

logger = logging.getLogger(__name__)

class Relay:
    """Class to control a relay module."""
    
    def __init__(self, pin=None, simulated=False):
        """Initialize the relay controller."""
        self.pin = pin
        self.simulated = simulated
        self.state = False  # Default state is OFF
        self.config = Config()  # Create an instance of the Config class
        
        if not simulated and pin is not None:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)  # Start with relay OFF
                logger.info(f"Hardware relay initialized on pin {pin}")
            except (ImportError, RuntimeError) as e:
                logger.warning(f"Failed to initialize hardware relay: {e}")
                logger.info("Falling back to simulated relay")
                self.simulated = True
        else:
            logger.info("Using simulated relay")
            self.simulated = True
    
    def on(self):
        """Turn the relay ON."""
        if not self.simulated:
            try:
                self.GPIO.output(self.pin, self.GPIO.HIGH)
            except Exception as e:
                logger.error(f"Error turning relay ON: {e}")
                return False
        
        self.state = True
        logger.info(f"Relay {'(simulated) ' if self.simulated else ''}turned ON")
        return True
    
    def off(self):
        """Turn the relay OFF."""
        if not self.simulated:
            try:
                self.GPIO.output(self.pin, self.GPIO.LOW)
            except Exception as e:
                logger.error(f"Error turning relay OFF: {e}")
                return False
        
        self.state = False
        logger.info(f"Relay {'(simulated) ' if self.simulated else ''}turned OFF")
        return True
    
    def get_state(self):
        """Get the current state of the relay."""
        return self.state
    
    def get_status(self):
        """Get a status dictionary for the relay."""
        return {
            "state": self.state,
            "simulated": self.simulated,
            "pin": self.pin if not self.simulated else None
        }
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if not self.simulated:
            try:
                self.GPIO.cleanup(self.pin)
                logger.info(f"Cleaned up GPIO pin {self.pin}")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO: {e}")