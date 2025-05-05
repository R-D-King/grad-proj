from flask_socketio import SocketIO

# Create SocketIO instance with proper configuration
# cors_allowed_origins="*" allows connections from any origin
# async_mode='eventlet' uses eventlet for async operations
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')


# Add this event handler
@socketio.on('get_sensor_status')
def handle_get_sensor_status():
    """Handle request for sensor status."""
    from shared.sensor import sensor_controller
    socketio.emit('sensor_status', {'sensor_status': sensor_controller.get_sensor_status()})