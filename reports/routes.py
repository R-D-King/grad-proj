from flask import Blueprint, jsonify, request, Response
import json
import csv
from io import StringIO
from datetime import datetime
from .controllers import generate_report

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report_route():
    """Generate a report based on the specified parameters."""
    data = request.json
    
    # Extract parameters
    report_type = data.get('report_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    options = data.get('options', {})
    
    # Validate parameters
    if not report_type or not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing required parameters."})
    
    # Generate the report
    report_data = generate_report(report_type, start_date, end_date, options)
    
    return jsonify(report_data)

@reports_bp.route('/api/reports/download', methods=['GET'])
def download_report():
    """Download a report as CSV."""
    # Extract parameters
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    options_str = request.args.get('options', '{}')
    
    try:
        options = json.loads(options_str)
    except json.JSONDecodeError:
        options = {}
    
    # Validate parameters
    if not report_type or not start_date or not end_date:
        return jsonify({"status": "error", "message": "Missing required parameters."})
    
    # Generate the report
    report_data = generate_report(report_type, start_date, end_date, options)
    
    # If no data, return a message
    if not report_data:
        return jsonify({"status": "no_data", "message": "No data available for the selected period."})
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['Timestamp']
    if report_type == 'weather':
        if options.get('temperature', False):
            headers.append('Temperature (°C)')
        if options.get('humidity', False):
            headers.append('Humidity (%)')
        if options.get('soil_moisture', False):
            headers.append('Soil Moisture (%)')
        if options.get('wind_speed', False):
            headers.append('Wind Speed (km/h)')
        if options.get('pressure', False):
            headers.append('Pressure (hPa)')
    else:  # irrigation
        if options.get('pump_status', False):
            headers.append('Pump Status')
        if options.get('water_level', False):
            headers.append('Water Level (%)')
        if options.get('duration', False):
            headers.append('Duration (s)')
    
    writer.writerow(headers)
    
    # Write data
    for item in report_data:
        row = [item['timestamp']]
        
        if report_type == 'weather':
            if options.get('temperature', False):
                row.append(item.get('temperature', ''))
            if options.get('humidity', False):
                row.append(item.get('humidity', ''))
            if options.get('soil_moisture', False):
                row.append(item.get('soil_moisture', ''))
            if options.get('wind_speed', False):
                row.append(item.get('wind_speed', ''))
            if options.get('pressure', False):
                row.append(item.get('pressure', ''))
        else:  # irrigation
            if options.get('pump_status', False):
                row.append('Running' if item.get('pump_status') else 'Stopped')
            if options.get('water_level', False):
                row.append(item.get('water_level', ''))
            if options.get('duration', False):
                row.append(item.get('duration', ''))
        
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={report_type}_report_{start_date}_to_{end_date}.csv"}
    )