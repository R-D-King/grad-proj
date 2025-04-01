from flask import Blueprint

# Create Blueprint
irrigation_bp = Blueprint('irrigation', __name__)

# Import routes after creating the blueprint to avoid circular imports
from . import routes

# Remove any problematic imports if they exist
# from . import views  # Remove if present
