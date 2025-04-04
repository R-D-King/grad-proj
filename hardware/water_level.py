"""
Module for water level sensor functionality.
"""
import random
import logging

# Set up logging
logger = logging.getLogger(__name__)

class WaterLevelSensor:
    """Class to interact with a water level sensor."""
    
    def __init__(self, pin=None, simulation=False):
        """Initialize the water level sensor.
        
        Args:
            pin: GPIO pin number (not used in simulation mode)
            simulation: Whether to simulate sensor readings
        """
        self.pin = pin
        self.simulation = simulation
        logger.info(f"Water level sensor initialized (simulation={simulation})")
    
    def get_level(self):
        """Get the current water level (0-100%).
        
        Returns:
            float: Water level percentage
        """
        if self.simulation:
            # Simulate a water level between 30% and 95%
            level = random.uniform(30, 95)
            # Round to integer for display
            level = round(level)
            logger.debug(f"Simulated water level: {level}%")
            return level
        
        # In a real implementation, this would read from the sensor
        # For now, just return a default value
        logger.warning("Real water level sensor not implemented, returning default")
        return 50