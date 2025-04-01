from flask import Blueprint

# Create Blueprint
reports_bp = Blueprint('reports', __name__)

# Import routes after creating the blueprint to avoid circular imports
from . import routes