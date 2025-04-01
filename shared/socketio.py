from flask_socketio import SocketIO

# Create SocketIO instance with proper configuration
# cors_allowed_origins="*" allows connections from any origin
# async_mode='eventlet' uses eventlet for async operations
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')