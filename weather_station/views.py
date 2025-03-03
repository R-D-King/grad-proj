from flask import request, jsonify
from shared.config import db
from .models import WeatherData
from datetime import datetime, timedelta
import csv
from io import StringIO
from . import weather_app  # استيراد Blueprint فقط
from shared.socketio import socketio  # استيراد socketio من shared

# إضافة بيانات الطقس
@weather_app.route('/api/weather', methods=['POST'])
def add_weather_data():
    data = request.json
    new_data = WeatherData(
        temperature=data['temperature'],
        humidity=data['humidity'],
        soil_moisture=data['soil_moisture'],
        wind_speed=data['wind_speed'],
        pressure=data['pressure']
    )
    db.session.add(new_data)
    db.session.commit()

    # إرسال حدث لتحديث الواجهة
    socketio.emit('update_weather', {
        "temperature": data['temperature'],
        "humidity": data['humidity'],
        "soil_moisture": data['soil_moisture'],
        "wind_speed": data['wind_speed'],
        "pressure": data['pressure']
    })

    return jsonify({"message": "Weather data added successfully"}), 201

# إنشاء تقارير الطقس
@weather_app.route('/report', methods=['GET'])
def generate_weather_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    download = request.args.get('download', 'false').lower() == 'true'

    # تحويل التواريخ من نص إلى كائن datetime
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    # إذا لم يتم تحديد التواريخ، استخدم آخر 7 أيام كافتراضي
    if not start_date or not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

    # جلب البيانات من قاعدة البيانات
    data = WeatherData.query.filter(WeatherData.timestamp.between(start_date, end_date)).all()

    if data:
        # إذا طلب المستخدم تحميل التقرير كملف CSV
        if download:
            output = StringIO()
            writer = csv.writer(output)

            # كتابة رأس الملف
            writer.writerow(["Timestamp", "Temperature (°C)", "Humidity (%)", "Soil Moisture (%)", "Wind Speed (km/h)", "Pressure (hPa)"])

            # كتابة البيانات
            for entry in data:
                writer.writerow([
                    entry.timestamp,
                    entry.temperature,
                    entry.humidity,
                    entry.soil_moisture,
                    entry.wind_speed,
                    entry.pressure
                ])

            output.seek(0)
            return output.getvalue(), 200, {
                "Content-Disposition": f"attachment; filename=weather_report_{start_date_str}_to_{end_date_str}.csv",
                "Content-type": "text/csv"
            }
        else:
            # عرض التقرير في الصفحة
            report = []
            for entry in data:
                report.append({
                    "timestamp": entry.timestamp,
                    "temperature": entry.temperature,
                    "humidity": entry.humidity,
                    "soil_moisture": entry.soil_moisture,
                    "wind_speed": entry.wind_speed,
                    "pressure": entry.pressure
                })
            return jsonify(report), 200
    else:
        return jsonify({"message": "No data available"}), 404