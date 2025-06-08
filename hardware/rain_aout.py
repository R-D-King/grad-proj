import spidev
import time

# MCP3008 SPI Configuration
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1000000  # Set SPI speed to 1MHz

# Define the channel for the rain sensor
RAIN_CHANNEL = 2  # Default to channel 2, can be changed as needed

# Calibration values for the rain sensor
DRY_VALUE = 1023   # Value when sensor is completely dry
WET_VALUE = 300    # Value when sensor is wet (adjust based on your sensor)

def read_channel(channel):
    # Read analog data from MCP3008 ADC
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def calculate_wetness_percentage(value):
    # Convert ADC value to wetness percentage
    # Clamp value to calibration range
    value = max(min(value, DRY_VALUE), WET_VALUE)
    # Calculate percentage (reversed because higher ADC value = drier)
    return ((DRY_VALUE - value) / (DRY_VALUE - WET_VALUE)) * 100

# Add a RainSensor class for better integration with other files
class RainSensor:
    """Rain sensor interface with analog output."""
    
    def __init__(self, channel=RAIN_CHANNEL, dry_value=DRY_VALUE, wet_value=WET_VALUE):
        """Initialize the rain sensor."""
        self.channel = channel
        self.dry_value = dry_value
        self.wet_value = wet_value
        self.spi = None
        
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Open SPI bus 0, device 0
            self.spi.max_speed_hz = 1000000  # Set SPI speed to 1MHz
        except (ImportError, IOError):
            pass
    
    def read_channel(self):
        """Read raw analog data from MCP3008 ADC."""
        try:
            if self.spi:
                adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
                data = ((adc[1] & 3) << 8) + adc[2]
                return data
            else:
                # Use global SPI if instance SPI is not available
                return read_channel(self.channel)
        except Exception:
            return None
    
    def get_rain_percentage(self):
        """Get the current rain/wetness level as a percentage."""
        raw_value = self.read_channel()
        if raw_value is None:
            return None
        
        # Clamp value to calibration range
        raw_value = max(min(raw_value, self.dry_value), self.wet_value)
        
        # Calculate percentage (reversed because higher ADC value = drier)
        return ((self.dry_value - raw_value) / (self.dry_value - self.wet_value)) * 100
    
    def read(self):
        """Get the current rain/wetness level as a percentage (alias for get_rain_percentage)."""
        return self.get_rain_percentage()
    
    def get_status(self):
        """Get the current rain status as a string."""
        wetness = self.get_rain_percentage()
        if wetness is None:
            return "UNKNOWN"
        
        if wetness < 10:
            return "DRY - No rain detected"
        elif wetness < 50:
            return "DAMP - Light rain/moisture"
        else:
            return "WET - Heavy rain detected"
    
    def close(self):
        """Close the SPI connection."""
        if self.spi:
            self.spi.close()

# Only run the test code when this file is executed directly, not when imported
if __name__ == "__main__":
    try:
        while True:
            # Read raw analog value from rain sensor
            raw_value = read_channel(RAIN_CHANNEL)
            
            # Convert raw value to wetness percentage
            wetness = calculate_wetness_percentage(raw_value)
            
            time.sleep(1)  # Wait for 1 second before next reading
            
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    finally:
        # Clean shutdown
        spi.close()  # Release SPI resources
