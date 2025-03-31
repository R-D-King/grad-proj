from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import os
import sqlite3
import csv
import io
from datetime import datetime, timedelta
from smart_irrigation.models import IrrigationPreset, IrrigationSchedule, IrrigationData, WeatherData
from shared.config import db
from time_utils import time_utils

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key'
# Use the config from shared.config
app.config.from_object('shared.config.Config')

# Ensure instance directory exists
instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# Initialize extensions
db.init_app(app)

# Register time_utils blueprint
app.register_blueprint(time_utils)

# Import and initialize socket handlers
from socket_handlers import init_app as init_socketio
socketio = init_socketio(app)

# Import and initialize reports blueprint
from reports import init_app as init_reports
reports_bp = init_reports(app)
app.register_blueprint(reports_bp)

# Import and initialize irrigation blueprint
from irrigation_control import init_app as init_irrigation
irrigation_bp = init_irrigation(app)
app.register_blueprint(irrigation_bp)

@app.route('/api/schedule/<int:schedule_id>/should-run')
def should_schedule_run(schedule_id):
    """Check if a schedule should run based on current server time"""
    from time_utils import is_time_to_run_schedule
    
    schedule = IrrigationSchedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'should_run': False})
    
    should_run = is_time_to_run_schedule(schedule)
    return jsonify({'should_run': should_run})

# Create database tables using SQLAlchemy
with app.app_context():
    db.create_all()

# Sample data for testing
weather_data = {
    'temperature': 25,
    'humidity': 60,
    'soil_moisture': 45,
    'wind_speed': 10,
    'pressure': 1013
}

pump_status = {
    'status': False
}

water_level = {
    'level': 75
}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

# Start the application
if __name__ == '__main__':
    # Install simple-websocket for better performance
    try:
        import simple_websocket
        print("Using simple-websocket for improved WebSocket performance")
    except ImportError:
        print("For better performance, install simple-websocket: pip install simple-websocket")
    
    socketio.run(app, debug=True, host='0.0.0.0')