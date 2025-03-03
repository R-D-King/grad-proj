from flask import Flask, render_template
from shared.config import db, Config
from shared.socketio import socketio  # استيراد socketio من shared
from weather_station import weather_app
from smart_irrigation import irrigation_app
from flask_migrate import Migrate

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config.from_object(Config)

# تهيئة db و socketio
db.init_app(app)
socketio.init_app(app)  # تهيئة socketio

# تهيئة Flask-Migrate
migrate = Migrate(app, db)

# تسجيل Blueprints
app.register_blueprint(weather_app, url_prefix='/weather')
app.register_blueprint(irrigation_app, url_prefix='/irrigation')

# تعريف route للصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

# إنشاء الجداول في قاعدة البيانات (للمرة الأولى فقط)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)  # تشغيل التطبيق مع SocketIO