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
import random

# Set up logging
logger = logging.getLogger(__name__)

class SensorController:
    """Controller for managing all sensors in the system."""
    
    def __init__(self, simulation=False):
        """Initialize the sensor controller.
        
        Args:
            simulation (bool): Whether to use simulated sensors
        """
        self.simulation = simulation
        self.sensors = {}
        self.last_readings = {}
        self.running = False  # Initialize the running attribute
        self.socketio = None  # Initialize socketio
        self.app = None       # Initialize app
        self.ui_update_interval = 1  # Default value
        self.db_update_interval = 60  # Default value
        self.last_ui_update = 0
        self.last_db_update = 0
        
        self.dht_pin = 26  # Default pin
        
        # CSV logging attributes
        self.csv_logging_enabled = False
        self.data_folder = None
        self.log_interval = 60
        self.timestamp_format = '%Y-%m-%d %H:%M:%S'
        self.csv_file = None
        self.csv_writer = None
        self.last_log_day = None
        self.validation_enabled = True
        self.validation_limits = {}
        self.logging_thread = None
        
        # Initialize sensors based on simulation mode
        self._initialize_sensors()
    
    def _initialize_sensors(self):
        """Initialize all sensors based on simulation mode."""
        try:
            if self.simulation:
                from .sensor_simulation import SimulatedSensor
                self.sensors['dht'] = SimulatedSensor('dht', min_value=0, max_value=40, default_value=22)
                self.sensors['soil_moisture'] = SimulatedSensor('soil_moisture', min_value=0, max_value=100, default_value=50)
                self.sensors['water_level'] = SimulatedSensor('water_level', min_value=0, max_value=100, default_value=75)
                self.sensors['pressure'] = SimulatedSensor('pressure', min_value=980, max_value=1050, default_value=1013)
                self.sensors['light'] = SimulatedSensor('light', min_value=0, max_value=100, default_value=60)
                self.sensors['rain'] = SimulatedSensor('rain', min_value=0, max_value=100, default_value=10)
            else:
                # Initialize hardware sensors
                try:
                    from .dht22 import DHT22Sensor
                    self.sensors['dht'] = DHT22Sensor(pin=26)
                except Exception as e:
                    print(f"Error initializing DHT22 sensor: {e}")
                    self.sensors['dht'] = None
                
                try:
                    from .soil_moisture import SoilMoistureSensor
                    self.sensors['soil_moisture'] = SoilMoistureSensor()
                except Exception as e:
                    print(f"Error initializing soil moisture sensor: {e}")
                    self.sensors['soil_moisture'] = None
                
                try:
                    from .water_level import WaterLevelSensor
                    self.sensors['water_level'] = WaterLevelSensor(pin=17)
                except Exception as e:
                    print(f"Error initializing water level sensor: {e}")
                    self.sensors['water_level'] = None
                
                try:
                    from .bmp180 import BMP180Sensor
                    self.sensors['pressure'] = BMP180Sensor()
                except Exception as e:
                    print(f"Error initializing BMP180 sensor: {e}")
                    self.sensors['pressure'] = None
                
                try:
                    from .ldr_aout import LDRSensor
                    self.sensors['light'] = LDRSensor()
                except Exception as e:
                    print(f"Error initializing LDR sensor: {e}")
                    self.sensors['light'] = None
                
                try:
                    from .rain_aout import RainSensor
                    self.sensors['rain'] = RainSensor()
                except Exception as e:
                    print(f"Error initializing rain sensor: {e}")
                    self.sensors['rain'] = None
        except Exception as e:
            print(f"Error initializing sensors: {e}")
    
    def update_readings(self):
        """Update all sensor readings and return as a dictionary."""
        readings = {'timestamp': datetime.now().isoformat()}

        # Temperature and Humidity
        try:
            dht_sensor = self.sensors.get('dht')
            if dht_sensor:
                if hasattr(dht_sensor, 'temperature') and hasattr(dht_sensor, 'humidity'): # adafruit_dht
                    temp = dht_sensor.temperature
                    humid = dht_sensor.humidity
                    readings['temperature'] = float(temp) if temp is not None else None
                    readings['humidity'] = float(humid) if humid is not None else None
                elif hasattr(dht_sensor, 'read'): # Other DHT libraries or simulation
                    dht_data = dht_sensor.read()
                    readings['temperature'] = float(dht_data['temperature']) if dht_data and dht_data.get('temperature') is not None else None
                    readings['humidity'] = float(dht_data['humidity']) if dht_data and dht_data.get('humidity') is not None else None
                logger.debug(f"DHT readings: {readings.get('temperature')}°C, {readings.get('humidity')}%")
            else:
                raise ValueError("DHT sensor not initialized")
        except Exception as e:
            logger.error(f"Error reading DHT sensor: {e}")
            readings.update({'temperature': None, 'humidity': None})
            if self.simulation:
                readings['temperature'] = round(random.uniform(18.0, 25.0), 1)
                readings['humidity'] = round(random.uniform(40.0, 60.0), 1)

        # Soil Moisture
        try:
            soil_sensor = self.sensors.get('soil_moisture')
            if soil_sensor:
                value = soil_sensor.read()
                readings['soil_moisture'] = round(value, 2) if value is not None else None
                logger.debug(f"Soil moisture: {readings.get('soil_moisture')}%")
            else:
                raise ValueError("Soil moisture sensor not initialized")
        except Exception as e:
            logger.error(f"Error reading soil moisture sensor: {e}")
            readings['soil_moisture'] = None
            if self.simulation:
                readings['soil_moisture'] = round(random.uniform(30.0, 70.0), 2)

        # Water Level
        try:
            water_level_sensor = self.sensors.get('water_level')
            if water_level_sensor:
                if hasattr(water_level_sensor, 'get_level'):
                    readings['water_level'] = round(water_level_sensor.get_level(), 2)
                else:
                    readings['water_level'] = round(water_level_sensor.read(), 2)
                logger.debug(f"Water level: {readings.get('water_level')}%")
            else:
                raise ValueError("Water level sensor not initialized")
        except Exception as e:
            logger.error(f"Error reading water level sensor: {e}")
            readings['water_level'] = None
            if self.simulation:
                readings['water_level'] = round(random.uniform(50.0, 90.0), 2)

        # Pressure
        try:
            pressure_sensor = self.sensors.get('pressure')
            if pressure_sensor:
                pressure_data = pressure_sensor.read()
                if isinstance(pressure_data, tuple) and len(pressure_data) >= 2:
                    readings['pressure'] = pressure_data[1]
                else:
                    readings['pressure'] = pressure_data
                logger.debug(f"Pressure: {readings.get('pressure')} hPa")
            else:
                raise ValueError("Pressure sensor not initialized")
        except Exception as e:
            logger.error(f"Error reading pressure sensor: {e}")
            readings['pressure'] = None
            if self.simulation:
                readings['pressure'] = random.uniform(980, 1050)

        # Light
        try:
            light_sensor = self.sensors.get('light')
            if light_sensor:
                if hasattr(light_sensor, 'get_light_percentage'):
                    readings['light'] = light_sensor.get_light_percentage()
                else:
                    readings['light'] = light_sensor.read()
                logger.debug(f"Light: {readings.get('light')}%")
            else:
                raise ValueError("Light sensor not initialized")
        except Exception as e:
            logger.error(f"Error reading light sensor: {e}")
            readings['light'] = None
            if self.simulation:
                readings['light'] = random.uniform(0, 100)

        # Rain
        try:
            rain_sensor = self.sensors.get('rain')
            if rain_sensor:
                if hasattr(rain_sensor, 'get_rain_percentage'):
                    readings['rain'] = rain_sensor.get_rain_percentage()
                else:
                    readings['rain'] = rain_sensor.read()
                logger.debug(f"Rain: {readings.get('rain')}%")
            else:
                raise ValueError("Rain sensor not initialized")
        except Exception as e:
            logger.error(f"Error reading rain sensor: {e}")
            readings['rain'] = None
            if self.simulation:
                readings['rain'] = random.uniform(0, 100)
        
        self.last_readings = readings
        return readings

    def get_latest_readings(self):
        """Get the latest sensor readings."""
        if not self.last_readings:
            return self.update_readings()
        return self.last_readings

    def set_socketio(self, socketio_instance):
        """Set the SocketIO instance to use for real-time updates."""
        self.socketio = socketio_instance
        logger.info("SocketIO instance set for sensor controller")
    
    def set_app(self, app):
        """Set the Flask app instance for the sensor controller."""
        self.app = app
        
        with app.app_context():
            try:
                dht_pin = app.config.get('hardware', {}).get('sensors', {}).get('pins', {}).get('dht22', 26)
                
                if dht_pin != self.dht_pin and not self.simulation and platform.system() == "Linux":
                    logger.info(f"Updating DHT pin from {self.dht_pin} to {dht_pin}")
                    self.dht_pin = dht_pin
                    
                    try:
                        import adafruit_dht
                        import board
                        pin_map = {
                            4: board.D4, 17: board.D17, 18: board.D18, 21: board.D21,
                            22: board.D22, 23: board.D23, 24: board.D24, 25: board.D25,
                            26: board.D26,
                        }
                        pin = pin_map.get(dht_pin, board.D26)
                        
                        old_sensor = self.sensors.get('dht')
                        if old_sensor and hasattr(old_sensor, 'exit'):
                            old_sensor.exit()
                            
                        self.sensors['dht'] = adafruit_dht.DHT22(pin)
                        logger.info(f"DHT22 sensor reinitialized on pin {dht_pin}")
                    except Exception as e:
                        logger.error(f"Failed to reinitialize DHT22 sensor: {e}")
                        
                self._initialize_csv_logging(app.config)
            except Exception as e:
                logger.warning(f"Could not get DHT pin from config: {e}")
        logger.info("Flask app instance set for sensor controller")
    
    def _initialize_csv_logging(self, config):
        """Initialize CSV logging based on configuration."""
        try:
            logging_config = config.get('logging', {})
            if logging_config is None:
                logging_config = {}
                logger.warning("Logging configuration not found, using defaults")
            
            self.csv_logging_enabled = logging_config.get('csv_enabled', False)
            
            if not self.csv_logging_enabled:
                logger.info("CSV logging is disabled")
                return
                
            self.data_folder = os.path.expanduser(logging_config.get('data_folder', '~/sensor_data'))
            self.log_interval = logging_config.get('log_interval', 60)
            self.timestamp_format = logging_config.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
            
            os.makedirs(self.data_folder, exist_ok=True)
            
            self.csv_file = None
            self.csv_writer = None
            self.last_log_day = None
            
            self.validation_enabled = logging_config.get('validation_enabled', True)
            self.validation_limits = logging_config.get('validation_limits', {
                'temperature': {'min': -10.0, 'max': 50.0}, 'humidity': {'min': 0.0, 'max': 100.0},
                'soil_moisture': {'min': 0.0, 'max': 100.0}, 'pressure': {'min': 900.0, 'max': 1100.0},
                'light': {'min': 0.0, 'max': 100.0}, 'rain': {'min': 0.0, 'max': 100.0}
            })
            
            if self.running:
                self.logging_thread = threading.Thread(target=self._csv_logging_loop)
                self.logging_thread.daemon = True
                self.logging_thread.start()
                logger.info(f"CSV logging initialized with interval {self.log_interval}s")
        except Exception as e:
            logger.error(f"Error initializing CSV logging: {e}")
            self.csv_logging_enabled = False
    
    def _setup_csv_file(self):
        """Setup CSV file with headers including units."""
        today = datetime.now().strftime('%Y-%m-%d')
        csv_path = os.path.join(self.data_folder, f"{today}.csv")
        file_exists = os.path.isfile(csv_path)
        csv_file = open(csv_path, 'a', newline='')
        csv_writer = csv.writer(csv_file)
        
        if not file_exists:
            headers = [
                'Timestamp', 'Temperature (°C)', 'Humidity (%)', 'Soil Moisture (%)',
                'Water Level (%)', 'Pressure (hPa)', 'Light Level (%)', 'Rain Level (%)'
            ]
            csv_writer.writerow(headers)
        
        return csv_file, csv_writer
    
    def _log_data_to_csv(self, data):
        """Write sensor data to CSV file."""
        timestamp = datetime.now().strftime(self.timestamp_format)
        row = [
            timestamp,
            round(data.get('temperature', 0), 1) if data.get('temperature') is not None else None,
            round(data.get('humidity', 0), 1) if data.get('humidity') is not None else None,
            round(data.get('soil_moisture', 0), 2) if data.get('soil_moisture') is not None else None,
            round(data.get('water_level', 0), 2) if data.get('water_level') is not None else None,
            round(data.get('pressure', 0), 1) if data.get('pressure') is not None else None,
            round(data.get('light', 0), 2) if data.get('light') is not None else None,
            round(data.get('rain', 0), 2) if data.get('rain') is not None else None
        ]
        self.csv_writer.writerow(row)
        self.csv_file.flush()
    
    def _validate_readings(self, readings):
        """Validate sensor readings against configured limits."""
        if not self.validation_enabled:
            return
            
        if readings.get('temperature') is not None:
            temp_limits = self.validation_limits.get('temperature', {'min': -10.0, 'max': 50.0})
            if not (temp_limits['min'] <= readings['temperature'] <= temp_limits['max']):
                logger.warning(f"Temperature {readings['temperature']}°C outside valid range")
        
        if readings.get('humidity') is not None:
            humid_limits = self.validation_limits.get('humidity', {'min': 0.0, 'max': 100.0})
            if not (humid_limits['min'] <= readings['humidity'] <= humid_limits['max']):
                logger.warning(f"Humidity {readings['humidity']}% outside valid range")
        
        if readings.get('soil_moisture') is not None:
            soil_limits = self.validation_limits.get('soil_moisture', {'min': 0.0, 'max': 100.0})
            if not (soil_limits['min'] <= readings['soil_moisture'] <= soil_limits['max']):
                logger.warning(f"Soil moisture {readings['soil_moisture']}% outside valid range")
        
        if readings.get('pressure') is not None:
            pressure_limits = self.validation_limits.get('pressure', {'min': 900.0, 'max': 1100.0})
            if not (pressure_limits['min'] <= readings['pressure'] <= pressure_limits['max']):
                logger.warning(f"Pressure {readings['pressure']}hPa outside valid range")
    
    def _csv_logging_loop(self):
        """Background thread for logging sensor data to CSV."""
        while self.running:
            try:
                today = datetime.now().day
                if self.last_log_day != today:
                    if self.csv_file:
                        self.csv_file.close()
                    self.csv_file, self.csv_writer = self._setup_csv_file()
                    self.last_log_day = today
                    logger.info(f"Created new log file for {datetime.now().strftime('%Y-%m-%d')}")
                
                readings = self.update_readings()
                self._validate_readings(readings)
                self._log_data_to_csv(readings)
                logger.info(f"Sensor data logged to CSV file.")
                
                time.sleep(self.log_interval)
            except Exception as e:
                logger.error(f"Error in CSV logging loop: {e}")
                time.sleep(10)
    
    def get_sensor_status(self):
        """Get the status of all sensors (real vs simulated)."""
        status = {}
        if not self.sensors:
            return {}

        try:
            from .sensor_simulation import SimulatedSensor
            for name, sensor_obj in self.sensors.items():
                is_simulated = isinstance(sensor_obj, SimulatedSensor) or sensor_obj is None
                status[f'{name}_simulated'] = is_simulated
        except ImportError:
             for name in self.sensors:
                status[f'{name}_simulated'] = self.simulation

        status['water_simulated'] = True
        return status
    
    def start_monitoring(self):
        """Start monitoring sensors at configured intervals."""
        if self.running: return
        if not self.app:
            logger.error("Cannot start monitoring: Flask app not set. Call set_app() first.")
            return
        if not self.socketio:
            logger.warning("SocketIO not set. Real-time updates will not be available.")
        
        self.running = True
        
        if self.csv_logging_enabled and not self.logging_thread:
            self.logging_thread = threading.Thread(target=self._csv_logging_loop)
            self.logging_thread.daemon = True
            self.logging_thread.start()
            logger.info(f"CSV logging started with interval {self.log_interval}s")
        
        self.ui_thread = threading.Thread(target=self._ui_monitoring_loop)
        self.ui_thread.daemon = True
        self.ui_thread.start()
        logger.info(f"UI sensor monitoring started with interval {self.ui_update_interval}s")
        
        self.db_thread = threading.Thread(target=self._db_monitoring_loop)
        self.db_thread.daemon = True
        self.db_thread.start()
        logger.info(f"Database sensor monitoring started with interval {self.db_update_interval}s")
    
    def stop_monitoring(self):
        """Stop the sensor monitoring threads."""
        self.running = False
        if hasattr(self, 'ui_thread') and self.ui_thread.is_alive():
            self.ui_thread.join(timeout=1.0)
        if hasattr(self, 'db_thread') and self.db_thread.is_alive():
            self.db_thread.join(timeout=1.0)
        if hasattr(self, 'logging_thread') and self.logging_thread.is_alive():
            self.logging_thread.join(timeout=1.0)
        logger.info("Sensor monitoring stopped")
    
    def _ui_monitoring_loop(self):
        """Background thread for UI sensor readings."""
        while self.running:
            try:
                readings = self.update_readings()
                if self.socketio:
                    self.socketio.emit('sensor_update', readings)
                else:
                    logger.warning("SocketIO not available for UI updates")
            except Exception as e:
                logger.error(f"Error in UI sensor monitoring loop: {e}")
            time.sleep(self.ui_update_interval)
    
    def _db_monitoring_loop(self):
        """Background thread for updating database with sensor readings."""
        while self.running:
            try:
                now = time.time()
                if now - self.last_db_update >= self.db_update_interval:
                    readings = self.update_readings()
                    with self.app.app_context():
                        from weather.controllers import update_weather_data
                        update_data = {
                            'temperature': readings.get('temperature', 0) if readings.get('temperature') is not None else 0,
                            'humidity': readings.get('humidity', 0) if readings.get('humidity') is not None else 0,
                            'soil_moisture': readings.get('soil_moisture', 0) if readings.get('soil_moisture') is not None else 0,
                            'pressure': readings.get('pressure', 0) if readings.get('pressure') is not None else 0,
                            'light': readings.get('light', 0) if readings.get('light') is not None else 0,
                            'rain': readings.get('rain', 0) if readings.get('rain') is not None else 0
                        }
                        logger.info(f"Updating database with sensor readings: {update_data}")
                        update_weather_data(update_data)
                    self.last_db_update = now
            except Exception as e:
                logger.error(f"Error in database monitoring loop: {e}")
            time.sleep(1)
