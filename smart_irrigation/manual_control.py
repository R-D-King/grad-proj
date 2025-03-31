from flask import request, jsonify
from shared.config import db
from .models import IrrigationData
from datetime import datetime
from . import irrigation_app
from shared.socketio import socketio

# Manual pump control (start/stop)
@irrigation_app.route('/api/irrigation/manual', methods=['POST'])
def manual_pump_control():
    data = request.json
    action = data.get('action')  # 'start' or 'stop'
    water_level = data.get('water_level', 0)  # water level (optional)

    if action not in ['start', 'stop']:
        return jsonify({"message": "Invalid action"}), 400

    if action == 'start':
        # Record pump start in database
        new_data = IrrigationData(
            pump_status=True,
            water_level=water_level,
            pump_duration=0  # Will be updated when stopped
        )
        db.session.add(new_data)
        db.session.commit()

        # Send event to update UI
        socketio.emit('update_irrigation', {
            "pump_status": True,
            "water_level": water_level
        })

        return jsonify({"message": "Pump started manually"}), 200

    elif action == 'stop':
        # If pump is stopped, calculate duration
        last_start_entry = IrrigationData.query.filter_by(pump_status=True).order_by(IrrigationData.timestamp.desc()).first()
        if last_start_entry:
            duration = (datetime.now() - last_start_entry.timestamp).total_seconds()
            last_start_entry.pump_duration = duration
            last_start_entry.pump_status = False  # Update pump status to off
            db.session.commit()

            # Send event to update UI
            socketio.emit('update_irrigation', {
                "pump_status": False,
                "water_level": water_level
            })

            return jsonify({"message": "Pump stopped manually", "duration": duration}), 200
        else:
            return jsonify({"message": "No active pump found"}), 404