from flask import Blueprint
from shared.socketio import socketio  # Import socketio from main application

# Create Blueprint
irrigation_app = Blueprint('irrigation_app', __name__)
