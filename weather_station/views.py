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

@weather_app.route('/report', methods=['GET'])
def generate_weather_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    temperature = request.args.get('temperature', 'false').lower() == 'true'
    humidity = request.args.get('humidity', 'false').lower() == 'true'
    soil_moisture = request.args.get('soil_moisture', 'false').lower() == 'true'
    wind_speed = request.args.get('wind_speed', 'false').lower() == 'true'
    pressure = request.args.get('pressure', 'false').lower() == 'true'
    download = request.args.get('download', 'false').lower() == 'true'
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None

    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

    data = WeatherData.query.filter(WeatherData.timestamp.between(start_date, end_date)).all()

    if data:
        report = []
        for entry in data:
            report_entry = {"timestamp": entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            if temperature:
                report_entry["temperature"] = entry.temperature
            if humidity:
                report_entry["humidity"] = entry.humidity
            if soil_moisture:
                report_entry["soil_moisture"] = entry.soil_moisture
            if wind_speed:
                report_entry["wind_speed"] = entry.wind_speed
            if pressure:
                report_entry["pressure"] = entry.pressure
            report.append(report_entry)

        if download:
            output = StringIO()
            writer = csv.writer(output)

            headers = ["Timestamp"]
            if temperature:
                headers.append("Temperature (°C)")
            if humidity:
                headers.append("Humidity (%)")
            if soil_moisture:
                headers.append("Soil Moisture (%)")
            if wind_speed:
                headers.append("Wind Speed (km/h)")
            if pressure:
                headers.append("Pressure (hPa)")
            writer.writerow(headers)

            for entry in report:
                row = [entry["timestamp"]]
                if temperature:
                    row.append(entry["temperature"])
                if humidity:
                    row.append(entry["humidity"])
                if soil_moisture:
                    row.append(entry["soil_moisture"])
                if wind_speed:
                    row.append(entry["wind_speed"])
                if pressure:
                    row.append(entry["pressure"])
                writer.writerow(row)

            output.seek(0)
            return output.getvalue(), 200, {
                "Content-Disposition": f"attachment; filename=weather_report_{start_date_str}_to_{end_date_str}.csv",
                "Content-type": "text/csv"
            }
        else:
            return jsonify(report), 200
    else:
        return jsonify({"message": "No data available"}), 404