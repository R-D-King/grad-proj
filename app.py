# Import eventlet and do monkey patching FIRST, before any other imports
import eventlet
eventlet.monkey_patch()

# Now import Flask and other modules
from flask import Flask, render_template, request, has_request_context
from shared.database import db
from shared.socketio import socketio
import os
import logging
from shared.config import Config
from shared.routes import shared_bp
from irrigation.routes import irrigation_bp
from weather.routes import weather_bp
from reports.routes import reports_bp

# Set default configuration values for key operational parameters
os.environ.setdefault('UI_UPDATE_INTERVAL', '1')  # 1 second default
os.environ.setdefault('DB_UPDATE_INTERVAL', '60')  # 60 seconds default

def create_app(config_class=Config):
    # Initialize configuration
    config = config_class()
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    app.register_blueprint(shared_bp)
    app.register_blueprint(irrigation_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(reports_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Initialize weather controller with app context
    from weather.controllers import init_app as init_weather
    init_weather(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration values
    config = app.config.get_namespace('')
    
    # Print configuration information
    print(f"UI update interval: {config.get('UI_UPDATE_INTERVAL', 1)} seconds")
    print(f"Database update interval: {config.get('DB_UPDATE_INTERVAL', 60)} seconds")
    
    # Run the application
    host = config.get('HOST', '0.0.0.0')
    port = config.get('PORT', 5000)
    debug = config.get('DEBUG', False)
    
    socketio.run(app, host=host, port=port, debug=debug)