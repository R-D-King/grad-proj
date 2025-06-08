from datetime import datetime
from shared.database import db
from shared.socketio import socketio
from .models import WeatherData
import time
import threading
import logging
from flask import current_app

# Import the sensor controller
from hardware.sensor_controller import SensorController
from hardware.lcd_16x2 import LCD
import subprocess

# Set up logging
logger = logging.getLogger(__name__)

import platform
import os

# Get configuration from environment or use defaults
UI_UPDATE_INTERVAL = int(os.environ.get('UI_UPDATE_INTERVAL', 2))  # 2 seconds default
DB_UPDATE_INTERVAL = int(os.environ.get('DB_UPDATE_INTERVAL', 60))  # 60 seconds default

sensor_controller = SensorController()

# LCD display instance - will be initialized in init_app
lcd = None
lcd_thread = None
lcd_running = False

def init_app(app):
    """Initialize the weather controller with the Flask app context."""
    global lcd, lcd_thread, lcd_running
    
    sensor_controller.set_app(app)
    sensor_controller.set_socketio(socketio)
    
    try:
        config = app.config.get_namespace('')
        lcd_config = config.get('hardware', {}).get('sensors', {}).get('pins', {}).get('lcd', {})
        lcd = LCD(
            cols=lcd_config.get('cols', 16), 
            rows=lcd_config.get('rows', 2), 
            pin_rs=lcd_config.get('pin_rs', 25), 
            pin_e=lcd_config.get('pin_e', 24), 
            pins_data=lcd_config.get('pins_data', [23, 17, 18, 22])
        )
        
        from app import get_network_ssid
        network_ssid = get_network_ssid()
        ip_address = app.config.get('IP_ADDRESS', '127.0.0.1')
        port = app.config.get('PORT', 5000)
        
        lcd.clear()
        lcd.write_line(0, f"Network: {network_ssid}")
        lcd.write_line(1, f"{ip_address}")
        
        lcd_running = True
        lcd_thread = threading.Thread(target=lcd_update_loop, args=(app,))
        lcd_thread.daemon = True
        lcd_thread.start()
        logger.info("LCD display initialized and update thread started")
    except Exception as e:
        logger.error(f"Failed to initialize LCD display: {e}")
        lcd = None

    # Start the monitoring thread for UI sensor data
    update_thread = socketio.start_background_task(target=emit_sensor_updates, app=app)
    setattr(update_thread, "do_run", True)

    # Start the monitoring thread for sensor connection status
    status_thread = socketio.start_background_task(target=emit_sensor_status, app=app)
    setattr(status_thread, "do_run", True)

    # Start the CSV logging thread
    sensor_controller.start_csv_logging()

    logger.info("Weather controller initialized and monitoring started.")
    return sensor_controller

def get_pressure_display():
    """Get formatted pressure display data."""
    from hardware.bmp180 import BMP180Sensor
    
    try:
        # Create a BMP180 sensor instance
        bmp_sensor = BMP180Sensor()
        
        # Get the pressure reading
        _, pressure, _ = bmp_sensor.read()
        
        if pressure is None:
            return ("Pressure:", "Not available")
        
        # Format the pressure reading
        return (f"Pressure:", f"{pressure:.1f} hPa")
    except Exception:
        return ("Pressure:", "Error")

def get_light_display():
    """Get formatted light display data."""
    from hardware.ldr_aout import LDRSensor
    
    try:
        # Create an LDR sensor instance
        ldr_sensor = LDRSensor()
        
        # Get the light percentage
        light = ldr_sensor.get_light_percentage()
        
        if light is None:
            return ("Light Level:", "Not available")
        
        # Format the light reading
        return (f"Light Level:", f"{light:.1f}%")
    except Exception:
        return ("Light Level:", "Error")

def get_rain_display():
    """Get formatted rain display data."""
    from hardware.rain_aout import RainSensor
    
    try:
        # Create a Rain sensor instance
        rain_sensor = RainSensor()
        
        # Get the rain percentage
        rain = rain_sensor.get_rain_percentage()
        
        if rain is None:
            return ("Rain Level:", "Not available")
        
        # Format the rain reading
        return (f"Rain Level:", f"{rain:.1f}%")
    except Exception:
        return ("Rain Level:", "Error")

def lcd_update_loop(app):
    """Background thread for updating LCD display."""
    global lcd_running
    time.sleep(5)
    
    from app import get_network_ssid
    display_modes = [
        lambda: (f"Network:", f"{get_network_ssid()}"),
        lambda: (f"{app.config.get('IP_ADDRESS', '127.0.0.1')[:16]}", f"Port:{app.config.get('PORT', 5000)}"),
        lambda: (f"Temp: {sensor_controller.get_latest_readings().get('temperature', 0):.1f}C", f"Humid: {sensor_controller.get_latest_readings().get('humidity', 0):.1f}%"),
        lambda: (f"Soil Moisture:", f"{sensor_controller.get_latest_readings().get('soil_moisture', 0):.1f}%"),
        lambda: (f"Pressure:", f"{sensor_controller.get_latest_readings().get('pressure', 0):.1f} hPa"),
        lambda: (f"Light Level:", f"{sensor_controller.get_latest_readings().get('light', 0):.1f}%"),
        lambda: (f"Rain Level:", f"{sensor_controller.get_latest_readings().get('rain', 0):.1f}%")
    ]
    
    current_mode = 0
    while lcd_running and lcd:
        try:
            line1, line2 = display_modes[current_mode]()
            lcd.clear()
            lcd.write_line(0, line1)
            lcd.write_line(1, line2)
            current_mode = (current_mode + 1) % len(display_modes)
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error in LCD update loop: {e}")
            time.sleep(1)

def get_latest_weather_data():
    """Get the latest weather data from the controller."""
    return sensor_controller.get_latest_readings()

def update_weather_data(data):
    """Update weather data in the database."""
    new_data = WeatherData(
        temperature=data.get('temperature'),
        humidity=data.get('humidity'),
        soil_moisture=data.get('soil_moisture'),
        pressure=data.get('pressure'),
        light=data.get('light'),
        rain=data.get('rain')
    )
    db.session.add(new_data)
    db.session.commit()
    logger.info(f"Logged new weather data to database: {data}")

def get_network_ssid():
    """Get the SSID of the connected WiFi network."""
    try:
        if platform.system() == "Linux":
            # For Raspberry Pi / Linux
            result = subprocess.check_output(['iwgetid', '-r']).decode('utf-8').strip()
            return result if result else "Not connected"
        else:
            # For other OS (e.g., development)
            return "Dev-SSID"  # Placeholder for development
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
        except Exception:
            pass

def emit_sensor_updates(app):
    """Continuously emit sensor data updates to clients."""
    ui_update_interval = app.config.get('UI_UPDATE_INTERVAL', 2)
    while getattr(threading.current_thread(), "do_run", True):
        with app.app_context():
            sensor_data = sensor_controller.get_latest_readings()
            socketio.emit('sensor_update', sensor_data)
        socketio.sleep(ui_update_interval)

def emit_sensor_status(app):
    """Periodically emit the connection status of sensors."""
    status_update_interval = app.config.get('SENSOR_STATUS_INTERVAL', 5) # 5 seconds
    while getattr(threading.current_thread(), "do_run", True):
        with app.app_context():
            statuses = sensor_controller.get_sensor_statuses()
            socketio.emit('sensor_status_update', statuses)
        socketio.sleep(status_update_interval)
