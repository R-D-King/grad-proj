"""
Hardware components module for controlling physical devices.
This module provides interfaces for various sensors and actuators used in the system.
"""

from .relay import Relay
from .pump import Pump
from .sensor_controller import SensorController
from .sensor_simulation import SimulatedSensor
from .water_level import WaterLevelSensor
from .soil_moisture import SoilMoistureSensor
from .dht22 import DHT22Sensor
from .lcd_16x2 import LCD