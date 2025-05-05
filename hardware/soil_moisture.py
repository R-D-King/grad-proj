import spidev  # Installation: See README.md for proper installation instructions
import time

# MCP3008 SPI Configuration
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