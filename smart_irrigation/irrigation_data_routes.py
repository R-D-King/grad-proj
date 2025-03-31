from flask import request, jsonify, render_template, redirect, url_for
from shared.config import db
from .models import IrrigationPreset, IrrigationData
from datetime import datetime, timedelta
import csv
from io import StringIO
from . import irrigation_app
from shared.socketio import socketio

# Global variable to store previous water level
previous_water_level = None

# Main page with presets list
@irrigation_app.route('/')
def index():
    presets = IrrigationPreset.query.all()
    return render_template('index.html', presets=presets)

# Select preset and show its irrigation schedule
@irrigation_app.route('/irrigation/select_preset', methods=['POST'])
def select_preset():
    preset_id = request.form.get('preset_id')
    if preset_id:
        selected_preset = IrrigationPreset.query.get(preset_id)
        return render_template('index.html', presets=IrrigationPreset.query.all(), selected_preset=selected_preset)
    return redirect(url_for('index'))

# Add irrigation data
@irrigation_app.route('/api/irrigation', methods=['POST'])
def add_irrigation_data():
    global previous_water_level
    data = request.json
    current_water_level = data['water_level']

    # Check for significant water level change
    if previous_water_level is not None:
        change_percentage = abs(current_water_level - previous_water_level) / previous_water_level * 100
        if change_percentage >= 5:
            # Record change in database
            new_data = IrrigationData(
                pump_status=data['pump_status'],
                water_level=current_water_level
            )
            db.session.add(new_data)
            db.session.commit()

    previous_water_level = current_water_level

    # Send event to update UI
    socketio.emit('update_irrigation', {
        "pump_status": data['pump_status'],
        "water_level": current_water_level
    })

    return jsonify({"message": "Irrigation data added successfully"}), 201

# Generate irrigation report
@irrigation_app.route('/api/irrigation/report', methods=['GET'])
def generate_irrigation_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    pump_status = request.args.get('pump_status', 'false').lower() == 'true'
    water_level = request.args.get('water_level', 'false').lower() == 'true'
    duration = request.args.get('duration', 'false').lower() == 'true'
    download = request.args.get('download', 'false').lower() == 'true'

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

    end_date += timedelta(days=1)  # Include the end date

    data = IrrigationData.query.filter(IrrigationData.timestamp.between(start_date, end_date)).all()

    if data:
        report = []
        for entry in data:
            report_entry = {"timestamp": entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            if pump_status:
                report_entry["pump_status"] = "ON" if entry.pump_status else "OFF"
            if water_level:
                report_entry["water_level"] = entry.water_level
            if duration:
                report_entry["pump_duration"] = int(entry.pump_duration)
            report.append(report_entry)

        if download:
            output = StringIO()
            writer = csv.writer(output)
            headers = ["Timestamp"]
            if pump_status:
                headers.append("Pump Status")
            if water_level:
                headers.append("Water Level (%)")
            if duration:
                headers.append("Pump Duration (seconds)")
            writer.writerow(headers)

            for entry in report:
                row = [entry["timestamp"]]
                if pump_status:
                    row.append(entry["pump_status"])
                if water_level:
                    row.append(entry["water_level"])
                if duration:
                    row.append(entry["pump_duration"])
                writer.writerow(row)

            output.seek(0)
            return output.getvalue(), 200, {
                "Content-Disposition": f"attachment; filename=irrigation_report_{start_date_str}_to_{end_date_str}.csv",
                "Content-type": "text/csv"
            }
        else:
            return jsonify(report), 200
    else:
        return jsonify({"message": "No data available"}), 404