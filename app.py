# Import eventlet and do monkey patching FIRST, before any other imports
import eventlet
eventlet.monkey_patch()

# Now import Flask and other modules
import signal
import sys
import time    # For the sleep function in signal handler
from flask import Flask, render_template, request, has_request_context
from shared.database import db
from shared.socketio import socketio
import os
import logging
import socket
from shared.config import Config
from shared.routes import shared_bp
from irrigation.routes import irrigation_bp
from weather.routes import weather_bp
from reports.routes import reports_bp
# Set default configuration values for key operational parameters
os.environ.setdefault('UI_UPDATE_INTERVAL', '1')  # 1 second default
os.environ.setdefault('DB_UPDATE_INTERVAL', '60')  # 60 seconds default

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

def create_app(config_class=Config):
    # Initialize configuration
    config = config_class()
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
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
        print("\nreceived SIGINT")
        
        # Display shutdown message on LCD if available
        try:
            from weather.controllers import lcd
            if lcd:
                lcd.display_shutdown()
                time.sleep(1)  # Give time for the message to be displayed
        except Exception as e:
            print(f"Error displaying shutdown message: {e}")
        
        # Exit the application
        sys.exit(0)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration values
    config = app.config.get_namespace('')
    
    # Get the device's IP address
    ip_address = get_ip_address()
    
    # Store IP address in app config for LCD display
    app.config['IP_ADDRESS'] = ip_address
    
    # Run the application
    host = config.get('HOST', '0.0.0.0')
    port = config.get('PORT', 5000)
    debug = config.get('DEBUG', False)
    
    # Print server information first with actual IP address
    print("\n" + "=" * 60)
    print(f"Starting Irrigation Control System Server")
    print(f"Local access:  http://localhost:{port}")
    print(f"Network access: http://{ip_address}:{port}")
    print("=" * 60 + "\n")
    
    # Print configuration information
    print(f"UI update interval: {config.get('UI_UPDATE_INTERVAL', 1)} seconds")
    print(f"Database update interval: {config.get('DB_UPDATE_INTERVAL', 60)} seconds")
    
    # Initialize weather controller with app context - moved here to run after server info is displayed
    from weather.controllers import init_app as init_weather
    print("\nChecking connected devices:")
    print("-" * 30)
    init_weather(app)
    print("-" * 30)
    
    # Start the server
    socketio.run(app, host=host, port=port, debug=debug)