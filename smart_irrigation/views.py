from flask import render_template, request, redirect, url_for, jsonify
from shared.config import db
from .models import IrrigationPreset, IrrigationSchedule, IrrigationData
from datetime import datetime, timedelta
import csv
from io import StringIO
from . import irrigation_app
from shared.socketio import socketio

# متغير لتخزين مستوى الماء السابق
previous_water_level = None

# عرض الصفحة الرئيسية مع قائمة الـ presets
@irrigation_app.route('/')
def index():
    presets = IrrigationPreset.query.all()
    return render_template('index.html', presets=presets)

# اختيار Preset وعرض جدول الري الخاص به
@irrigation_app.route('/irrigation/select_preset', methods=['POST'])
def select_preset():
    preset_id = request.form.get('preset_id')
    if preset_id:
        selected_preset = IrrigationPreset.query.get(preset_id)
        return render_template('index.html', presets=IrrigationPreset.query.all(), selected_preset=selected_preset)
    return redirect(url_for('index'))

# إضافة بيانات الري
@irrigation_app.route('/api/irrigation', methods=['POST'])
def add_irrigation_data():
    global previous_water_level
    data = request.json
    current_water_level = data['water_level']

    # تحقق من التغير في مستوى الماء
    if previous_water_level is not None:
        change_percentage = abs(current_water_level - previous_water_level) / previous_water_level * 100
        if change_percentage >= 5:
            # سجل التغير في قاعدة البيانات
            new_data = IrrigationData(
                pump_status=data['pump_status'],
                water_level=current_water_level
            )
            db.session.add(new_data)
            db.session.commit()

    previous_water_level = current_water_level

    # إرسال حدث لتحديث الواجهة
    socketio.emit('update_irrigation', {
        "pump_status": data['pump_status'],
        "water_level": current_water_level
    })

    return jsonify({"message": "Irrigation data added successfully"}), 201

# تشغيل أو إيقاف المضخة يدويًا
@irrigation_app.route('/api/irrigation/manual', methods=['POST'])
def manual_pump_control():
    data = request.json
    action = data.get('action')  # 'start' أو 'stop'
    water_level = data.get('water_level', 0)  # مستوى المياه (اختياري)

    if action not in ['start', 'stop']:
        return jsonify({"message": "Invalid action"}), 400

    if action == 'start':
        # تسجيل حالة تشغيل المضخة في قاعدة البيانات
        new_data = IrrigationData(
            pump_status=True,
            water_level=water_level,
            pump_duration=0  # سيتم تحديثه عند الإيقاف
        )
        db.session.add(new_data)
        db.session.commit()

        # إرسال حدث لتحديث الواجهة
        socketio.emit('update_irrigation', {
            "pump_status": True,
            "water_level": water_level
        })

        return jsonify({"message": "Pump started manually"}), 200

    elif action == 'stop':
        # إذا تم إيقاف المضخة، قم بحساب مدة التشغيل
        last_start_entry = IrrigationData.query.filter_by(pump_status=True).order_by(IrrigationData.timestamp.desc()).first()
        if last_start_entry:
            duration = (datetime.now() - last_start_entry.timestamp).total_seconds()
            last_start_entry.pump_duration = duration
            last_start_entry.pump_status = False  # تحديث حالة المضخة إلى إيقاف
            db.session.commit()

            # إرسال حدث لتحديث الواجهة
            socketio.emit('update_irrigation', {
                "pump_status": False,
                "water_level": water_level
            })

            return jsonify({"message": "Pump stopped manually", "duration": duration}), 200
        else:
            return jsonify({"message": "No active pump found"}), 404
# تقرير ببيانات الري    
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
    
# إضافة جدول ري جديد
@irrigation_app.route('/api/irrigation/schedule', methods=['POST'])
def add_schedule():
    data = request.json
    start_time = datetime.strptime(data['start_time'], '%H:%M').time()  # تحويل النص إلى وقت
    duration = float(data['duration'])  # مدة التشغيل (بالثواني)

    new_schedule = IrrigationSchedule(
        start_time=start_time,
        duration=duration,
        active=True
    )
    db.session.add(new_schedule)
    db.session.commit()

    return jsonify({"message": "Schedule added successfully"}), 201

# إضافة preset جديد
@irrigation_app.route('/api/irrigation/preset', methods=['POST'])
def add_preset():
    data = request.json
    name = data['name']
    schedules = data.get('schedules', [])  # قائمة بجداول الري

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

# جلب جميع الـ presets
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

# جلب الـ preset المحدد
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

# تحديث preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>', methods=['PUT'])
def update_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404
    
    data = request.json
    if 'name' in data:
        preset.name = data['name']
    
    db.session.commit()
    
    # إرسال حدث لتحديث الواجهة
    socketio.emit('preset_updated', {
        "id": preset.id,
        "name": preset.name
    })
    
    return jsonify({"message": "Preset updated successfully"}), 200

# حذف preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404
    
    db.session.delete(preset)
    db.session.commit()
    
    # إرسال حدث لتحديث الواجهة
    socketio.emit('preset_deleted', {
        "id": preset_id
    })
    
    return jsonify({"message": "Preset deleted successfully"}), 200

# تحديث جدول الري
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
    
    # إرسال حدث لتحديث الواجهة
    socketio.emit('schedule_updated', {
        "id": schedule.id,
        "preset_id": schedule.preset_id,
        "start_time": schedule.start_time.strftime('%H:%M'),
        "duration": schedule.duration,
        "active": schedule.active
    })
    
    return jsonify({"message": "Schedule updated successfully"}), 200

# حذف جدول الري
@irrigation_app.route('/api/irrigation/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    schedule = IrrigationSchedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404
    
    preset_id = schedule.preset_id
    db.session.delete(schedule)
    db.session.commit()
    
    # إرسال حدث لتحديث الواجهة
    socketio.emit('schedule_deleted', {
        "id": schedule_id,
        "preset_id": preset_id
    })
    
    return jsonify({"message": "Schedule deleted successfully"}), 200

# تفعيل preset
@irrigation_app.route('/api/irrigation/preset/<int:preset_id>/activate', methods=['POST'])
def activate_preset(preset_id):
    preset = IrrigationPreset.query.get(preset_id)
    if not preset:
        return jsonify({"message": "Preset not found"}), 404
    
    # تحديث حالة التفعيل للـ preset
    preset.active = True
    
    # إلغاء تفعيل باقي الـ presets
    other_presets = IrrigationPreset.query.filter(IrrigationPreset.id != preset_id).all()
    for other_preset in other_presets:
        other_preset.active = False
    
    db.session.commit()
    
    # إرسال حدث لتحديث الواجهة
    socketio.emit('preset_activated', {
        "id": preset_id
    })
    
    return jsonify({"message": "Preset activated successfully"}), 200