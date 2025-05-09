from datetime import datetime
from shared.database import db
from shared.socketio import socketio
from .models import WeatherData
import time
import threading
import logging

# Import the sensor controller
from hardware.sensor_controller import SensorController
from hardware.lcd_16x2 import LCD
import subprocess

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the sensor controller with simulation mode based on environment
# This will be set to False on Raspberry Pi
import platform
import os

# Get configuration from environment or use defaults
UI_UPDATE_INTERVAL = int(os.environ.get('UI_UPDATE_INTERVAL', 1))  # 1 second default
DB_UPDATE_INTERVAL = int(os.environ.get('DB_UPDATE_INTERVAL', 60))  # 60 seconds default

simulation_mode = platform.system() != "Linux"
sensor_controller = SensorController(
    simulation=simulation_mode
)

# LCD display instance - will be initialized in init_app
lcd = None
lcd_thread = None
lcd_running = False

def init_app(app):
    """Initialize the weather controller with the app context."""
    global lcd, lcd_thread, lcd_running
    
    # Set the socketio instance for the sensor controller
    sensor_controller.set_socketio(socketio)
    
    # Set the Flask app instance for the sensor controller
    sensor_controller.set_app(app)
    
    # Start sensor monitoring with configured intervals
    sensor_controller.start_monitoring()
    
    # Initialize LCD display with configuration from app
    try:
        # Get LCD configuration from app config
        config = app.config.get_namespace('')
        lcd_config = config.get('hardware', {}).get('sensors', {}).get('pins', {}).get('lcd', {})
        
        # Extract LCD parameters with defaults as fallback
        cols = lcd_config.get('cols', 16)
        rows = lcd_config.get('rows', 2)
        pin_rs = lcd_config.get('pin_rs', 25)
        pin_e = lcd_config.get('pin_e', 24)
        pins_data = lcd_config.get('pins_data', [23, 17, 18, 22])
        simulation = simulation_mode
        
        # Initialize LCD
        lcd = LCD(
            cols=cols, 
            rows=rows, 
            pin_rs=pin_rs, 
            pin_e=pin_e, 
            pins_data=pins_data, 
            simulation=simulation
        )
        
        # Display network name, IP and port on LCD
        network_ssid = get_network_ssid()
        ip_address = app.config.get('IP_ADDRESS', '127.0.0.1')
        port = app.config.get('PORT', 5000)
        
        lcd.clear()
        lcd.write_line(0, f"Network: {network_ssid}")
        lcd.write_line(1, f"IP: {ip_address}")
        
        # Start LCD update thread
        lcd_running = True
        lcd_thread = threading.Thread(target=lcd_update_loop, args=(app,))
        lcd_thread.daemon = True
        lcd_thread.start()
        
        logger.info("LCD display initialized and update thread started")
    except Exception as e:
        logger.error(f"Failed to initialize LCD display: {e}")
        lcd = None

def lcd_update_loop(app):
    """Background thread for updating LCD display."""
    global lcd_running
    
    # Wait 5 seconds to keep showing IP and port
    time.sleep(5)
    
    # Define display modes and their data
    display_modes = [
        # Mode 0: Network Name (SSID) - Now first in the list
        lambda: (f"Network:", 
                f"{get_network_ssid()}"),
        
        # Mode 1: IP and Port
        lambda: (f"IP:{app.config.get('IP_ADDRESS', '127.0.0.1')[:16]}", 
                f"Port:{app.config.get('PORT', 5000)}"),
        
        # Mode 2: Temperature and Humidity
        lambda: (f"Temp: {sensor_controller.get_latest_readings().get('temperature', 0):.1f}C", 
                f"Humid: {sensor_controller.get_latest_readings().get('humidity', 0):.1f}%"),
        
        # Mode 3: Soil Moisture
        lambda: (f"Soil Moisture:", 
                f"{sensor_controller.get_latest_readings().get('soil_moisture', 0):.1f}%"),
        
        # Mode 4: Pressure from BMP180 - Reimplemented
        lambda: get_pressure_display(),
        
        # Mode 5: Light Percentage from LDR - Reimplemented
        lambda: get_light_display(),
                
        # Mode 6: Rain Percentage - Reimplemented
        lambda: get_rain_display()
    ]
    
    current_mode = 0
    
    while lcd_running and lcd:
        try:
            # Get data for current display mode
            line1, line2 = display_modes[current_mode]()
            
            # Update LCD
            lcd.clear()
            lcd.write_line(0, line1)
            lcd.write_line(1, line2)
            
            # Cycle to next mode
            current_mode = (current_mode + 1) % len(display_modes)
            
            # Wait before changing display
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error updating LCD: {e}")
            time.sleep(1)

def get_pressure_display():
    """Get formatted pressure display data."""
    readings = sensor_controller.get_latest_readings()
    pressure = readings.get('pressure')
    if pressure is None:
        return ("Pressure:", "Not available")
    try:
        # Try to format as float, but handle any conversion errors
        return (f"Pressure:", f"{float(pressure):.1f} hPa")
    except (ValueError, TypeError):
        # If conversion fails, just display the raw value
        return (f"Pressure:", f"{pressure} hPa")

def get_light_display():
    """Get formatted light display data."""
    readings = sensor_controller.get_latest_readings()
    light = readings.get('light')
    if light is None:
        return ("Light Level:", "Not available")
    try:
        # Try to format as float, but handle any conversion errors
        return (f"Light Level:", f"{float(light):.1f}%")
    except (ValueError, TypeError):
        # If conversion fails, just display the raw value
        return (f"Light Level:", f"{light}%")

def get_rain_display():
    """Get formatted rain display data."""
    readings = sensor_controller.get_latest_readings()
    rain = readings.get('rain')
    if rain is None:
        return ("Rain Level:", "Not available")
    try:
        # Try to format as float, but handle any conversion errors
        return (f"Rain Level:", f"{float(rain):.1f}%")
    except (ValueError, TypeError):
        # If conversion fails, just display the raw value
        return (f"Rain Level:", f"{rain}%")

def get_latest_weather_data():
    """Get the latest weather data."""
    # First try to get data from the database
    data = WeatherData.query.order_by(WeatherData.timestamp.desc()).first()
    
    if data:
        return data.to_dict()
    
    # If no data in database, use sensor readings
    sensor_data = sensor_controller.get_latest_readings()
    return {
        'temperature': sensor_data.get('temperature', 0),
        'humidity': sensor_data.get('humidity', 0),
        'soil_moisture': sensor_data.get('soil_moisture', 0),
        'pressure': 0,    # We don't have a pressure sensor
        'timestamp': sensor_data.get('timestamp', datetime.now().isoformat())
    }

def update_weather_data(data=None):
    """Update weather data with new readings (API endpoint)."""
    if data is None:
        # If no data provided, get from sensors
        sensor_data = sensor_controller.get_latest_readings()
        data = {
            'temperature': sensor_data.get('temperature', 0),
            'humidity': sensor_data.get('humidity', 0),
            'soil_moisture': sensor_data.get('soil_moisture', 0),
            'pressure': 0     # We don't have a pressure sensor
        }
    
    # Create new weather data entry
    weather_data = WeatherData(
        temperature=data.get('temperature', 0),
        humidity=data.get('humidity', 0),
        soil_moisture=data.get('soil_moisture', 0),
        pressure=data.get('pressure', 0)
    )
    db.session.add(weather_data)
    db.session.commit()
    
    # Emit the new data to connected clients
    socketio.emit('weather_update', weather_data.to_dict())
    
    return weather_data.to_dict()


def get_network_ssid():
    """Get the SSID of the connected WiFi network."""
    try:
        if platform.system() == "Linux":
            # For Raspberry Pi / Linux
            result = subprocess.check_output(['iwgetid', '-r']).decode('utf-8').strip()
            return result if result else "Not connected"
        else:
            # For Windows (simulation mode)
            return "Simulation SSID"
    except Exception as e:
        logger.error(f"Error getting network SSID: {e}")
        return "Unknown"


def display_shutdown():
    """Display shutdown message on the LCD."""
    global lcd
    if lcd:
        try:
            lcd.clear()
            lcd.write_line(0, "System")
            lcd.write_line(1, "Shutting Down...")
        except Exception as e:
            logger.error(f"Error displaying shutdown message: {e}")