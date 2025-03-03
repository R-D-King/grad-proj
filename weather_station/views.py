from flask import request, jsonify
from shared.config import db
from .models import WeatherData
from datetime import datetime, timedelta
import csv
from io import StringIO
from . import weather_app

@weather_app.route('/report', methods=['GET'])
def generate_weather_report():
    days = int(request.args.get('days', 7))  # عدد الأيام الافتراضي هو 7
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # تحديد أنواع البيانات المطلوبة
    include_temperature = request.args.get('temperature', 'false').lower() == 'true'
    include_humidity = request.args.get('humidity', 'false').lower() == 'true'
    include_soil_moisture = request.args.get('soil_moisture', 'false').lower() == 'true'
    include_wind_speed = request.args.get('wind_speed', 'false').lower() == 'true'
    include_pressure = request.args.get('pressure', 'false').lower() == 'true'

    # جلب البيانات من قاعدة البيانات
    data = WeatherData.query.filter(WeatherData.timestamp.between(start_date, end_date)).all()

    if data:
        # تجميع البيانات حسب الساعة
        hourly_data = {}
        for entry in data:
            hour = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour not in hourly_data:
                hourly_data[hour] = {
                    "temperature": [],
                    "humidity": [],
                    "soil_moisture": [],
                    "wind_speed": [],
                    "pressure": []
                }
            hourly_data[hour]["temperature"].append(entry.temperature)
            hourly_data[hour]["humidity"].append(entry.humidity)
            hourly_data[hour]["soil_moisture"].append(entry.soil_moisture)
            hourly_data[hour]["wind_speed"].append(entry.wind_speed)
            hourly_data[hour]["pressure"].append(entry.pressure)

        # حساب المتوسطات لكل ساعة
        report = []
        for hour, values in hourly_data.items():
            entry = {"timestamp": hour}
            if include_temperature:
                entry["avg_temperature"] = sum(values["temperature"]) / len(values["temperature"])
            if include_humidity:
                entry["avg_humidity"] = sum(values["humidity"]) / len(values["humidity"])
            if include_soil_moisture:
                entry["avg_soil_moisture"] = sum(values["soil_moisture"]) / len(values["soil_moisture"])
            if include_wind_speed:
                entry["avg_wind_speed"] = sum(values["wind_speed"]) / len(values["wind_speed"])
            if include_pressure:
                entry["avg_pressure"] = sum(values["pressure"]) / len(values["pressure"])
            report.append(entry)

        # إذا طلب المستخدم تحميل التقرير كملف CSV
        if request.args.get('download') == 'true':
            output = StringIO()
            writer = csv.writer(output)

            # كتابة رأس الملف بناءً على الخيارات المحددة
            headers = ["Timestamp"]
            if include_temperature:
                headers.append("Avg Temperature (°C)")
            if include_humidity:
                headers.append("Avg Humidity (%)")
            if include_soil_moisture:
                headers.append("Avg Soil Moisture (%)")
            if include_wind_speed:
                headers.append("Avg Wind Speed (km/h)")
            if include_pressure:
                headers.append("Avg Pressure (hPa)")
            writer.writerow(headers)

            # كتابة البيانات
            for entry in report:
                row = [entry["timestamp"]]
                if include_temperature:
                    row.append(entry["avg_temperature"])
                if include_humidity:
                    row.append(entry["avg_humidity"])
                if include_soil_moisture:
                    row.append(entry["avg_soil_moisture"])
                if include_wind_speed:
                    row.append(entry["avg_wind_speed"])
                if include_pressure:
                    row.append(entry["avg_pressure"])
                writer.writerow(row)

            output.seek(0)
            return output.getvalue(), 200, {
                "Content-Disposition": f"attachment; filename=weather_report_{days}_days.csv",
                "Content-type": "text/csv"
            }
        else:
            # عرض التقرير في الواجهة
            return jsonify(report), 200
    else:
        return jsonify({"message": "No data available"}), 404