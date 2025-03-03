from flask import request, jsonify
from shared.config import db
from .models import IrrigationData
from datetime import datetime, timedelta
import csv
from io import StringIO
from . import irrigation_app, socketio  # استيراد Blueprint و socketio

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

    return jsonify({"message": "Data added successfully"}), 201

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
    # الحصول على نطاق التاريخ من الطلب
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
            writer.writerow(["Timestamp", "Pump Status", "Water Level", "Pump Duration (seconds)"])

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