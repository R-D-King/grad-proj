from flask import Blueprint
from flask_socketio import SocketIO

# إنشاء Blueprint
weather_app = Blueprint('weather_app', __name__)

# تهيئة SocketIO
socketio = SocketIO()

# استيراد views بعد تعريف socketio
from . import views