from flask import Flask, render_template
from shared.config import db, Config
from shared.socketio import socketio
from weather_station import weather_app
from smart_irrigation import irrigation_app
from smart_irrigation.models import IrrigationPreset  # استيراد النموذج
from flask_migrate import Migrate
from datetime import datetime
import time
from threading import Thread

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config.from_object(Config)

# تهيئة db و socketio
db.init_app(app)
socketio.init_app(app)

# تهيئة Flask-Migrate
migrate = Migrate(app, db)

# تسجيل Blueprints
app.register_blueprint(weather_app, url_prefix='/weather')
app.register_blueprint(irrigation_app, url_prefix='/irrigation')

# إنشاء الجداول في قاعدة البيانات (للمرة الأولى فقط)
with app.app_context():
    db.create_all()

# تعريف route للصفحة الرئيسية
@app.route('/')
def index():
    presets = IrrigationPreset.query.all()  # الآن IrrigationPreset معرّف
    return render_template('index.html', presets=presets)

# وظيفة لتحديث الوقت الحقيقي
def update_time():
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        socketio.emit('update_time', {'time': current_time})
        time.sleep(1)

# بدء thread لتحديث الوقت
time_thread = Thread(target=update_time)
time_thread.daemon = True
time_thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')