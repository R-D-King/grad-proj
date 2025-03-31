import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
from weather.models import WeatherData
from irrigation.models import IrrigationLog
import json

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate a report based on the provided parameters."""
    data = request.json
    report_type = data.get('report_type')
    
    # Use provided dates or default to last 7 days
    if data.get('start_date') and data.get('start_date').strip():
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=7)
        
    if data.get('end_date') and data.get('end_date').strip():
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
    else:
        end_date = datetime.now()
        
    options = data.get('options', {})
    
    # Add one day to end_date to include the entire day
    end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    if report_type == 'weather':
        query = WeatherData.query.filter(
            WeatherData.timestamp >= start_date,
            WeatherData.timestamp <= end_date
        ).order_by(WeatherData.timestamp.desc())
        
        results = [item.to_dict() for item in query.all()]
    else:  # irrigation
        query = IrrigationLog.query.filter(
            IrrigationLog.timestamp >= start_date,
            IrrigationLog.timestamp <= end_date
        ).order_by(IrrigationLog.timestamp.desc())
        
        results = [item.to_dict() for item in query.all()]
    
    return jsonify(results)

@reports_bp.route('/api/reports/download', methods=['GET'])
def download_report():
    """Download a report as CSV based on the provided parameters."""
    report_type = request.args.get('report_type')
    
    # Use provided dates or default to last 7 days
    if request.args.get('start_date') and request.args.get('start_date').strip():
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=7)
        
    if request.args.get('end_date') and request.args.get('end_date').strip():
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    options_str = request.args.get('options', '{}')
    options = json.loads(options_str)
    
    # Add one day to end_date to include the entire day
    end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    
    # Query data
    if report_type == 'weather':
        query = WeatherData.query.filter(
            WeatherData.timestamp >= start_date,
            WeatherData.timestamp <= end_date
        ).order_by(WeatherData.timestamp.desc())
        
        results = [item.to_dict() for item in query.all()]
    else:  # irrigation
        query = IrrigationLog.query.filter(
            IrrigationLog.timestamp >= start_date,
            IrrigationLog.timestamp <= end_date
        ).order_by(IrrigationLog.timestamp.desc())
        
        results = [item.to_dict() for item in query.all()]
    
    if not results:
        return jsonify({
            'status': 'no_data',
            'message': 'No data available for the selected period'
        })
    
    # Create CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['Timestamp']
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
    # Write data rows
    for item in results:
        timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        row = [timestamp.strftime('%Y-%m-%d %H:%M:%S')]
        
        if report_type == 'weather':
            if options.get('temperature'): row.append(item['temperature'])
            if options.get('humidity'): row.append(item['humidity'])
            if options.get('soil_moisture'): row.append(item['soil_moisture'])
            if options.get('wind_speed'): row.append(item['wind_speed'])
            if options.get('pressure'): row.append(item['pressure'])
        else:
            if options.get('pump_status'): row.append('Running' if item['pump_status'] else 'Stopped')
            if options.get('water_level'): row.append(item['water_level'])
            # Make sure duration is included if it exists, otherwise use 0
            if options.get('duration'): row.append(item.get('duration', 0))
        
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{report_type}_report_{start_date.strftime("%Y-%m-%d")}_to_{end_date.strftime("%Y-%m-%d")}.csv'
    )