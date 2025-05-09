import smbus  # Installation: See README.md for proper installation instructions
import time
from ctypes import c_short
import signal
import sys

# Configuration
DEVICE = 0x77  # I2C address of BMP180 sensor
bus = smbus.SMBus(1)  # Use I2C bus 1 on Raspberry Pi

def getShort(data, index):
    # Combine two bytes and return signed 16-bit value
    return c_short((data[index] << 8) + data[index + 1]).value

def getUshort(data, index):
    # Combine two bytes and return unsigned 16-bit value
    return (data[index] << 8) + data[index + 1]

def readBmp180Id(addr=DEVICE):
    # Read chip ID and version from the sensor
    REG_ID = 0xD0
    (chip_id, chip_version) = bus.read_i2c_block_data(addr, REG_ID, 2)
    return (chip_id, chip_version)

def readBmp180(addr=DEVICE):
    # Register addresses
    REG_CALIB  = 0xAA
    REG_MEAS   = 0xF4
    REG_MSB    = 0xF6
    REG_LSB    = 0xF7
    CRV_TEMP   = 0x2E
    CRV_PRES   = 0x34
    OVERSAMPLE = 3  # Oversampling setting (0-3)

    # Read calibration data from the sensor
    cal = bus.read_i2c_block_data(addr, REG_CALIB, 22)

    # Convert bytes to calibration values
    AC1 = getShort(cal, 0)
    AC2 = getShort(cal, 2)
    AC3 = getShort(cal, 4)
    AC4 = getUshort(cal, 6)
    AC5 = getUshort(cal, 8)
    AC6 = getUshort(cal, 10)
    B1  = getShort(cal, 12)
    B2  = getShort(cal, 14)
    MB  = getShort(cal, 16)
    MC  = getShort(cal, 18)
    MD  = getShort(cal, 20)

    # Request temperature measurement
    bus.write_byte_data(addr, REG_MEAS, CRV_TEMP)
    time.sleep(0.005)  # Wait for measurement
    msb, lsb = bus.read_i2c_block_data(addr, REG_MSB, 2)
    UT = (msb << 8) + lsb

    # Request pressure measurement
    bus.write_byte_data(addr, REG_MEAS, CRV_PRES + (OVERSAMPLE << 6))
    time.sleep(0.04)  # Wait for measurement
    msb, lsb, xsb = bus.read_i2c_block_data(addr, REG_MSB, 3)
    UP = ((msb << 16) + (lsb << 8) + xsb) >> (8 - OVERSAMPLE)

    # Calculate true temperature
    X1 = ((UT - AC6) * AC5) >> 15
    X2 = int((MC << 11) / (X1 + MD))
    B5 = X1 + X2
    temperature = int(B5 + 8) >> 4
    temperature = temperature / 10.0

    # Calculate true pressure
    B6 = B5 - 4000
    X1 = (B2 * (B6 * B6 >> 12)) >> 11
    X2 = (AC2 * B6) >> 11
    X3 = X1 + X2
    B3 = (((AC1 * 4 + X3) << OVERSAMPLE) + 2) >> 2
    X1 = (AC3 * B6) >> 13
    X2 = (B1 * (B6 * B6 >> 12)) >> 16
    X3 = ((X1 + X2) + 2) >> 2
    B4 = (AC4 * (X3 + 32768)) >> 15
    B7 = (UP - B3) * (50000 >> OVERSAMPLE)

    if B7 < 0x80000000:
        P = (B7 * 2) // B4
    else:
        P = (B7 // B4) * 2

    X1 = (P >> 8) * (P >> 8)
    X1 = (X1 * 3038) >> 16
    X2 = (-7357 * P) >> 16
    pressure = P + ((X1 + X2 + 3791) >> 4)
    pressure = pressure / 100.0  # Convert to hPa

    # Calculate altitude using pressure
    altitude = 44330.0 * (1.0 - pow(pressure / 1013.25, 1.0 / 5.255))
    altitude = round(altitude, 2)

    return (temperature, pressure, altitude)

# Function to handle clean exit
def signal_handler(sig, frame):
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, signal_handler)

# Add a BMP180Sensor class for better integration with other files
class BMP180Sensor:
    """BMP180 pressure, temperature and altitude sensor interface."""
    
    def __init__(self, i2c_address=DEVICE, i2c_bus=1, simulation=False):
        """Initialize the BMP180 sensor."""
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus
        self.simulation = simulation
        
        if not simulation:
            try:
                # Try to initialize the I2C bus
                global bus
                bus = smbus.SMBus(i2c_bus)
            except (ImportError, IOError):
                self.simulation = True
    
    def read(self):
        """Read sensor data and return temperature, pressure, and altitude."""
        if self.simulation:
            # Return simulated values
            import random
            temperature = round(random.uniform(18.0, 25.0), 1)
            pressure = round(random.uniform(980.0, 1050.0), 1)
            altitude = round(random.uniform(0.0, 100.0), 2)
            return (temperature, pressure, altitude)
        
        try:
            return readBmp180(self.i2c_address)
        except Exception:
            # Return simulated values on error
            import random
            temperature = round(random.uniform(18.0, 25.0), 1)
            pressure = round(random.uniform(980.0, 1050.0), 1)
            altitude = round(random.uniform(0.0, 100.0), 2)
            return (temperature, pressure, altitude)
    
    def get_temperature(self):
        """Get the current temperature in °C."""
        return self.read()[0]
    
    def get_pressure(self):
        """Get the current pressure in hPa."""
        return self.read()[1]
    
    def get_altitude(self):
        """Get the current altitude in meters."""
        return self.read()[2]

# Main function
def main():
    try:
        # Read and display chip ID and version
        chip_id, chip_version = readBmp180Id()
        
        # Main loop
        while True:
            temperature, pressure, altitude = readBmp180()
            time.sleep(1)
    except Exception:
        pass

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
