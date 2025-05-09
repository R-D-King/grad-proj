import os
import json
import time
import signal
import sys

class RainSensor:
    """Rain sensor interface with analog output."""
    
    def __init__(self, channel=2, dry_value=1023, wet_value=300, simulation=False):
        """Initialize the rain sensor.
        
        Args:
            channel: ADC channel for the sensor (default: 2)
            dry_value: ADC value when sensor is completely dry (default: 1023)
            wet_value: ADC value when sensor is wet (default: 300)
            simulation: Whether to simulate readings
        """
        self.channel = channel
        self.dry_value = dry_value
        self.wet_value = wet_value
        self.simulation = simulation
        self.spi = None
        
        if not simulation:
            try:
                import spidev
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)  # Open SPI bus 0, device 0
                self.spi.max_speed_hz = 1000000  # Set SPI speed to 1MHz
            except (ImportError, IOError) as e:
                print(f"Error initializing SPI for rain sensor: {e}")
                self.simulation = True
                print("Using simulation mode for rain sensor")
    
    def read_channel(self):
        """Read raw analog data from MCP3008 ADC."""
        if self.simulation:
            # Return a simulated value
            import random
            return int(random.uniform(self.wet_value, self.dry_value))
        
        try:
            adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            return data
        except Exception as e:
            print(f"Error reading rain sensor: {e}")
            # Return a simulated value on error
            import random
            return int(random.uniform(self.wet_value, self.dry_value))
    
    def get_wetness_percentage(self):
        """Get the current wetness level as a percentage."""
        raw_value = self.read_channel()
        
        # Clamp value to calibration range
        raw_value = max(min(raw_value, self.dry_value), self.wet_value)
        
        # Calculate percentage (reversed because higher ADC value = drier)
        percentage = ((self.dry_value - raw_value) / (self.dry_value - self.wet_value)) * 100
        
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
        print(f"Error loading configuration: {e}")
        return {"sensors": {"simulation": True, "pins": {"rain": {"channel": 2, "dry_value": 1023, "wet_value": 300}}}}

# Function to handle clean exit
def signal_handler(sig, frame):
    print("\nProgram terminated.")
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, signal_handler)

# Main function for standalone testing
def main():
    print("Rain Sensor Monitoring Started")
    print("Press CTRL+C to exit")
    print("----------------------------------------")
    
    # Load configuration
    config = load_config()
    simulation = config["sensors"].get("simulation", False)
    rain_config = config["sensors"]["pins"].get("rain", {"channel": 2, "dry_value": 1023, "wet_value": 300})
    
    # Initialize sensor
    sensor = RainSensor(
        channel=rain_config.get("channel", 2),
        dry_value=rain_config.get("dry_value", 1023),
        wet_value=rain_config.get("wet_value", 300),
        simulation=simulation
    )
    
    try:
        print(f"Using channel: {sensor.channel}")
        print(f"Simulation mode: {sensor.simulation}")
        
        # Main loop
        while True:
            # Read raw value
            raw_value = sensor.read_channel()
            
            # Convert to percentage
            wetness = sensor.get_wetness_percentage()
            
            # Display values and status
            print(f"Raw: {raw_value} | Wetness: {wetness:.1f}% | Channel: {sensor.channel}")
            
            # Interpret the wetness level
            if wetness < 10:
                print("Status: DRY - No rain detected")
            elif wetness < 50:
                print("Status: DAMP - Light rain/moisture")
            else:
                print("Status: WET - Heavy rain detected")
                
            print("----------------------------------------")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\Program terminated.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean shutdown
        sensor.close()
        print("SPI connection closed")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
