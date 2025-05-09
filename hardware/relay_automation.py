"""
Relay automation module for controlling relays based on sensor readings.
"""
import json
import logging
import time
import os
import threading
from pathlib import Path

from .relay import Relay

logger = logging.getLogger(__name__)

class RelayAutomation:
    """Class for automating relay control based on sensor readings."""
    
    def __init__(self, config_path=None, sensor_controller=None, simulation=False):
        """Initialize the relay automation controller.
        
        Args:
            config_path (str): Path to the relay automation configuration file
            sensor_controller: SensorController instance to get sensor readings
            simulation (bool): Whether to use simulation mode
        """
        self.config_path = config_path or os.path.join(
            Path(__file__).parent.parent, 'config', 'relay_automation.json'
        )
        self.sensor_controller = sensor_controller
        self.simulation = simulation
        self.relays = {}
        self.rules = []
        self.running = False
        self.thread = None
        self.last_activations = {}  # Track when rules were last activated
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load the relay automation configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Get global settings
            self.check_interval = config.get('global_settings', {}).get('check_interval', 60)
            self.simulation = config.get('global_settings', {}).get('simulation_mode', self.simulation)
            
            # Configure logging
            log_level = config.get('global_settings', {}).get('logging_level', 'INFO')
            logging.getLogger(__name__).setLevel(getattr(logging, log_level))
            
            # Initialize relays and rules
            self.rules = config.get('rules', [])
            self._initialize_relays()
            
            logger.info(f"Loaded relay automation configuration with {len(self.rules)} rules")
        except Exception as e:
            logger.error(f"Error loading relay automation configuration: {e}")
            # Set default values
            self.check_interval = 60
            self.rules = []
    
    def _initialize_relays(self):
        """Initialize relays from configuration."""
        # Clean up existing relays
        for relay in self.relays.values():
            relay.cleanup()
        
        self.relays = {}
        
        # Create new relays
        for rule in self.rules:
            relay_config = rule.get('relay', {})
            pin = relay_config.get('pin')
            name = relay_config.get('name')
            
            if pin is not None and pin not in self.relays:
                self.relays[pin] = Relay(pin=pin, name=name, simulation=self.simulation)
                logger.info(f"Initialized relay {name} on pin {pin}")
    
    def start(self):
        """Start the relay automation controller."""
        if self.running:
            logger.warning("Relay automation is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.thread.start()
        logger.info("Relay automation started")
    
    def stop(self):
        """Stop the relay automation controller."""
        if not self.running:
            logger.warning("Relay automation is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        
        # Turn off all relays
        for relay in self.relays.values():
            relay.turn_off()
        
        logger.info("Relay automation stopped")
    
    def _automation_loop(self):
        """Main automation loop."""
        while self.running:
            try:
                self._check_rules()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in automation loop: {e}")
                time.sleep(5)  # Short delay before retrying
    
    def _check_rules(self):
        """Check all rules and control relays accordingly."""
        if not self.sensor_controller:
            logger.warning("No sensor controller available, skipping rule checks")
            return
        
        current_time = time.time()
        
        for rule in self.rules:
            rule_name = rule.get('name', 'Unnamed Rule')
            relay_config = rule.get('relay', {})
            pin = relay_config.get('pin')
            
            if pin not in self.relays:
                logger.warning(f"Relay pin {pin} for rule '{rule_name}' not found")
                continue
            
            relay = self.relays[pin]
            
            # Check cooldown period
            last_activation = self.last_activations.get(rule_name, 0)
            cooldown_period = rule.get('actions', {}).get('cooldown_period', 0)
            
            if current_time - last_activation < cooldown_period:
                # Still in cooldown period
                continue
            
            # Evaluate conditions
            conditions_met = self._evaluate_conditions(rule)
            
            if conditions_met:
                # Activate the relay
                actions = rule.get('actions', {})
                duration = actions.get('duration', 0)
                
                if actions.get('turn_on', True):
                    logger.info(f"Rule '{rule_name}' conditions met, turning on relay {relay.name}")
                    relay.turn_on()
                    self.last_activations[rule_name] = current_time
                    
                    # If duration is specified, schedule turn off
                    if duration > 0:
                        def turn_off_later(relay_obj, rule_name):
                            time.sleep(duration)
                            logger.info(f"Duration elapsed for rule '{rule_name}', turning off relay {relay_obj.name}")
                            relay_obj.turn_off()
                        
                        threading.Thread(
                            target=turn_off_later, 
                            args=(relay, rule_name),
                            daemon=True
                        ).start()
                else:
                    logger.info(f"Rule '{rule_name}' conditions met, turning off relay {relay.name}")
                    relay.turn_off()
                    self.last_activations[rule_name] = current_time
    
    def _evaluate_conditions(self, rule):
        """Evaluate the conditions for a rule.
        
        Args:
            rule (dict): Rule configuration
            
        Returns:
            bool: True if conditions are met, False otherwise
        """
        conditions = rule.get('conditions', [])
        logic = rule.get('condition_logic', 'AND').upper()
        
        if not conditions:
            return False
        
        results = []
        
        for condition in conditions:
            sensor_type = condition.get('sensor')
            operator = condition.get('operator')
            threshold = condition.get('value')
            
            # Get sensor reading
            reading = self._get_sensor_reading(sensor_type)
            
            if reading is None:
                # If we can't get a reading, the condition fails
                results.append(False)
                continue
            
            # Evaluate the condition
            if operator == 'less_than':
                results.append(reading < threshold)
            elif operator == 'less_than_or_equal':
                results.append(reading <= threshold)
            elif operator == 'greater_than':
                results.append(reading > threshold)
            elif operator == 'greater_than_or_equal':
                results.append(reading >= threshold)
            elif operator == 'equal':
                results.append(abs(reading - threshold) < 0.001)  # Float comparison
            elif operator == 'not_equal':
                results.append(abs(reading - threshold) >= 0.001)  # Float comparison
            else:
                logger.warning(f"Unknown operator '{operator}' in condition")
                results.append(False)
        
        # Combine results based on logic
        if logic == 'AND':
            return all(results)
        elif logic == 'OR':
            return any(results)
        else:
            logger.warning(f"Unknown condition logic '{logic}'")
            return False
    
    def _get_sensor_reading(self, sensor_type):
        """Get a sensor reading from the sensor controller.
        
        Args:
            sensor_type (str): Type of sensor
            
        Returns:
            float: Sensor reading or None if not available
        """
        if not self.sensor_controller:
            return None
        
        try:
            # Get the latest readings from the sensor controller
            readings = self.sensor_controller.get_latest_readings()
            
            # Extract the specific sensor reading
            if sensor_type == 'temperature':
                return readings.get('dht22', {}).get('temperature')
            elif sensor_type == 'humidity':
                return readings.get('dht22', {}).get('humidity')
            elif sensor_type == 'soil_moisture':
                return readings.get('soil_moisture', {}).get('moisture')
            elif sensor_type == 'light':
                return readings.get('light', {}).get('level')
            elif sensor_type == 'water_level':
                return readings.get('water_level', {}).get('level')
            elif sensor_type == 'rain':
                return readings.get('rain', {}).get('level')
            else:
                logger.warning(f"Unknown sensor type '{sensor_type}'")
                return None
        except Exception as e:
            logger.error(f"Error getting sensor reading for '{sensor_type}': {e}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        for relay in self.relays.values():
            relay.cleanup()
        logger.info("Relay automation resources cleaned up")