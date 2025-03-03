from flask import render_template, request, redirect, url_for, jsonify
from shared.config import db
from .models import IrrigationPreset, IrrigationSchedule, IrrigationData
from datetime import datetime, time, timedelta
import csv
from io import StringIO
from . import irrigation_app
from shared.socketio import socketio

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
    data = request.json
    new_data = IrrigationData(
        pump_status=data['pump_status'],
        water_level=data['water_level']
    )
    db.session.add(new_data)
    db.session.commit()

    # إرسال حدث لتحديث الواجهة
    socketio.emit('update_irrigation', {
        "pump_status": data['pump_status'],
        "water_level": data['water_level']
    })

    return jsonify({"message": "Irrigation data added successfully"}), 201

# التحكم في المضخة بناءً على نسبة الرطوبة
@irrigation_app.route('/api/irrigation/control', methods=['POST'])
def control_pump():
    data = request.json
    moisture_level = data['moisture_level']
    schedule_active = data['schedule_active']  # هل الجدول نشط؟

    # تحديد حالة المضخة بناءً على نسبة الرطوبة والجدول
    if schedule_active and moisture_level < 30:  # إذا كانت الرطوبة أقل من 30% والجدول نشط
        pump_status = True
    elif moisture_level > 70:  # إذا كانت الرطوبة أعلى من 70%
        pump_status = False
    else:
        pump_status = False  # إيقاف المضخة في الحالات الأخرى

    # حفظ حالة المضخة في قاعدة البيانات
    new_data = IrrigationData(
        pump_status=pump_status,
        water_level=data['water_level']
    )
    db.session.add(new_data)
    db.session.commit()

    # إرسال حدث لتحديث الواجهة
    socketio.emit('update_irrigation', {
        "pump_status": pump_status,
        "water_level": data['water_level']
    })

    return jsonify({"pump_status": pump_status}), 200

# تشغيل أو إيقاف المضخة يدويًا
@irrigation_app.route('/api/irrigation/manual', methods=['POST'])
def manual_pump_control():
    data = request.json
    action = data.get('action')  # 'start' أو 'stop'
    water_level = data.get('water_level', 0)  # مستوى المياه (اختياري)

    if action not in ['start', 'stop']:
        return jsonify({"message": "Invalid action"}), 400

    # تسجيل حالة المضخة في قاعدة البيانات
    new_data = IrrigationData(
        pump_status=(action == 'start'),
        water_level=water_level,
        pump_duration=0  # سيتم تحديثه لاحقًا
    )
    db.session.add(new_data)
    db.session.commit()

    # إرسال حدث لتحديث الواجهة
    socketio.emit('update_irrigation', {
        "pump_status": (action == 'start'),
        "water_level": water_level
    })

    # إذا كانت المضخة تعمل، قم بحساب مدة التشغيل
    if action == 'start':
        return jsonify({"message": "Pump started manually"}), 200
    else:
        # إذا تم إيقاف المضخة، قم بحساب مدة التشغيل
        last_start_entry = IrrigationData.query.filter_by(pump_status=True).order_by(IrrigationData.timestamp.desc()).first()
        if last_start_entry:
            duration = (datetime.utcnow() - last_start_entry.timestamp).total_seconds()
            last_start_entry.pump_duration = duration
            db.session.commit()
            return jsonify({"message": "Pump stopped manually", "duration": duration}), 200
        else:
            return jsonify({"message": "No active pump found"}), 404

# إنشاء تقارير CSV
@irrigation_app.route('/api/irrigation/report', methods=['GET'])
def generate_irrigation_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    download = request.args.get('download', 'false').lower() == 'true'

    # تحويل التواريخ من نص إلى كائن datetime
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    # إذا لم يتم تحديد التواريخ، استخدم آخر 7 أيام كافتراضي
    if not start_date or not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

    # جلب البيانات من قاعدة البيانات
    data = IrrigationData.query.filter(IrrigationData.timestamp.between(start_date, end_date)).all()

    if data:
        # إذا طلب المستخدم تحميل التقرير كملف CSV
        if download:
            output = StringIO()
            writer = csv.writer(output)

            # كتابة رأس الملف
            writer.writerow(["Timestamp", "Pump Status", "Water Level (%)", "Pump Duration (seconds)"])

            # كتابة البيانات
            for entry in data:
                writer.writerow([
                    entry.timestamp,
                    "ON" if entry.pump_status else "OFF",  # تحويل Boolean إلى نص
                    entry.water_level,
                    entry.pump_duration
                ])

            output.seek(0)
            return output.getvalue(), 200, {
                "Content-Disposition": f"attachment; filename=irrigation_report_{start_date_str}_to_{end_date_str}.csv",
                "Content-type": "text/csv"
            }
        else:
            # عرض التقرير في الصفحة
            report = []
            for entry in data:
                report.append({
                    "timestamp": entry.timestamp,
                    "pump_status": "ON" if entry.pump_status else "OFF",
                    "water_level": entry.water_level,
                    "pump_duration": entry.pump_duration
                })
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
        presets_list.append({
            "id": preset.id,
            "name": preset.name
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
            "start_time": schedule.start_time.strftime('%H:%M'),
            "duration": schedule.duration
        })

    return jsonify({
        "name": preset.name,
        "schedules": schedules
    }), 200