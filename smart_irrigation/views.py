# This file now serves as a compatibility layer
# All functionality has been moved to specialized modules

from flask import render_template, request, redirect, url_for, jsonify
from shared.config import db
from .models import IrrigationPreset, IrrigationSchedule, IrrigationData
from datetime import datetime, timedelta
import csv
from io import StringIO
from . import irrigation_app
from shared.socketio import socketio

# Import all routes from the modular files
from .preset_routes import (
    add_preset, get_presets, get_preset, update_preset, 
    delete_preset, activate_preset
)
from .schedule_routes import (
    add_schedule, update_schedule, delete_schedule
)
from .irrigation_data_routes import (
    index, select_preset, add_irrigation_data, generate_irrigation_report
)
from .manual_control import manual_pump_control
