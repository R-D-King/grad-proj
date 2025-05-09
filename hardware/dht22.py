import adafruit_dht  # Installation: See README.md for proper installation instructions
import board
import time
import signal
import sys
import logging

logger = logging.getLogger(__name__)

# Define sensor type and pin (using BCM pin numbering)
DHT_PIN = 26
dht_sensor = adafruit_dht.DHT22(getattr(board, f"D{DHT_PIN}"))

# Function to handle clean exit
def signal_handler(sig, frame):
    logger.info("\nProgram terminated.")
    # Clean up resources
    dht_sensor.exit()
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, signal_handler)

# Main loop
try:
    logger.info("DHT22 Sensor Reading (Press CTRL+C to exit)")
    logger.info("----------------------------------------")
    
    while True:
        try:
            temperature = dht_sensor.temperature
            humidity = dht_sensor.humidity
            
            if humidity is not None and temperature is not None:
                logger.info(f"Temperature: {temperature:.1f}°C")
                logger.info(f"Humidity: {humidity:.1f}%")
            else:
                logger.error("Failed to read data from sensor")
            
            logger.info("----------------------------------------")
        except RuntimeError as e:
            # DHT sensors sometimes fail to read, just try again
            logger.error(f"Reading error: {e}")
        
        time.sleep(2)  # DHT22 needs at least 2 seconds between readings

except Exception as e:
    logger.error(f"An error occurred: {e}")
finally:
    # This will run on any exit except when CTRL+C is pressed (which is handled by signal_handler)
    logger.info("Program ended.")
    try:
        dht_sensor.exit()
    except:
        pass
