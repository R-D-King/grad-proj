import os
import json
import signal
import sys
import atexit
from time import sleep
import logging

logger = logging.getLogger(__name__)

class LCD:
    """16x2 LCD display interface with simulation capability."""
    
    def __init__(self, cols=16, rows=2, pin_rs=25, pin_e=24, pins_data=None, simulation=False):
        """Initialize the LCD display.
        
        Args:
            cols: Number of columns (default: 16)
            rows: Number of rows (default: 2)
            pin_rs: GPIO pin for RS (default: 25)
            pin_e: GPIO pin for E (default: 24)
            pins_data: List of GPIO pins for data lines [D4, D5, D6, D7] (default: [23, 17, 18, 22])
            simulation: Whether to simulate the display
        """
        self.cols = cols
        self.rows = rows
        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_data = pins_data or [23, 17, 18, 22]
        self.simulation = simulation
        self.lcd = None
        self.display_content = [
            [' ' for _ in range(cols)] for _ in range(rows)
        ]
        
        if not simulation:
            try:
                import RPi.GPIO as GPIO
                from RPLCD.gpio import CharLCD
                
                # Set GPIO mode
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                
                # Initialize LCD
                self.lcd = CharLCD(
                    cols=cols, 
                    rows=rows, 
                    pin_rs=pin_rs, 
                    pin_e=pin_e, 
                    pins_data=self.pins_data,
                    numbering_mode=GPIO.BCM
                )
                self.gpio = GPIO
            except (ImportError, RuntimeError) as e:
                logger.error(f"Error initializing LCD: {e}")
                self.simulation = True
                logger.info("Using simulation mode for LCD display")
    
    def clear(self):
        """Clear the display."""
        if not self.simulation and self.lcd:
            try:
                self.lcd.clear()
            except Exception as e:
                logger.error(f"Error clearing LCD: {e}")
        
        # Clear simulation display
        for row in range(self.rows):
            for col in range(self.cols):
                self.display_content[row][col] = ' '
        
        if self.simulation:
            self._print_simulation()
    
    def write_line(self, row, text):
        """Write text to a specific row on the display.
        
        Args:
            row: Row number (0 or 1 for a 16x2 display)
            text: Text to display (will be truncated if longer than display width)
        """
        if row < 0 or row >= self.rows:
            logger.error(f"Invalid row: {row}")
            return
        
        # Truncate text if needed
        text = str(text)[:self.cols]
        
        # Pad text to fill the row
        text = text.ljust(self.cols)
        
        if not self.simulation and self.lcd:
            try:
                self.lcd.cursor_pos = (row, 0)
                self.lcd.write_string(text)
            except Exception as e:
                logger.error(f"Error writing to LCD: {e}")
        
        # Update simulation display
        for col, char in enumerate(text):
            if col < self.cols:
                self.display_content[row][col] = char
        
        if self.simulation:
            self._print_simulation()
    
    def write_string(self, text, row=0, col=0):
        """Write text to the display at a specific position.
        
        Args:
            text: Text to display
            row: Starting row (default: 0)
            col: Starting column (default: 0)
        """
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            logger.error(f"Invalid position: row={row}, col={col}")
            return
        
        if not self.simulation and self.lcd:
            try:
                self.lcd.cursor_pos = (row, col)
                self.lcd.write_string(text)
            except Exception as e:
                logger.error(f"Error writing to LCD: {e}")
        
        # Update simulation display
        for i, char in enumerate(text):
            if col + i < self.cols:
                self.display_content[row][col + i] = char
            else:
                # Move to next row if text is too long
                next_row = row + 1
                next_col = col + i - self.cols
                if next_row < self.rows and next_col < self.cols:
                    self.display_content[next_row][next_col] = char
                else:
                    break
        
        if self.simulation:
            self._print_simulation()
    
    def _print_simulation(self):
        """Print the simulated display to the console."""
        display_str = "\n" + "=" * (self.cols + 2) + "\n"
        for row in self.display_content:
            display_str += "|" + "".join(row) + "|\n"
        display_str += "=" * (self.cols + 2)
        logger.info(display_str)
    
    def close(self):
        """Close the LCD connection and clean up."""
        if not self.simulation and self.lcd:
            try:
                self.clear()
                if hasattr(self, 'gpio'):
                    self.gpio.cleanup()
            except Exception as e:
                logger.error(f"Error closing LCD: {e}")

# Register cleanup function to run on exit
@atexit.register
def cleanup():
    """Clean up resources on exit."""
    logger.info("Cleaning up LCD resources")

# Function to load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'hardware.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {"sensors": {"simulation": True, "pins": {"lcd": {"cols": 16, "rows": 2, "pin_rs": 25, "pin_e": 24, "pins_data": [23, 17, 18, 22]}}}}

# Global LCD instance
lcd_instance = None

# Function to get the LCD instance (singleton pattern)
def get_lcd_instance():
    global lcd_instance
    if lcd_instance is None:
        # Load configuration
        config = load_config()
        simulation = config["sensors"].get("simulation", False)
        lcd_config = config["sensors"]["pins"].get("lcd", {
            "cols": 16, 
            "rows": 2, 
            "pin_rs": 25, 
            "pin_e": 24, 
            "pins_data": [23, 17, 18, 22]
        })
        
        # Initialize LCD
        lcd_instance = LCD(
            cols=lcd_config.get("cols", 16),
            rows=lcd_config.get("rows", 2),
            pin_rs=lcd_config.get("pin_rs", 25),
            pin_e=lcd_config.get("pin_e", 24),
            pins_data=lcd_config.get("pins_data", [23, 17, 18, 22]),
            simulation=simulation
        )
    return lcd_instance

# Function to display shutdown message and clean up
def cleanup():
    global lcd_instance
    if lcd_instance:
        try:
            # Display shutdown message
            lcd_instance.clear()
            lcd_instance.write_string("System Inactive", 0, 0)
            lcd_instance.write_string("LCD Stopped", 1, 0)
            sleep(1)  # Brief pause to ensure message is displayed
            
            # Then clear and close
            lcd_instance.close(clear=True)
        except Exception as e:
            print(f"Error during cleanup: {e}")

# Register cleanup function to run at exit
atexit.register(cleanup)
 
# Function to handle clean exit
def signal_handler(sig, frame):
    logger.info("\Program terminated.")
    # Exit will trigger the atexit handler
    sys.exit(0)

# Register signal handler for clean exit
signal.signal(signal.SIGINT, signal_handler)

# Function to display sensor readings on LCD
def display_sensor_readings(temperature=None, humidity=None, pressure=None, soil_moisture=None, light=None, rain=None):
    """Display sensor readings on the LCD.
    
    Args:
        temperature: Temperature reading in °C
        humidity: Humidity reading in %
        pressure: Pressure reading in hPa
        soil_moisture: Soil moisture reading in %
        light: Light level in %
        rain: Rain level in %
    """
    lcd = get_lcd_instance()
    
    # Display temperature and humidity on first row
    if temperature is not None and humidity is not None:
        lcd.write_string(f"T:{temperature:4.1f}C H:{humidity:4.1f}%", 0, 0)
    elif temperature is not None:
        lcd.write_string(f"Temp: {temperature:5.1f} C", 0, 0)
    elif humidity is not None:
        lcd.write_string(f"Humidity: {humidity:5.1f}%", 0, 0)
    
    # Display pressure or soil moisture on second row
    if pressure is not None:
        lcd.write_string(f"Press: {pressure:5.1f}hPa", 1, 0)
    elif soil_moisture is not None:
        lcd.write_string(f"Soil: {soil_moisture:5.1f}%", 1, 0)
    elif light is not None:
        lcd.write_string(f"Light: {light:5.1f}%", 1, 0)
    elif rain is not None:
        lcd.write_string(f"Rain: {rain:5.1f}%", 1, 0)

# Main function for standalone testing
def main():
    logger.info("LCD 16x2 Display Test Started")
    logger.info("Press CTRL+C to exit")
    logger.info("----------------------------------------")
    
    # Get LCD instance
    lcd = get_lcd_instance()
    
    try:
        # Clear the display at start
        lcd.clear()
        
        # Write to first line (row 0)
        lcd.write_string("Hello There!", 0, 0)
        sleep(2)
        
        # Move cursor to second line (row 1)
        lcd.write_string("LCD 16x2 OK!", 1, 0)
        
        # Simulate some sensor readings
        sleep(2)
        display_sensor_readings(temperature=23.5, humidity=45.2)
        sleep(2)
        display_sensor_readings(temperature=23.5, pressure=1013.2)
        sleep(2)
        display_sensor_readings(temperature=23.5, soil_moisture=67.8)
        
        # Keep the program running without writing more text
        while True:
            sleep(1)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # The atexit handler will take care of cleanup

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
