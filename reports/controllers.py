from datetime import datetime, timedelta
from flask import jsonify
from shared.database import db
from irrigation.models import IrrigationLog
from weather.models import WeatherData

def generate_report(report_type, start_date, end_date, options):
    """Generate a report based on the specified parameters."""
    
    # Convert string dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # Add one day to end_date to include the entire day
        end_date = end_date + timedelta(days=1)
    except ValueError:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}
    
    # Generate the appropriate report
    if report_type == 'weather':
        return generate_weather_report(start_date, end_date, options)
    elif report_type == 'irrigation':
        return generate_irrigation_report(start_date, end_date, options)
    else:
        return {"status": "error", "message": "Invalid report type."}

def generate_weather_report(start_date, end_date, options):
    """Generate a weather report."""
    
    # Build the query
    query = db.session.query(WeatherData).filter(
        WeatherData.timestamp >= start_date,
        WeatherData.timestamp < end_date
    ).order_by(WeatherData.timestamp.desc())
    
    # Execute the query
    data = query.all()
    
    # If no data, return empty list
    if not data:
        return []
    
    # Convert to list of dictionaries with only the selected options
    result = []
    for item in data:
        entry = {
            'timestamp': item.timestamp.isoformat()
        }
        
        # Only include selected options
        if options.get('temperature', False):
            entry['temperature'] = item.temperature
        
        if options.get('humidity', False):
            entry['humidity'] = item.humidity
        
        if options.get('soil_moisture', False):
            entry['soil_moisture'] = item.soil_moisture
        
        if options.get('wind_speed', False):
            entry['wind_speed'] = item.wind_speed
        
        if options.get('pressure', False):
            entry['pressure'] = item.pressure
        
        result.append(entry)
    
    return result

def generate_irrigation_report(start_date, end_date, options):
    """Generate an irrigation report."""
    
    # Build the query
    query = db.session.query(IrrigationLog).filter(
        IrrigationLog.timestamp >= start_date,
        IrrigationLog.timestamp < end_date
    ).order_by(IrrigationLog.timestamp.desc())
    
    # Execute the query
    data = query.all()
    
    # If no data, return empty list
    if not data:
        return []
    
    # Convert to list of dictionaries with only the selected options
    result = []
    for item in data:
        entry = {
            'timestamp': item.timestamp.isoformat()
        }
        
        # Only include selected options
        if options.get('pump_status', False):
            entry['pump_status'] = item.pump_status
        
        if options.get('water_level', False):
            entry['water_level'] = item.water_level
        
        if options.get('duration', False):
            entry['duration'] = item.duration
        
        result.append(entry)
    
    return result