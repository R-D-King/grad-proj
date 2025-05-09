import smbus  # Installation: See README.md for proper installation instructions
import time
from ctypes import c_short
import signal
import sys
import json
import os
import logging

logger = logging.getLogger(__name__)

class BMP180Sensor:
    """BMP180 pressure and temperature sensor interface."""
    
    def __init__(self, i2c_address=0x77, i2c_bus=1, simulation=False):
        """Initialize the BMP180 sensor.
        
        Args:
            i2c_address: I2C address of the sensor (default: 0x77)
            i2c_bus: I2C bus to use (default: 1 for Raspberry Pi)
            simulation: Whether to simulate readings
        """
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus
        self.simulation = simulation
        self.bus = None
        
        if not simulation:
            try:
                self.bus = smbus.SMBus(i2c_bus)
                # Test if sensor is reachable
                self.read_id()
            except (ImportError, IOError, OSError) as e:
                logger.error(f"Error initializing BMP180: {e}")
                self.simulation = True
                logger.info("Using simulation mode for BMP180 sensor")
    
    def get_short(self, data, index):
        """Combine two bytes and return signed 16-bit value."""
        return c_short((data[index] << 8) + data[index + 1]).value

    def get_ushort(self, data, index):
        """Combine two bytes and return unsigned 16-bit value."""
        return (data[index] << 8) + data[index + 1]
    
    def read_id(self):
        """Read chip ID and version from the sensor."""
        if self.simulation:
            return (0x55, 0x01)  # Simulated values
        
        REG_ID = 0xD0
        try:
            (chip_id, chip_version) = self.bus.read_i2c_block_data(self.i2c_address, REG_ID, 2)
            return (chip_id, chip_version)
        except Exception as e:
            logger.error(f"Error reading BMP180 ID: {e}")
            self.simulation = True
            return (0, 0)
    
    def read(self):
        """Read temperature, pressure, and altitude from the sensor."""
        if self.simulation:
            # Return simulated values
            import random
            temperature = round(random.uniform(18.0, 25.0), 1)
            pressure = round(random.uniform(990.0, 1020.0), 1)
            altitude = round(random.uniform(100.0, 120.0), 1)
            return (temperature, pressure, altitude)
        
        # Register addresses
        REG_CALIB  = 0xAA
        REG_MEAS   = 0xF4
        REG_MSB    = 0xF6
        REG_LSB    = 0xF7
        CRV_TEMP   = 0x2E
        CRV_PRES   = 0x34
        OVERSAMPLE = 3  # Oversampling setting (0-3)

        try:
            # Read calibration data from the sensor
            cal = self.bus.read_i2c_block_data(self.i2c_address, REG_CALIB, 22)

            # Convert bytes to calibration values
            AC1 = self.get_short(cal, 0)
            AC2 = self.get_short(cal, 2)
            AC3 = self.get_short(cal, 4)
            AC4 = self.get_ushort(cal, 6)
            AC5 = self.get_ushort(cal, 8)
            AC6 = self.get_ushort(cal, 10)
            B1  = self.get_short(cal, 12)
            B2  = self.get_short(cal, 14)
            MB  = self.get_short(cal, 16)
            MC  = self.get_short(cal, 18)
            MD  = self.get_short(cal, 20)

            # Request temperature measurement
            self.bus.write_byte_data(self.i2c_address, REG_MEAS, CRV_TEMP)
            time.sleep(0.005)  # Wait for measurement
            msb, lsb = self.bus.read_i2c_block_data(self.i2c_address, REG_MSB, 2)
            UT = (msb << 8) + lsb

            # Request pressure measurement
            self.bus.write_byte_data(self.i2c_address, REG_MEAS, CRV_PRES + (OVERSAMPLE << 6))
            time.sleep(0.04)  # Wait for measurement
            msb, lsb, xsb = self.bus.read_i2c_block_data(self.i2c_address, REG_MSB, 3)
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
        except Exception as e:
            logger.error(f"Error reading BMP180 sensor: {e}")
            # Return simulated values on error
            import random
            temperature = round(random.uniform(18.0, 25.0), 1)
            pressure = round(random.uniform(990.0, 1020.0), 1)
            altitude = round(random.uniform(100.0, 120.0), 1)
            return (temperature, pressure, altitude)

# Function to load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'hardware.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {"sensors": {"simulation": True, "pins": {"bmp180": {"i2c_address": "0x77", "i2c_bus": 1}}}}

# Main function for standalone testing
def main():
    logger.info("BMP180 Sensor Monitoring Started")
    logger.info("Press CTRL+C to exit")
    logger.info("----------------------------------------")
    
    # Load configuration
    config = load_config()
    simulation = config["sensors"].get("simulation", False)
    bmp_config = config["sensors"]["pins"].get("bmp180", {"i2c_address": "0x77", "i2c_bus": 1})
    
    # Convert hex string to int if needed
    i2c_address = int(bmp_config["i2c_address"], 16) if isinstance(bmp_config["i2c_address"], str) else bmp_config["i2c_address"]
    
    # Initialize sensor
    sensor = BMP180Sensor(
        i2c_address=i2c_address,
        i2c_bus=bmp_config["i2c_bus"],
        simulation=simulation
    )
    
    try:
        # Read and display chip ID and version
        chip_id, chip_version = sensor.read_id()
        logger.info(f"Chip ID: {chip_id}, Version: {chip_version}")
        logger.info(f"Simulation mode: {sensor.simulation}")
        
        # Main loop
        while True:
            try:
                temperature, pressure, altitude = sensor.read()
                logger.info(f"Temperature: {temperature:.1f} °C")
                logger.info(f"Pressure: {pressure:.1f} hPa")
                logger.info(f"Altitude: {altitude:.1f} m")
                logger.info("----------------------------------------")
            except OSError as e:
                logger.error(f"Error reading sensor: {e}")
                
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\Program terminated.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

# Function to handle clean exit
def signal_handler(sig, frame):
    print("\Program terminated.")
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, signal_handler)

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
