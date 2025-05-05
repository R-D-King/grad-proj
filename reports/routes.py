from flask import Blueprint, jsonify, request, current_app, send_file
from datetime import datetime
import os
import csv
import tempfile

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report_route():
    """Generate a report based on the specified parameters."""
    from .controllers import generate_report
    
    data = request.json
    report_type = data.get('type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    options = data.get('options', {})
    
    result = generate_report(report_type, start_date, end_date, options)
    return jsonify(result)

@reports_bp.route('/api/reports/download', methods=['POST'])
def download_report():
    """Download a report as CSV."""
    data = request.json
    report_data = data.get('data', [])
    report_type = data.get('type', 'report')
    
    if not report_data:
        return jsonify({"status": "error", "message": "No data to download"}), 400
    
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.csv')
    try:
        with os.fdopen(fd, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            if report_data:
                writer.writerow(report_data[0].keys())
                
                # Write data rows
                for row in report_data:
                    writer.writerow(row.values())
        
        return send_file(
            path,
            as_attachment=True,
            download_name=f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500