# Import eventlet and do monkey patching FIRST, before any other imports
import eventlet
eventlet.monkey_patch()

# Now import Flask and other modules
from flask import Flask, render_template, request, has_request_context
from shared.database import db
from shared.socketio import socketio
import os
import logging

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure logging to skip certain requests
    class NoTimeRequestsFilter(logging.Filter):
        def filter(self, record):
            # Only check request path when in a request context
            if has_request_context():
                # Skip logging for server-time, favicon, and pump duration requests
                if (request.path == '/api/server-time/display' or 
                    request.path == '/favicon.ico' or
                    request.path == '/api/irrigation/pump/duration'):
                    return False
                # Skip socket.io polling requests
                if request.path.startswith('/socket.io'):
                    return False
            # Filter out eventlet and wsgi startup messages
            if 'wsgi starting up on' in getattr(record, 'msg', ''):
                return False
            if '(accepted' in getattr(record, 'msg', ''):
                return False
            return True
            
    # Apply filter to Werkzeug logger
    logging.getLogger('werkzeug').addFilter(NoTimeRequestsFilter())
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, logger=False, engineio_logger=False)  # Disable socketio logging
    
    # Import blueprints
    from shared.routes import shared_bp
    
    # Instead, ensure we're using:
    from irrigation.routes import irrigation_bp
    from reports.routes import reports_bp
    from weather.routes import weather_bp
    
    # Register blueprints
    app.register_blueprint(shared_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(irrigation_bp)
    app.register_blueprint(weather_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Use socketio instead of Flask's built-in server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)