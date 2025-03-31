from flask import Blueprint
from shared.socketio import socketio  # Import socketio from main application

# Create Blueprint
irrigation_app = Blueprint('irrigation_app', __name__)

# No need to create socketio here, as it is imported from the main application
from . import preset_routes, schedule_routes, irrigation_data_routes, manual_control

# For backward compatibility, import all routes into views
from . import views