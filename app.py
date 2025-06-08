# Import eventlet and do monkey patching FIRST, before any other imports
import eventlet
eventlet.monkey_patch()

# Now import Flask and other modules
import signal
import sys
import time    # For the sleep function in signal handler
import threading
from flask import Flask, render_template, request, has_request_context
from shared.database import db
from shared.socketio import socketio
import os
import socket
import platform  # Add platform import here
import subprocess  # Add subprocess import for the SSID function
from shared.config import Config
from shared.routes import shared_bp
from irrigation.routes import irrigation_bp
from weather.routes import weather_bp
from reports.routes import reports_bp
import json
import logging

# Import all models to ensure they are registered with SQLAlchemy
from weather.models import WeatherData
from irrigation.models import Preset, PumpLog, IrrigationLog

# Set default configuration values for key operational parameters
os.environ.setdefault('UI_UPDATE_INTERVAL', '1')  # 1 second default
os.environ.setdefault('DB_UPDATE_INTERVAL', '60')  # 60 seconds default
os.environ.setdefault('NETWORK_UPDATE_INTERVAL', '60') # 60 seconds default

def get_ip_address():
    """Get the primary IP address of the device"""
    try:
        # Create a socket connection to determine the primary interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable, just used to determine interface
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return '127.0.0.1'  # Fallback to localhost

def get_network_ssid():
    """Get the SSID of the connected WiFi network."""
    try:
        if platform.system() == "Linux":
            # For Raspberry Pi / Linux
            result = subprocess.check_output(['iwgetid', '-r']).decode('utf-8').strip()
            return result if result else "Not connected"
        else:
            # For other OS (e.g., development)
            return "Dev-SSID"  # Placeholder for development
    except Exception as e:
        print(f"Error getting network SSID: {e}")
        return "Unknown"

def update_network_info(app):
    """Updates network IP and SSID in app config."""
    ip_address = get_ip_address()
    network_ssid = get_network_ssid()
    
    current_ip = app.config.get('IP_ADDRESS')
    current_ssid = app.config.get('NETWORK_SSID')

    if ip_address != current_ip or network_ssid != current_ssid:
        logging.info(f"Network change detected. New IP: {ip_address}, New SSID: {network_ssid}")
        app.config['IP_ADDRESS'] = ip_address
        app.config['NETWORK_SSID'] = network_ssid

def network_update_loop(app):
    """Periodically updates network information."""
    interval = app.config.get('NETWORK_UPDATE_INTERVAL', 60)
    logging.info(f"Network info will be updated every {interval} seconds.")
    
    while getattr(app, 'network_thread_running', False):
        update_network_info(app)
        eventlet.sleep(interval)

def create_app(config_class=Config):
    # Configure logging to show INFO level messages in the terminal
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize configuration
    config = config_class()
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Load and apply the logging configuration
    logging_config_path = os.path.join(os.path.dirname(__file__), 'config', 'logging.json')
    if os.path.exists(logging_config_path):
        with open(logging_config_path, 'r') as f:
            try:
                logging_config = json.load(f)
                app.config['logging'] = logging_config
                logging.info("Successfully loaded logging configuration.")
            except json.JSONDecodeError as e:
                logging.error(f"Could not parse logging.json: {e}")
    else:
        logging.warning(f"Logging config file not found at {logging_config_path}")

    # Configure the database with an absolute path to instance/app.db
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'app.db')
    
    # Ensure the instance directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints - IMPORTANT: Remove url_prefix to fix 404 errors
    app.register_blueprint(shared_bp)
    app.register_blueprint(irrigation_bp)  # Removed url_prefix
    app.register_blueprint(weather_bp)     # Removed url_prefix
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Create database tables within app context
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        return render_template('index.html')
        
    # Add server time endpoint to fix 404 error
    @app.route('/api/server-time/display', methods=['GET'])
    def server_time():
        from datetime import datetime
        return {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    def signal_handler(sig, frame):
        """Handle SIGINT (Ctrl+C) gracefully."""
        logging.info("\nReceived SIGINT")
        
        if hasattr(app, 'network_thread_running'):
            app.network_thread_running = False
        
        # Use a non-blocking approach for LCD
        try:
            from weather.controllers import sensor_controller
            # Stop all monitoring threads first
            if hasattr(sensor_controller, 'running'):
                sensor_controller.running = False
                eventlet.sleep(0.5)  # Brief pause to let threads notice the change
        except Exception as e:
            logging.error(f"Error stopping sensor controller: {e}")
        
        # Clean up any GPIO resources
        try:
            logging.info("\nDe-initializing hardware resources...")
            # Clean up GPIO resources
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except Exception as e:
            logging.error(f"Error during GPIO cleanup: {e}")
        
        # Exit the application
        sys.exit(0)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.network_thread_running = True
    
    # Get configuration values
    config = app.config.get_namespace('')
    
    # Get logging interval for display
    logging_config = config.get('logging', {})
    log_interval = logging_config.get('log_interval', 60)
    
    # Initial network info fetch
    update_network_info(app)
    
    # Start network update loop
    eventlet.spawn(network_update_loop, app)
    
    # Run the application
    host = config.get('HOST', '0.0.0.0')
    port = config.get('PORT', 5000)
    debug = config.get('DEBUG', False)
    
    # Print server information first with actual IP address
    print("\n" + "=" * 60)
    print(f"Starting Irrigation Control System Server")
    print(f"Local access:  http://localhost:{port}")
    print(f"Network access: http://{app.config.get('IP_ADDRESS')}:{port}")
    print("=" * 60 + "\n")
    
    # Print configuration information
    print(f"UI update interval: {config.get('UI_UPDATE_INTERVAL', 1)} seconds")
    print(f"Database update interval: {config.get('DB_UPDATE_INTERVAL', 60)} seconds")
    print(f"Network check interval: {config.get('NETWORK_UPDATE_INTERVAL', 60)} seconds")
    print(f"CSV logging interval: {log_interval} seconds")
    
    # Initialize weather controller with app context - moved here to run after server info is displayed
    from weather.controllers import init_app as init_weather
    print("\nChecking connected devices:")
    print("-" * 30)
    init_weather(app)
    print("-" * 30)
    
    # Start the server
    socketio.run(app, host=host, port=port, debug=debug)