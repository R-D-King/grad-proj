from flask import Blueprint

# Create Blueprint
weather_bp = Blueprint('weather', __name__)

# Import routes after creating the blueprint to avoid circular imports
from . import routes
