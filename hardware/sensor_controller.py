"""
Module for integrating and managing hardware sensors.
"""
import time
import logging
import platform
import threading
from datetime import datetime
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

class SensorController:
    """Controller for managing all sensors and providing unified interface."""
    
    def __init__(self, simulation=False, ui_update_interval=1, db_update_interval=60):
        """Initialize the sensor controller.
        
        Args:
            simulation: Whether to simulate sensor readings
            ui_update_interval: Time between UI updates in seconds
            db_update_interval: Time between database updates in seconds
        """
        self.simulation = simulation
        self.ui_update_interval = ui_update_interval
        self.db_update_interval = db_update_interval
        self.dht_sensor = None
        self.soil_moisture_sensor = None
        self.water_level_sensor = None
        self.last_readings = {
            'temperature': 0,
            'humidity': 0,
            'soil_moisture': 0,
            'water_level': 0,
            'timestamp': datetime.now().isoformat()
        }
        self.running = False
        self.ui_thread = None
        self.db_thread = None
        self.last_db_update = 0  # Timestamp of last database update
        self.socketio = None  # Will be set later
        self.app = None  # Store the Flask app instance
        
        # Initialize sensors based on platform
        self._initialize_sensors()
        
        logger.info(f"Sensor controller initialized (simulation={simulation}, ui_interval={ui_update_interval}s, db_interval={db_update_interval}s)")
    
    def set_socketio(self, socketio_instance):
        """Set the SocketIO instance to use for real-time updates."""
        self.socketio = socketio_instance
        logger.info("SocketIO instance set for sensor controller")
    
    def set_app(self, app):
        """Set the Flask app instance for creating application contexts."""
        self.app = app
        logger.info("Flask app instance set for sensor controller")
    
    def _initialize_sensors(self):
        """Initialize the appropriate sensors based on platform."""
        if self.simulation or platform.system() != "Linux":
            logger.info("Using simulated sensors")
            from hardware.water_level import WaterLevelSensor
            self.water_level_sensor = WaterLevelSensor(simulation=True)
            
            # Import simulation modules for other sensors
            from hardware.sensor_simulation import SimulatedDHT, SimulatedSoilMoisture
            self.dht_sensor = SimulatedDHT()
            self.soil_moisture_sensor = SimulatedSoilMoisture()
        else:
            # We're on Linux, likely a Raspberry Pi
            logger.info("Initializing hardware sensors")
            
            # Initialize water level sensor
            from hardware.water_level import WaterLevelSensor
            self.water_level_sensor = WaterLevelSensor(pin=17, simulation=False)
            
            try:
                # Initialize DHT22 sensor
                import adafruit_dht
                import board
                self.dht_sensor = adafruit_dht.DHT22(board.D4)  # Using GPIO pin 4
                logger.info("DHT22 sensor initialized")
            except (ImportError, NotImplementedError) as e:
                logger.error(f"Failed to initialize DHT22 sensor: {e}")
                from hardware.sensor_simulation import SimulatedDHT
                self.dht_sensor = SimulatedDHT()
                logger.info("Using simulated DHT22 sensor instead")
            
            try:
                # Initialize soil moisture sensor using the existing module
                import hardware.soil_moisture as soil_moisture
                self.soil_moisture_sensor = soil_moisture
                logger.info("Soil moisture sensor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize soil moisture sensor: {e}")
                from hardware.sensor_simulation import SimulatedSoilMoisture
                self.soil_moisture_sensor = SimulatedSoilMoisture()
                logger.info("Using simulated soil moisture sensor instead")
    
    def start_monitoring(self):
        """Start monitoring sensors at configured intervals."""
        if self.running:
            return
        
        if not self.app:
            logger.error("Cannot start monitoring: Flask app not set. Call set_app() first.")
            return
            
        if not self.socketio:
            logger.warning("SocketIO not set. Real-time updates will not be available.")
        
        self.running = True
        
        # Start UI update thread
        self.ui_thread = threading.Thread(target=self._ui_monitoring_loop)
        self.ui_thread.daemon = True
        self.ui_thread.start()
        logger.info(f"UI sensor monitoring started with interval {self.ui_update_interval}s")
        
        # Start DB update thread
        self.db_thread = threading.Thread(target=self._db_monitoring_loop)
        self.db_thread.daemon = True
        self.db_thread.start()
        logger.info(f"Database sensor monitoring started with interval {self.db_update_interval}s")
    
    def stop_monitoring(self):
        """Stop the sensor monitoring threads."""
        self.running = False
        if self.ui_thread:
            self.ui_thread.join(timeout=1.0)
        if self.db_thread:
            self.db_thread.join(timeout=1.0)
        logger.info("Sensor monitoring stopped")
    
    def _ui_monitoring_loop(self):
        """Background thread for UI sensor readings."""
        while self.running:
            try:
                # Update sensor readings
                readings = self.update_readings()
                
                # Emit to UI via socketio if available
                if self.socketio:
                    self.socketio.emit('sensor_update', readings)
                else:
                    logger.warning("SocketIO not available for UI updates")
                
            except Exception as e:
                logger.error(f"Error in UI sensor monitoring loop: {e}")
            
            # Sleep for the UI update interval
            time.sleep(self.ui_update_interval)
    
    def _db_monitoring_loop(self):
        """Background thread for database sensor readings."""
        while self.running:
            try:
                # Check if it's time for a database update
                current_time = time.time()
                if current_time - self.last_db_update >= self.db_update_interval:
                    # Get the latest readings
                    readings = self.get_latest_readings()
                    
                    # Update the database - use app context
                    if self.app:
                        with self.app.app_context():
                            from weather.models import WeatherData
                            from shared.database import db
                            
                            # Create new weather data entry
                            weather_data = WeatherData(
                                temperature=readings.get('temperature', 0),
                                humidity=readings.get('humidity', 0),
                                soil_moisture=readings.get('soil_moisture', 0),
                                wind_speed=0,  # We don't have a wind sensor
                                pressure=0     # We don't have a pressure sensor
                            )
                            db.session.add(weather_data)
                            db.session.commit()
                            
                            # Emit via socketio if available
                            if self.socketio:
                                self.socketio.emit('weather_update', weather_data.to_dict())
                        
                        # Update the timestamp
                        self.last_db_update = current_time
                        logger.debug("Updated database with sensor readings")
                    else:
                        logger.error("Cannot update database: Flask app not set")
            except Exception as e:
                logger.error(f"Error in DB sensor monitoring loop: {e}")
            
            # Sleep for a short interval to check again
            time.sleep(1)
    
    def update_readings(self):
        """Update all sensor readings."""
        readings = {
            'timestamp': datetime.now().isoformat()
        }
        
        # Get temperature and humidity
        try:
            if hasattr(self.dht_sensor, 'temperature') and hasattr(self.dht_sensor, 'humidity'):
                # Adafruit DHT sensor
                readings['temperature'] = self.dht_sensor.temperature
                readings['humidity'] = self.dht_sensor.humidity
            elif hasattr(self.dht_sensor, 'read'):
                # Simulated sensor
                dht_data = self.dht_sensor.read()
                readings['temperature'] = dht_data['temperature']
                readings['humidity'] = dht_data['humidity']
            logger.debug(f"DHT readings: {readings['temperature']}°C, {readings['humidity']}%")
        except Exception as e:
            logger.error(f"Error reading DHT sensor: {e}")
            readings['temperature'] = self.last_readings.get('temperature', 0)
            readings['humidity'] = self.last_readings.get('humidity', 0)
        
        # Get soil moisture
        try:
            if hasattr(self.soil_moisture_sensor, 'read'):
                # Simulated sensor
                moisture_data = self.soil_moisture_sensor.read()
                readings['soil_moisture'] = moisture_data['moisture']
            else:
                # Hardware module
                raw_value = self.soil_moisture_sensor.read_adc(self.soil_moisture_sensor.MOISTURE_CHANNEL)
                readings['soil_moisture'] = self.soil_moisture_sensor.calculate_moisture_percentage(raw_value)
            logger.debug(f"Soil moisture: {readings['soil_moisture']}%")
        except Exception as e:
            logger.error(f"Error reading soil moisture sensor: {e}")
            readings['soil_moisture'] = self.last_readings.get('soil_moisture', 0)
        
        # Get water level
        try:
            readings['water_level'] = self.water_level_sensor.get_level()
            logger.debug(f"Water level: {readings['water_level']}%")
        except Exception as e:
            logger.error(f"Error reading water level sensor: {e}")
            readings['water_level'] = self.last_readings.get('water_level', 0)
        
        # Update last readings
        self.last_readings = readings
        return readings
    
    def get_latest_readings(self):
        """Get the most recent sensor readings."""
        return self.last_readings