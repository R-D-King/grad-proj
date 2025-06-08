"""
Pump control module for irrigation system.
This module provides an interface for controlling a water pump via a relay.
"""
import logging
import time
from .relay import Relay

# Set up logging
logger = logging.getLogger(__name__)

class Pump:
    """
    Class to control a water pump via a relay.
    
    This class provides methods to start and stop the pump,
    as well as run it for a specific duration.
    """
    
    def __init__(self, relay_pin=17, name="Water Pump"):
        """
        Initialize the pump controller.
        
        Args:
            relay_pin (int): GPIO pin number connected to the relay
            name (str): Name of the pump for logging
        """
        self.name = name
        self.relay = Relay(pin=relay_pin, name=f"{name} Relay")
        self.running = False
        self.start_time = None
        logger.info(f"Initialized {name} controller using relay on pin {relay_pin}")
    
    def start(self):
        """
        Start the pump.
        
        Returns:
            bool: True if pump was started successfully
        """
        if self.running:
            logger.info(f"{self.name} is already running")
            return False
        
        result = self.relay.on()
        if result:
            self.running = True
            self.start_time = time.time()
            logger.info(f"{self.name} started")
        return result
    
    def stop(self):
        """
        Stop the pump.
        
        Returns:
            dict: Status information including runtime if pump was running
        """
        if not self.running:
            logger.info(f"{self.name} is already stopped")
            return {"status": "not_running", "message": f"{self.name} was not running"}
        
        result = self.relay.off()
        if result:
            self.running = False
            runtime = time.time() - self.start_time if self.start_time else 0
            self.start_time = None
            logger.info(f"{self.name} stopped after running for {runtime:.2f} seconds")
            return {
                "status": "success", 
                "message": f"{self.name} stopped", 
                "runtime": runtime
            }
        return {"status": "error", "message": f"Failed to stop {self.name}"}
    
    def run_for_duration(self, duration):
        """
        Run the pump for a specific duration in seconds.
        
        Args:
            duration (float): Duration in seconds to run the pump
            
        Returns:
            dict: Status information including actual runtime
        """
        if self.running:
            logger.warning(f"{self.name} is already running, stopping first")
            self.stop()
        
        logger.info(f"Running {self.name} for {duration} seconds")
        self.start()
        
        # In a real application, you would use a separate thread or async
        # to avoid blocking. This is a simplified version.
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            logger.warning(f"{self.name} operation interrupted")
        finally:
            return self.stop()
    
    def get_status(self):
        """
        Get the current status of the pump.
        
        Returns:
            dict: Status information
        """
        runtime = None
        if self.running and self.start_time:
            runtime = time.time() - self.start_time
            
        return {
            "name": self.name,
            "running": self.running,
            "runtime": runtime,
            "relay_state": self.relay.get_state()
        }
    
    def cleanup(self):
        """Clean up resources."""
        if self.running:
            self.stop()
        self.relay.cleanup()
        logger.info(f"{self.name} resources cleaned up")