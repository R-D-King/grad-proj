import os
import json
from time import sleep
import logging

logger = logging.getLogger(__name__)

class LCD:
    """16x2 LCD display interface."""
    
    def __init__(self, cols=16, rows=2, pin_rs=25, pin_e=24, pins_data=None):
        """Initialize the LCD display.
        
        Args:
            cols: Number of columns (default: 16)
            rows: Number of rows (default: 2)
            pin_rs: GPIO pin for RS (default: 25)
            pin_e: GPIO pin for E (default: 24)
            pins_data: List of GPIO pins for data lines [D4, D5, D6, D7] (default: [23, 17, 18, 22])
        """
        self.cols = cols
        self.rows = rows
        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_data = pins_data or [23, 17, 18, 22]
        self.lcd = None
        
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
    
    def clear(self):
        """Clear the display."""
        if self.lcd:
            try:
                self.lcd.clear()
            except Exception as e:
                logger.error(f"Error clearing LCD: {e}")
    
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
        
        if self.lcd:
            try:
                self.lcd.cursor_pos = (row, 0)
                self.lcd.write_string(text)
            except Exception as e:
                logger.error(f"Error writing to LCD: {e}")
    
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
        
        if self.lcd:
            try:
                self.lcd.cursor_pos = (row, col)
                self.lcd.write_string(text)
            except Exception as e:
                logger.error(f"Error writing to LCD: {e}")
    
    def close(self):
        """Close the LCD connection and clean up."""
        if self.lcd:
            try:
                self.clear()
                if hasattr(self, 'gpio'):
                    self.gpio.cleanup()
            except Exception as e:
                logger.error(f"Error closing LCD: {e}")

def display_sensor_readings(lcd, temperature=None, humidity=None, pressure=None, soil_moisture=None, light=None, rain=None):
    """Display sensor readings on the LCD.
    
    Args:
        lcd: The LCD object
        temperature: Temperature reading in °C
        humidity: Humidity reading in %
        pressure: Pressure reading in hPa
        soil_moisture: Soil moisture reading in %
        light: Light level in %
        rain: Rain level in %
    """
    if lcd is None:
        logger.error("LCD object is not initialized.")
        return
        
    # Display temperature and humidity on first row
    if temperature is not None and humidity is not None:
        lcd.write_line(0, f"T:{temperature:.1f}C H:{humidity:.1f}%")
        
    # Display soil moisture on second row
    if soil_moisture is not None:
        lcd.write_line(1, f"Soil:{soil_moisture:.1f}%")
        
    # Add more display logic as needed for other sensors
    
# Example usage and testing
def main():
    """Example usage of the LCD class."""
    
    # Initialize LCD
    lcd = LCD()
    
    # Check if LCD was initialized successfully
    if lcd.lcd is None:
        logger.error("Failed to initialize LCD. Exiting.")
        return
    
    try:
        # Clear display
        lcd.clear()
        
        # Write welcome message
        lcd.write_line(0, "System Starting")
        lcd.write_line(1, "Please wait...")
        sleep(2)
        
        # Display IP and Network
        lcd.clear()
        lcd.write_line(0, "IP: 192.168.1.10")
        lcd.write_line(1, "SSID: MyNetwork")
        sleep(3)
        
        # Display sensor readings in a loop
        while True:
            # Simulate some sensor data
            temp = 23.5
            hum = 55.2
            soil = 45.8
            
            # Display on LCD
            display_sensor_readings(
                lcd,
                temperature=temp,
                humidity=hum,
                soil_moisture=soil
            )
            
            sleep(5)  # Update every 5 seconds
            
            # Display another message
            lcd.clear()
            lcd.write_line(0, "Checking Status")
            lcd.write_line(1, "All Systems Go")
            sleep(2)

    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    finally:
        # Clean up on exit
        if lcd:
            lcd.close()

if __name__ == "__main__":
    main()
