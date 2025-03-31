from datetime import datetime
from flask import Blueprint, jsonify, current_app
import logging

time_utils = Blueprint('time_utils', __name__)

# Configure logging to disable specific route logging
class NoServerTimeFilter(logging.Filter):
    def filter(self, record):
        return 'GET /api/server-time/display' not in record.getMessage()

# Apply the filter to the Werkzeug logger
logging.getLogger('werkzeug').addFilter(NoServerTimeFilter())

@time_utils.route('/api/server-time/display')
def get_display_time():
    """Return formatted server time for display"""
    now = datetime.now()
    return jsonify({
        'formatted_time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%Y-%m-%d'),
        'full_datetime': now.strftime('%Y-%m-%d %H:%M:%S')
    })

@time_utils.route('/api/server-time')
def get_server_time():
    """Return the current server time"""
    now = datetime.now()
    return jsonify({
        'timestamp': now.timestamp(),
        'formatted': now.strftime('%Y-%m-%d %H:%M:%S'),
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S')
    })

@time_utils.route('/api/server-time/formatted')
def get_formatted_server_time():
    """Return formatted server time"""
    now = datetime.now()
    return jsonify({
        'formatted_time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%Y-%m-%d')
    })

def is_time_to_run_schedule(schedule):
    """Check if it's time to run a schedule based on current server time"""
    now = datetime.now()
    schedule_time = schedule.start_time.strftime('%H:%M')
    current_time = now.strftime('%H:%M')
    
    # Check if it's time to run this schedule and it's active
    return schedule_time == current_time and schedule.active