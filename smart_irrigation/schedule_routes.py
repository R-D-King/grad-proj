from flask import request, jsonify
from shared.config import db
from .models import IrrigationSchedule
from datetime import datetime
from . import irrigation_app
from shared.socketio import socketio

# Add new schedule
@irrigation_app.route('/api/irrigation/schedule', methods=['POST'])
def add_schedule():
    data = request.json
    start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    duration = float(data['duration'])

    new_schedule = IrrigationSchedule(
        start_time=start_time,
        duration=duration,
        active=True
    )
    db.session.add(new_schedule)
    db.session.commit()

    return jsonify({"message": "Schedule added successfully"}), 201

# Update schedule
@irrigation_app.route('/api/irrigation/schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    schedule = IrrigationSchedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404
    
    data = request.json
    if 'start_time' in data:
        schedule.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    if 'duration' in data:
        schedule.duration = float(data['duration'])
    if 'active' in data:
        schedule.active = data['active']
    
    db.session.commit()
    
    socketio.emit('schedule_updated', {
        "id": schedule.id,
        "preset_id": schedule.preset_id,
        "start_time": schedule.start_time.strftime('%H:%M'),
        "duration": schedule.duration,
        "active": schedule.active
    })
    
    return jsonify({"message": "Schedule updated successfully"}), 200

# Delete schedule
@irrigation_app.route('/api/irrigation/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    schedule = IrrigationSchedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404
    
    preset_id = schedule.preset_id
    db.session.delete(schedule)
    db.session.commit()
    
    socketio.emit('schedule_deleted', {
        "id": schedule_id,
        "preset_id": preset_id
    })
    
    return jsonify({"message": "Schedule deleted successfully"}), 200