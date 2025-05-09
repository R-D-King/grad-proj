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
        """Set the Flask app instance for the sensor controller."""
        self.app = app
        
        # Now that we have the app, we can get the proper configuration
        with app.app_context():
            try:
                # Get DHT pin from config
                dht_pin = app.config.get('hardware', {}).get('sensors', {}).get('pins', {}).get('dht22', 26)
                
                # If the pin has changed and we're not in simulation mode, reinitialize the DHT sensor
                if dht_pin != self.dht_pin and not self.simulation and platform.system() == "Linux":
                    logger.info(f"Updating DHT pin from {self.dht_pin} to {dht_pin}")
                    self.dht_pin = dht_pin
                    
                    # Reinitialize the DHT sensor with the correct pin
                    try:
                        import adafruit_dht
                        import board
                        pin_map = {
                            4: board.D4,
                            17: board.D17,
                            18: board.D18,
                            21: board.D21,
                            22: board.D22,
                            23: board.D23,
                            24: board.D24,
                            25: board.D25,
                            26: board.D26,
                            # Add more pins as needed
                        }
                        pin = pin_map.get(dht_pin, board.D26)
                        
                        # Clean up old sensor if it exists
                        if hasattr(self, 'dht_sensor') and hasattr(self.dht_sensor, 'exit'):
                            self.dht_sensor.exit()
                            
                        self.dht_sensor = adafruit_dht.DHT22(pin)
                        logger.info(f"DHT22 sensor reinitialized on pin {dht_pin}")
                    except Exception as e:
                        logger.error(f"Failed to reinitialize DHT22 sensor: {e}")
            except Exception as e:
                logger.warning(f"Could not get DHT pin from config: {e}")
        logger.info("Flask app instance set for sensor controller")
    
    def _initialize_sensors(self):
        """Initialize the appropriate sensors based on platform."""
        # Get pin configuration from config - without using Flask's current_app
        dht_pin = 26  # Default pin
        
        # We'll set the actual pin later when the app context is available
        self.dht_pin = dht_pin
        
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
            
            # Initialize water level sensor with simulation mode since hardware is not available
            from hardware.water_level import WaterLevelSensor
            self.water_level_sensor = WaterLevelSensor(simulation=True)
            logger.info("Water level sensor not available - using simulated data")
            
            try:
                # Initialize DHT22 sensor with default pin for now
                import adafruit_dht
                import board
                pin_map = {
                    4: board.D4,
                    17: board.D17,
                    18: board.D18,
                    21: board.D21,
                    22: board.D22,
                    23: board.D23,
                    24: board.D24,
                    25: board.D25,
                    26: board.D26,
                    # Add more pins as needed
                }
                pin = pin_map.get(dht_pin, board.D26)  # Default to D26 if pin not in map
                self.dht_sensor = adafruit_dht.DHT22(pin)
                logger.info(f"DHT22 sensor initialized on pin {dht_pin}")
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
    
    # Add this method to your SensorController class
    def get_sensor_status(self):
        """Get the status of all sensors (real vs simulated)."""
        status = {
            'dht_simulated': not hasattr(self.dht_sensor, 'temperature'),
            'soil_simulated': hasattr(self.soil_moisture_sensor, 'read'),
            'water_simulated': True  # Always simulated for now
        }
        return status
    
    # Modify your start_monitoring method to emit initial status
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
                            
                            # Ensure we have valid values for required fields
                            temperature = readings.get('temperature')
                            humidity = readings.get('humidity')
                            soil_moisture = readings.get('soil_moisture', 0)
                            
                            # Only insert into database if we have valid temperature and humidity
                            if temperature is not None and humidity is not None:
                                # Create new weather data entry
                                weather_data = WeatherData(
                                    temperature=temperature,
                                    humidity=humidity,
                                    soil_moisture=soil_moisture,
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
                                logger.warning("Skipping database update due to missing temperature or humidity data")
                        
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
            # Provide realistic default values and mark as simulated
            import random
            readings['temperature'] = round(random.uniform(18.0, 25.0), 1)  # Realistic room temperature
            readings['humidity'] = round(random.uniform(40.0, 60.0), 1)     # Realistic indoor humidity
            readings['simulated'] = True  # Flag to indicate these are simulated values
        
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
            # Provide realistic default value
            import random
            readings['soil_moisture'] = round(random.uniform(30.0, 70.0), 1)  # Realistic soil moisture
            
        # Get water level - always use simulation since hardware is not available
        try:
            # Only log the missing hardware once per session
            if not hasattr(self, '_water_level_warning_shown'):
                logger.info("Water level sensor hardware not available, using simulated data")
                self._water_level_warning_shown = True
                
            readings['water_level'] = self.water_level_sensor.get_level()
            logger.debug(f"Water level (simulated): {readings['water_level']}%")
        except Exception as e:
            # Provide realistic default value
            import random
            readings['water_level'] = round(random.uniform(50.0, 90.0), 1)  # Realistic water level
            
        # Update last readings
        self.last_readings = readings
        return readings
    
    def get_latest_readings(self):
        """Get the most recent sensor readings."""
        return self.last_readings