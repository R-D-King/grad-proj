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

"""
Unified sensor controller for managing all sensors in the system.
"""
import time
import random
from datetime import datetime

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
                    self.sensors['dht'] = DHT22Sensor(pin=4)
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
    
    def _read_dht(self):
        """Read temperature and humidity from DHT sensor."""
        if 'dht' not in self.sensors or self.sensors['dht'] is None:
            if self.simulation:
                return {'temperature': random.uniform(18, 30), 'humidity': random.uniform(30, 80)}
            return {'temperature': None, 'humidity': None}
        
        try:
            return self.sensors['dht'].read()
        except Exception as e:
            print(f"Error reading DHT sensor: {e}")
            return {'temperature': None, 'humidity': None}
    
    def _read_soil_moisture(self):
        """Read soil moisture level."""
        if 'soil_moisture' not in self.sensors or self.sensors['soil_moisture'] is None:
            if self.simulation:
                return random.uniform(0, 100)
            return None
        
        try:
            return self.sensors['soil_moisture'].read()
        except Exception as e:
            print(f"Error reading soil moisture sensor: {e}")
            return None
    
    def _read_water_level(self):
        """Read water level."""
        if 'water_level' not in self.sensors or self.sensors['water_level'] is None:
            if self.simulation:
                return random.uniform(0, 100)
            return None
        
        try:
            return self.sensors['water_level'].read()
        except Exception as e:
            print(f"Error reading water level sensor: {e}")
            return None
    
    def _read_pressure(self):
        """Read barometric pressure."""
        if 'pressure' not in self.sensors or self.sensors['pressure'] is None:
            if self.simulation:
                return random.uniform(980, 1050)
            return None
        
        try:
            # For BMP180, read() returns a tuple (temperature, pressure, altitude)
            # We need to extract just the pressure value (second element)
            readings = self.sensors['pressure'].read()
            if isinstance(readings, tuple) and len(readings) >= 2:
                return readings[1]  # Extract pressure from tuple
            return readings
        except Exception as e:
            print(f"Error reading pressure sensor: {e}")
            return None
    
    def _read_light(self):
        """Read light level."""
        if 'light' not in self.sensors or self.sensors['light'] is None:
            if self.simulation:
                return random.uniform(0, 100)
            return None
        
        try:
            # For LDR sensor, we need to call get_light_percentage()
            if hasattr(self.sensors['light'], 'get_light_percentage'):
                return self.sensors['light'].get_light_percentage()
            return self.sensors['light'].read()
        except Exception as e:
            print(f"Error reading light sensor: {e}")
            return None
    
    def _read_rain(self):
        """Read rain level."""
        if 'rain' not in self.sensors or self.sensors['rain'] is None:
            if self.simulation:
                return random.uniform(0, 100)
            return None
        
        try:
            # For rain sensor, we need to call get_rain_percentage() if available
            if hasattr(self.sensors['rain'], 'get_rain_percentage'):
                return self.sensors['rain'].get_rain_percentage()
            return self.sensors['rain'].read()
        except Exception as e:
            print(f"Error reading rain sensor: {e}")
            return None
    
    def read_all(self):
        """Read all sensor values and return as a dictionary."""
        dht_data = self._read_dht()
        
        readings = {
            'temperature': dht_data.get('temperature'),
            'humidity': dht_data.get('humidity'),
            'soil_moisture': self._read_soil_moisture(),
            'water_level': self._read_water_level(),
            'pressure': self._read_pressure(),
            'light': self._read_light(),
            'rain': self._read_rain(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.last_readings = readings
        return readings
    
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
        """Background thread for updating database with sensor readings."""
        while self.running:
            try:
                # Get current time
                now = time.time()
                
                # Check if it's time to update the database
                if now - self.last_db_update >= self.db_update_interval:
                    # Get latest readings
                    readings = self.read_all()
                    
                    # Update database with readings
                    with self.app.app_context():
                        from weather.controllers import update_weather_data
                        
                        # Handle None values by providing default values
                        update_data = {
                            'temperature': readings.get('temperature', 0) if readings.get('temperature') is not None else 0,
                            'humidity': readings.get('humidity', 0) if readings.get('humidity') is not None else 0,
                            'soil_moisture': readings.get('soil_moisture', 0) if readings.get('soil_moisture') is not None else 0,
                            'pressure': readings.get('pressure', 0) if readings.get('pressure') is not None else 0,
                            'light': readings.get('light', 0) if readings.get('light') is not None else 0,
                            'rain': readings.get('rain', 0) if readings.get('rain') is not None else 0
                        }
                        
                        # Log what we're updating
                        logger.info(f"Updating database with sensor readings: {update_data}")
                        
                        # Update the database
                        update_weather_data(update_data)
                    
                    # Update last database update time
                    self.last_db_update = now
            except Exception as e:
                logger.error(f"Error in database monitoring loop: {e}")
            
            # Sleep for a short time to avoid high CPU usage
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
                temp = self.dht_sensor.temperature
                humid = self.dht_sensor.humidity
                readings['temperature'] = float(temp) if temp is not None else None
                readings['humidity'] = float(humid) if humid is not None else None
            elif hasattr(self.dht_sensor, 'read'):
                # Simulated sensor
                dht_data = self.dht_sensor.read()
                readings['temperature'] = float(dht_data['temperature']) if dht_data['temperature'] is not None else None
                readings['humidity'] = float(dht_data['humidity']) if dht_data['humidity'] is not None else None
            logger.debug(f"DHT readings: {readings.get('temperature')}°C, {readings.get('humidity')}%")
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
        """Get the latest sensor readings."""
        # If we don't have any readings yet, update them
        if not self.last_readings:
            return self.update_readings()
        return self.last_readings
        readings = {
            'temperature': 0,
            'humidity': 0,
            'soil_moisture': 0,
            'water_level': 0,
            'pressure': 0,
            'light_percentage': 0
        }
        
        # Get temperature and humidity from DHT22
        try:
            temperature, humidity = self._read_dht()
            readings['temperature'] = temperature
            readings['humidity'] = humidity
        except Exception as e:
            logger.error(f"Error reading DHT sensor: {e}")
        
        # Get soil moisture
        try:
            soil_moisture = self._read_soil_moisture()
            readings['soil_moisture'] = soil_moisture
        except Exception as e:
            logger.error(f"Error reading soil moisture sensor: {e}")
        
        # Get water level
        try:
            water_level = self._read_water_level()
            readings['water_level'] = water_level
        except Exception as e:
            logger.error(f"Error reading water level sensor: {e}")
        
        # Get pressure from BMP180
        try:
            pressure = self._read_pressure()
            readings['pressure'] = pressure
        except Exception as e:
            logger.error(f"Error reading BMP180 sensor: {e}")
        
        # Get light percentage from LDR
        try:
            light_percentage = self._read_light_percentage()
            readings['light_percentage'] = light_percentage
        except Exception as e:
            logger.error(f"Error reading LDR sensor: {e}")
        
        return readings
    
    def _read_pressure(self):
        """Read pressure from BMP180 sensor."""
        if hasattr(self, 'bmp180_sensor'):
            try:
                # If we already have a BMP180 sensor instance, use it
                _, pressure, _ = self.bmp180_sensor.read()
                return pressure
            except Exception as e:
                logger.error(f"Error reading from existing BMP180 sensor: {e}")
        
        # If we don't have a BMP180 sensor instance or there was an error, try to create one
        try:
            from hardware.bmp180 import BMP180Sensor
            
            # Get configuration if available
            bmp_config = {}
            if hasattr(self, 'app'):
                with self.app.app_context():
                    bmp_config = self.app.config.get('hardware', {}).get('sensors', {}).get('pins', {}).get('bmp180', {})
            
            # Extract parameters with defaults
            i2c_address = bmp_config.get('i2c_address', 0x77)
            if isinstance(i2c_address, str) and i2c_address.startswith('0x'):
                i2c_address = int(i2c_address, 16)
            i2c_bus = bmp_config.get('i2c_bus', 1)
            
            # Create BMP180 sensor instance
            self.bmp180_sensor = BMP180Sensor(
                i2c_address=i2c_address,
                i2c_bus=i2c_bus,
                simulation=self.simulation
            )
            
            # Read from the sensor
            _, pressure, _ = self.bmp180_sensor.read()
            return pressure
        except Exception as e:
            logger.error(f"Error initializing BMP180 sensor: {e}")
            return 0
    
    def _read_light_percentage(self):
        """Read light percentage from LDR sensor."""
        if hasattr(self, 'ldr_sensor'):
            try:
                # If we already have an LDR sensor instance, use it
                return self.ldr_sensor.get_light_percentage()
            except Exception as e:
                logger.error(f"Error reading from existing LDR sensor: {e}")
        
        # If we don't have an LDR sensor instance or there was an error, try to create one
        try:
            from hardware.ldr_aout import LDRSensor
            
            # Get configuration if available
            ldr_config = {}
            if hasattr(self, 'app'):
                with self.app.app_context():
                    ldr_config = self.app.config.get('hardware', {}).get('sensors', {}).get('pins', {}).get('ldr', {})
            
            # Extract parameters with defaults
            channel = ldr_config.get('channel', 1)
            min_value = ldr_config.get('min_value', 0)
            max_value = ldr_config.get('max_value', 1023)
            
            # Create LDR sensor instance
            self.ldr_sensor = LDRSensor(
                channel=channel,
                min_value=min_value,
                max_value=max_value,
                simulation=self.simulation
            )
            
            # Read from the sensor
            return self.ldr_sensor.get_light_percentage()
        except Exception as e:
            logger.error(f"Error initializing LDR sensor: {e}")