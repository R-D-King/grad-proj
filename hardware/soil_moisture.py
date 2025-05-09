import spidev  # Installation: See README.md for proper installation instructions
import time
import random

class SoilMoistureSensor:
    """Soil moisture sensor interface with analog output."""
    
    def __init__(self, channel=0, dry_value=900, wet_value=400, simulation=False):
        """Initialize the soil moisture sensor.
        
        Args:
            channel: ADC channel for the sensor (default: 0)
            dry_value: ADC value when sensor is completely dry (default: 900)
            wet_value: ADC value when sensor is in water (default: 400)
            simulation: Whether to simulate readings
        """
        self.channel = channel
        self.dry_value = dry_value
        self.wet_value = wet_value
        self.simulation = simulation
        self.spi = None
        
        if not simulation:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)  # Open SPI bus 0, device 0
                self.spi.max_speed_hz = 1000000  # Set SPI speed to 1MHz
            except (ImportError, IOError) as e:
                print(f"Error initializing SPI for soil moisture sensor: {e}")
                self.simulation = True
                print("Using simulation mode for soil moisture sensor")
    
    def read(self):
        """Get the current moisture level as a percentage."""
        return self.get_moisture_percentage()
    
    def read_channel(self):
        """Read raw analog data from MCP3008 ADC."""
        if self.simulation:
            # Return a simulated value
            return int(random.uniform(self.wet_value, self.dry_value))
        
        try:
            adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            return data
        except Exception as e:
            print(f"Error reading soil moisture sensor: {e}")
            # Return a simulated value on error
            return int(random.uniform(self.wet_value, self.dry_value))
    
    def get_moisture_percentage(self):
        """Get the current moisture level as a percentage."""
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

# MCP3008 SPI Configuration - for backwards compatibility with existing code
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0
spi.max_speed_hz = 1000000  # 1MHz

# Soil moisture sensor channel configuration
MOISTURE_CHANNEL = 0  # Default to channel 0, can be changed as needed

# Calibration values
DRY_VALUE = 900  # Value when sensor is in dry air
WET_VALUE = 400  # Value when sensor is in water

def read_adc(channel):
    """Read the analog value from the MCP3008 ADC"""
    adc_request = [1, (8 + channel) << 4, 0]
    adc_response = spi.xfer2(adc_request)
    return ((adc_response[1] & 3) << 8) + adc_response[2]

def calculate_moisture_percentage(value):
    """Convert ADC value to moisture percentage"""
    value = max(min(value, DRY_VALUE), WET_VALUE)
    return ((DRY_VALUE - value) / (DRY_VALUE - WET_VALUE)) * 100

# Only run the test code when this file is executed directly, not when imported
if __name__ == "__main__":
    try:
        print("Soil Moisture Sensor Test Started (Press CTRL+C to exit)")
        print("----------------------------------------")
        print(f"Using MCP3008 channel: {MOISTURE_CHANNEL}")
        print("----------------------------------------")
        
        while True:
            # Read sensor and calculate moisture
            raw_value = read_adc(MOISTURE_CHANNEL)
            moisture = calculate_moisture_percentage(raw_value)
            
            # Print results
            print(f"Raw Value: {raw_value} | Moisture: {moisture:.1f}% | Channel: {MOISTURE_CHANNEL}")
            
            # Interpret the moisture level
            if moisture < 30:
                print("Status: DRY - Watering needed")
            elif moisture < 70:
                print("Status: MOIST - Adequate moisture")
            else:
                print("Status: WET - No watering needed")
            
            print("----------------------------------------")
            time.sleep(2)

    except KeyboardInterrupt:
        print("Program stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        spi.close()
        print("SPI connection closed.")