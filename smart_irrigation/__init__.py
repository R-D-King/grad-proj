from flask import Blueprint
from shared.socketio import socketio  # استيراد socketio من التطبيق الرئيسي

# إنشاء Blueprint
irrigation_app = Blueprint('irrigation_app', __name__)

# لا داعي لإنشاء socketio هنا، لأنه مستورد من التطبيق الرئيسي

from . import views