import os
import json
import time
import signal
import sys
import logging

logger = logging.getLogger(__name__)

class LDRSensor:
    """Light Dependent Resistor (LDR) sensor interface."""
    
    def __init__(self, channel=1, min_value=0, max_value=1023, simulation=False):
        """Initialize the LDR sensor.
        
        Args:
            channel: ADC channel for the sensor (default: 1)
            min_value: Minimum ADC value (darkness) (default: 0)
            max_value: Maximum ADC value (brightness) (default: 1023)
            simulation: Whether to simulate readings
        """
        self.channel = channel
        self.min_value = min_value
        self.max_value = max_value
        self.simulation = simulation
        self.spi = None
        
        if not simulation:
            try:
                import spidev
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)  # Open SPI bus 0, device 0
                self.spi.max_speed_hz = 1000000  # Set SPI speed to 1MHz
            except (ImportError, IOError) as e:
                logger.error(f"Error initializing SPI for LDR: {e}")
                self.simulation = True
                logger.info("Using simulation mode for LDR sensor")
    
    def read_channel(self):
        """Read raw analog data from MCP3008 ADC."""
        if self.simulation:
            # Return a simulated value
            import random
            return int(random.uniform(self.min_value, self.max_value))
        
        try:
            adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            return data
        except Exception as e:
            logger.error(f"Error reading LDR sensor: {e}")
            # Return a simulated value on error
            import random
            return int(random.uniform(self.min_value, self.max_value))
    
    def get_light_percentage(self):
        """Get the current light level as a percentage."""
        raw_value = self.read_channel()
        
        # Convert raw value to percentage (higher value = more light)
        # Formula: ((max - current) / (max - min)) * 100
        percentage = ((self.max_value - raw_value) / (self.max_value - self.min_value)) * 100
        
        # Clamp to 0-100% range
        return max(0, min(100, percentage))
    
    def close(self):
        """Close the SPI connection."""
        if not self.simulation and self.spi:
            self.spi.close()

# Function to load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'hardware.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {"sensors": {"simulation": True, "pins": {"ldr": {"channel": 1, "min_value": 0, "max_value": 1023}}}}

# Function to handle clean exit
def signal_handler(sig, frame):
    logger.info("\Program terminated.")
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, signal_handler)

# Main function for standalone testing
def main():
    logger.info("LDR Sensor Monitoring Started")
    logger.info("Press CTRL+C to exit")
    logger.info("----------------------------------------")
    
    # Load configuration
    config = load_config()
    simulation = config["sensors"].get("simulation", False)
    ldr_config = config["sensors"]["pins"].get("ldr", {"channel": 1, "min_value": 0, "max_value": 1023})
    
    # Initialize sensor
    sensor = LDRSensor(
        channel=ldr_config.get("channel", 1),
        min_value=ldr_config.get("min_value", 0),
        max_value=ldr_config.get("max_value", 1023),
        simulation=simulation
    )
    
    try:
        logger.info(f"Using channel: {sensor.channel}")
        logger.info(f"Simulation mode: {sensor.simulation}")
        
        # Main loop
        while True:
            # Read raw value
            raw_value = sensor.read_channel()
            
            # Convert to percentage
            percentage = sensor.get_light_percentage()
            
            # Display values
            logger.info(f"Raw: {raw_value} | Light: {percentage:.1f}% | Channel: {sensor.channel}")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\Program terminated.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Clean shutdown
        sensor.close()
        logger.info("SPI connection closed")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
