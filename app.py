from flask import Flask, render_template, request, has_request_context
from shared.database import db
from shared.socketio import socketio
from shared.routes import shared_bp
from shared.reports import reports_bp
from irrigation.routes import irrigation_bp
from weather.routes import weather_bp
import os
import logging

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure logging to skip certain requests
    class NoTimeRequestsFilter(logging.Filter):
        def filter(self, record):
            # Only check request path when in a request context
            if has_request_context() and request.path == '/api/server-time/display':
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
    socketio.init_app(app)
    
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
    socketio.run(app, debug=True)