from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
from smart_irrigation.models import IrrigationData, WeatherData
from shared.config import db
import csv
import io
import json

reports_bp = Blueprint('reports', __name__)
flask_app = None

def init_app(app):
    """Store the Flask app instance for later use"""
    global flask_app
    flask_app = app
    return reports_bp

@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report():
    data = request.json
    report_type = data['report_type']
    
    # Use provided dates or default to last 7 days
    if data.get('start_date') and data.get('end_date'):
        start_date = data['start_date']
        end_date = data['end_date']
    else:
        # Default to last 7 days
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Use current_app instead of reports_bp.app
    if report_type == 'weather':
        # Use SQLAlchemy to query weather data
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        report_data = WeatherData.query.filter(
            WeatherData.timestamp.between(start_datetime, end_datetime)
        ).order_by(WeatherData.timestamp).all()
        
        # Convert to dict for JSON serialization
        report_data = [{
            'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': item.temperature,
            'humidity': item.humidity,
            'soil_moisture': item.soil_moisture,
            'wind_speed': item.wind_speed,
            'pressure': item.pressure
        } for item in report_data]
    else:
        # Use SQLAlchemy to query irrigation data
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        report_data = IrrigationData.query.filter(
            IrrigationData.timestamp.between(start_datetime, end_datetime)
        ).order_by(IrrigationData.timestamp).all()
        
        # Convert to dict for JSON serialization
        report_data = [{
            'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'pump_status': item.pump_status,
            'water_level': item.water_level,
            'duration': item.pump_duration
        } for item in report_data]
    
    # Return empty array when no data is available
    if not report_data:
        return jsonify([])
    
    return jsonify(report_data)

@reports_bp.route('/api/reports/download')
def download_report():
    """Generate and download a CSV report"""
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    options = json.loads(request.args.get('options'))
    
    # Use provided dates or default to last 7 days
    if not start_date or not end_date:
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Use current_app instead of reports_bp.app
    if report_type == 'weather':
        # Use SQLAlchemy to query weather data
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        query_data = WeatherData.query.filter(
            WeatherData.timestamp.between(start_datetime, end_datetime)
        ).order_by(WeatherData.timestamp).all()
        
        # Convert to dict for processing
        report_data = [{
            'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': item.temperature,
            'humidity': item.humidity,
            'soil_moisture': item.soil_moisture,
            'wind_speed': item.wind_speed,
            'pressure': item.pressure
        } for item in query_data]
    else:
        # Use SQLAlchemy to query irrigation data
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        query_data = IrrigationData.query.filter(
            IrrigationData.timestamp.between(start_datetime, end_datetime)
        ).order_by(IrrigationData.timestamp).all()
        
        # Convert to dict for processing
        report_data = [{
            'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'pump_status': item.pump_status,
            'water_level': item.water_level,
            'duration': item.pump_duration
        } for item in query_data]
    
    # If no data, return a special response that will trigger a popup instead of an error page
    if not report_data:
        return jsonify({
            'status': 'no_data',
            'message': 'No data available for the selected period. Please try a different date range.'
        }), 200  # Return 200 OK status instead of 404
    
    # Create CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['Date/Time']
    if report_type == 'weather':
        if options.get('temperature'): headers.append('Temperature (°C)')
        if options.get('humidity'): headers.append('Humidity (%)')
        if options.get('soil_moisture'): headers.append('Soil Moisture (%)')
        if options.get('wind_speed'): headers.append('Wind Speed (km/h)')
        if options.get('pressure'): headers.append('Pressure (hPa)')
    else:
        if options.get('pump_status'): headers.append('Pump Status')
        if options.get('water_level'): headers.append('Water Level (%)')
        if options.get('duration'): headers.append('Duration (s)')
    
    writer.writerow(headers)
    
    # Write data
    for item in report_data:
        row = [item['timestamp']]
        if report_type == 'weather':
            if options.get('temperature'): row.append(item['temperature'])
            if options.get('humidity'): row.append(item['humidity'])
            if options.get('soil_moisture'): row.append(item['soil_moisture'])
            if options.get('wind_speed'): row.append(item['wind_speed'])
            if options.get('pressure'): row.append(item['pressure'])
        else:
            if options.get('pump_status'): row.append('Running' if item['pump_status'] else 'Stopped')
            if options.get('water_level'): row.append(item['water_level'])
            if options.get('duration'): row.append(item['duration'])
        
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{report_type}_report_{start_date}_to_{end_date}.csv')