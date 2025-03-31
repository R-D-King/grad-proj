from flask import request, jsonify
from shared.config import db
from .models import IrrigationPreset, IrrigationSchedule
from datetime import datetime
from . import irrigation_app
from shared.socketio import socketio

# Add new preset
@irrigation_app.route('/api/irrigation/preset', methods=['POST'])
def add_preset():
    data = request.json
    name = data['name']
    schedules = data.get('schedules', [])

    new_preset = IrrigationPreset(name=name)
    db.session.add(new_preset)

    for schedule in schedules:
        start_time = datetime.strptime(schedule['start_time'], '%H:%M').time()
        duration = float(schedule['duration'])
        new_schedule = IrrigationSchedule(
            start_time=start_time,
            duration=duration,
            active=True,
            preset=new_preset
        )
        db.session.add(new_schedule)

    db.session.commit()
    return jsonify({"message": "Preset added successfully"}), 201

# Get all presets
@irrigation_app.route('/api/irrigation/presets', methods=['GET'])
def get_presets():
    presets = IrrigationPreset.query.all()
    presets_list = []
    for preset in presets:
        schedules = []
        for schedule in preset.schedules:
            schedules.append({
                "id": schedule.id,
                "start_time": schedule.start_time.strftime('%H:%M'),
                "duration": schedule.duration,
                "active": schedule.active
            })
        
        presets_list.append({
            "id": preset.id,
            "name": preset.name,
            "schedules": schedules
        })
    return jsonify(presets_list), 200

# Get specific preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>', methods=['GET'])
def get_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404

    schedules = []
    for schedule in preset.schedules:
        schedules.append({
            "id": schedule.id,
            "start_time": schedule.start_time.strftime('%H:%M'),
            "duration": schedule.duration,
            "active": schedule.active
        })

    return jsonify({
        "id": preset.id,
        "name": preset.name,
        "schedules": schedules
    }), 200

# Update preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>', methods=['PUT'])
def update_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404
    
    data = request.json
    if 'name' in data:
        preset.name = data['name']
    
    db.session.commit()
    
    socketio.emit('preset_updated', {
        "id": preset.id,
        "name": preset.name
    })
    
    return jsonify({"message": "Preset updated successfully"}), 200

# Delete preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404
    
    db.session.delete(preset)
    db.session.commit()
    
    socketio.emit('preset_deleted', {
        "id": preset_id
    })
    
    return jsonify({"message": "Preset deleted successfully"}), 200

# Activate preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>/activate', methods=['POST'])
def activate_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404
    
    # Update activation status
    preset.active = True
    
    # Deactivate other presets
    other_presets = IrrigationPreset.query.filter(IrrigationPreset.id != preset_id).all()
    for other_preset in other_presets:
        other_preset.active = False
    
    db.session.commit()
    
    socketio.emit('preset_activated', {
        "id": preset_id
    })
    
    return jsonify({"message": "Preset activated successfully"}), 200