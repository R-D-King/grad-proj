from flask import Blueprint

# إنشاء Blueprint مع تحديد مجلد القوالب
weather_app = Blueprint('weather_app', __name__, template_folder='templates')

from . import views