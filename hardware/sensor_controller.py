"""
Module for integrating and managing hardware sensors.
"""
import time
import logging
import platform
import threading
from datetime import datetime
from flask import current_app
import os
import csv
from threading import Lock

# Set up logging
logger = logging.getLogger(__name__)

class SensorController:
    """Controller for managing all sensors in the system."""
    
    def __init__(self):
        """Initialize the sensor controller."""
        self.sensors = {}
        self.last_readings = {
            'temperature': None, 'humidity': None, 'soil_moisture': None,
            'pressure': None, 'light': None, 'rain': None, 'timestamp': None
        }
        self.running = False
        self.socketio = None
        self.app = None
        
        self.readings_lock = Lock()
        self.sensor_threads = []

        self.ui_update_interval = 0.5  # Broadcast data to UI every 500ms
        self.db_update_interval = 60
        
        self.csv_logging_enabled = False
        self.data_folder = None
        self.log_interval = 60
        self.csv_writer = None
        self.logging_thread = None
        
        self._initialize_sensors()
    
    def _initialize_sensors(self):
        """Initialize all sensors and create placeholder if they fail."""
        sensor_map = {
            'dht': ('hardware.dht22', 'DHT22Sensor', {'pin': 26}),
            'soil_moisture': ('hardware.soil_moisture', 'SoilMoistureSensor', {}),
            'pressure': ('hardware.bmp180', 'BMP180Sensor', {}),
            'light': ('hardware.ldr_aout', 'LDRSensor', {}),
            'rain': ('hardware.rain_aout', 'RainSensor', {})
        }

        for name, (module_path, class_name, kwargs) in sensor_map.items():
            try:
                module = __import__(module_path, fromlist=[class_name])
                sensor_class = getattr(module, class_name)
                self.sensors[name] = sensor_class(**kwargs)
                logger.info(f"Successfully initialized {name} sensor.")
            except Exception as e:
                self.sensors[name] = None
                logger.error(f"Failed to initialize {name} sensor: {e}. It will be disabled.")

    def _read_sensor_loop(self, sensor_name, sensor_instance, keys_to_update):
        """Dedicated loop to read data from a single sensor."""
        while self.running:
            try:
                reading = sensor_instance.read()
                with self.readings_lock:
                    if sensor_name == 'pressure' and isinstance(reading, (list, tuple)) and len(reading) > 1:
                        # Handle BMP180 returning (temp, pressure)
                        self.last_readings['pressure'] = reading[1]
                    elif isinstance(keys_to_update, list): # For DHT
                        for key in keys_to_update:
                            self.last_readings[key] = reading.get(key)
                    else: # For other sensors
                        self.last_readings[keys_to_update] = reading
                
                # Sleep for 2 seconds as requested for stability
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error reading from {sensor_name}: {e}")
                with self.readings_lock:
                    if isinstance(keys_to_update, list):
                        for key in keys_to_update: self.last_readings[key] = None
                    else: self.last_readings[keys_to_update] = None
                time.sleep(5) # Longer sleep on error

    def get_latest_readings(self):
        """Get the latest sensor readings in a thread-safe way."""
        with self.readings_lock:
            self.last_readings['timestamp'] = datetime.now().isoformat()
            return self.last_readings.copy()

    def set_socketio(self, socketio_instance):
        """Set the SocketIO instance to use for real-time updates."""
        self.socketio = socketio_instance
        logger.info("SocketIO instance set for sensor controller")
    
    def set_app(self, app):
        """Set the Flask app instance for the sensor controller."""
        self.app = app
        with app.app_context():
            self._initialize_csv_logging(app.config)
            # Override UI update interval from config if present
            self.ui_update_interval = self.app.config.get('UI_UPDATE_INTERVAL', 0.5)
        logger.info("Flask app instance set for sensor controller")
    
    def _initialize_csv_logging(self, config):
        """Initialize CSV logging based on configuration."""
        logging_config = config.get('logging', {})
        self.csv_logging_enabled = logging_config.get('csv_enabled', False)
        logger.info(f"CSV logging enabled: {self.csv_logging_enabled}")
        
        if self.csv_logging_enabled:
            self.data_folder = os.path.expanduser(logging_config.get('data_folder', '~/sensor_data'))
            self.log_interval = logging_config.get('log_interval', 60)
            os.makedirs(self.data_folder, exist_ok=True)
            logger.info(f"CSV data folder set to: {self.data_folder}")

    def _broadcast_loop(self):
        """Continuously broadcasts the latest data to the UI."""
        logger.info(f"UI broadcast loop started. Interval: {self.ui_update_interval}s")
        while self.running:
            try:
                readings = self.get_latest_readings()
                statuses = self.get_sensor_statuses()
                
                if self.socketio:
                    self.socketio.emit('sensor_update', readings)
                    self.socketio.emit('sensor_status_update', statuses)
                
                self.socketio.sleep(self.ui_update_interval)
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                self.socketio.sleep(self.ui_update_interval)

    def _setup_csv_file(self):
        """Setup CSV file with headers including units."""
        today = datetime.now().strftime('%Y-%m-%d')
        csv_path = os.path.join(self.data_folder, f"{today}.csv")
        file_exists = os.path.isfile(csv_path)
        
        csv_file = open(csv_path, 'a', newline='')
        csv_writer = csv.writer(csv_file)
        
        if not file_exists:
            headers = ['Timestamp', 'Temperature (°C)', 'Humidity (%)', 'Soil Moisture (%)',
                       'Pressure (hPa)', 'Light Level (%)', 'Rain Level (%)']
            csv_writer.writerow(headers)
            logger.info(f"Created new CSV log file: {csv_path}")
        
        return csv_file, csv_writer

    def _log_data_to_csv(self):
        """Rounds sensor data, writes it to CSV, and logs it to the terminal."""
        if not self.csv_logging_enabled:
            return

        try:
            readings = self.get_latest_readings()
            
            # Data for logging to terminal
            log_payload = {'timestamp': readings.get('timestamp')}
            # Data for writing to CSV
            csv_row = [readings.get('timestamp')]

            # Process each sensor reading
            for key in ['temperature', 'humidity', 'soil_moisture', 'pressure', 'light', 'rain']:
                value = readings.get(key)
                if isinstance(value, (int, float)):
                    rounded_value = round(value, 2)
                    log_payload[key] = rounded_value
                    csv_row.append(rounded_value)
                else:
                    log_payload[key] = None
                    csv_row.append('') # Write empty string for None values in CSV

            # Write to CSV file
            csv_file, csv_writer = self._setup_csv_file()
            with csv_file:
                csv_writer.writerow(csv_row)
            
            # Log to terminal after successful write
            logger.info(f"Logged to CSV: {log_payload}")

        except Exception as e:
            logger.error(f"Failed to write to CSV: {e}")

    def _csv_logging_loop(self):
        """Periodically log data to CSV."""
        logger.info(f"CSV logging loop started with interval {self.log_interval}s")
        while self.running:
            try:
                self._log_data_to_csv()
                if self.socketio:
                    self.socketio.sleep(self.log_interval)
                else:
                    time.sleep(self.log_interval)
            except Exception as e:
                logger.error(f"Error in CSV logging loop: {e}")

    def get_sensor_statuses(self):
        """Get the connection status of each sensor."""
        statuses = {}
        with self.readings_lock:
            statuses['dht'] = 'Connected' if self.last_readings['temperature'] is not None else 'Disconnected'
            statuses['soil_moisture'] = 'Connected' if self.last_readings['soil_moisture'] is not None else 'Disconnected'
            statuses['pressure'] = 'Connected' if self.last_readings['pressure'] is not None else 'Disconnected'
            statuses['light'] = 'Connected' if self.last_readings['light'] is not None else 'Disconnected'
            statuses['rain'] = 'Connected' if self.last_readings['rain'] is not None else 'Disconnected'
        return statuses

    def start_monitoring(self):
        """Start all monitoring threads."""
        if self.running:
            logger.warning("Monitoring is already running.")
            return
            
        self.running = True

        # Map sensors to the keys they update in last_readings
        sensor_key_map = {
            'dht': ['temperature', 'humidity'],
            'soil_moisture': 'soil_moisture',
            'pressure': 'pressure',
            'light': 'light',
            'rain': 'rain'
        }

        # Start a thread for each active sensor
        for name, instance in self.sensors.items():
            if instance:
                keys = sensor_key_map[name]
                thread = threading.Thread(target=self._read_sensor_loop, args=(name, instance, keys))
                thread.daemon = True
                thread.start()
                self.sensor_threads.append(thread)
        
        # Start the UI broadcasting loop
        if self.socketio:
            self.socketio.start_background_task(self._broadcast_loop)
        
        # Start CSV logging loop
        if self.csv_logging_enabled:
            self.logging_thread = self.socketio.start_background_task(self._csv_logging_loop)

        logger.info("All sensor monitoring threads started.")

    def stop_monitoring(self):
        """Stop all monitoring threads."""
        if self.running:
            self.running = False
            # Threads are daemons, so they will exit automatically.
            # No need to join them, which can cause blocking issues.
            logger.info("Stopped all monitoring threads.")