"""
attendance_routes.py
Attendance endpoints for teachers/HODs/students
Poornima University Management System
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db_connect import db

attendance_bp = Blueprint('attendance', __name__)


def teacher_or_hod():
    claims = get_jwt()
    return claims.get('role') in ('teacher', 'hod', 'admin')


# ----- list of students visible to the caller -----
@attendance_bp.route('/students', methods=['GET'])
@jwt_required()
def list_students():
    claims = get_jwt()
    role = claims.get('role')
    user = int(get_jwt_identity())

    if role == 'teacher':
        # a teacher should only see students in subjects they teach
        students = db.execute_query(
            """SELECT s.id, CONCAT(s.first_name,' ',s.last_name) AS name
               FROM students s
               JOIN subjects sub ON sub.department = s.department
               WHERE sub.teacher_id = %s""", (user,)
        ) or []
    elif role == 'hod':
        hod = db.fetch_one("SELECT department FROM hods WHERE id = %s", (user,))
        students = db.execute_query(
            "SELECT id, CONCAT(first_name,' ',last_name) AS name FROM students WHERE department = %s",
            (hod['department'],)
        ) or []
    elif role == 'admin':
        students = db.execute_query(
            "SELECT id, CONCAT(first_name,' ',last_name) AS name FROM students"
        ) or []
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    return jsonify({'success': True, 'students': students}), 200


# ----- record attendance entries -----
@attendance_bp.route('', methods=['POST'])
@jwt_required()
def save_attendance():
    if not teacher_or_hod():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    date = data.get('date')
    entries = data.get('attendance', [])

    if not date or not isinstance(entries, list):
        return jsonify({'success': False, 'message': 'date and attendance array required'}), 400

    marker = get_jwt_identity()
    role = get_jwt().get('role')

    try:
        for e in entries:
            # each entry must have id and status
            if 'id' not in e or 'status' not in e:
                continue
            db.execute_insert(
                """INSERT INTO attendance
                   (student_id, subject, `date`, status, marked_by, role)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (e['id'], e.get('subject', ''), date, e['status'].lower(), marker, role)
            )
        db.commit()
        try:
            # emit socket event if socketio is available
            from server import socketio
            socketio.emit('attendance_update', {'date': date}, namespace='/')
        except Exception:
            pass
        return jsonify({'success': True, 'message': 'Attendance recorded'}), 200
    except Exception as err:
        db.rollback()
        print('Attendance save error:', err)
        return jsonify({'success': False, 'message': 'Error saving attendance'}), 500


# ----- attendance history for a student -----
@attendance_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def attendance_by_student(student_id):
    claims = get_jwt()
    role = claims.get('role')
    user = int(get_jwt_identity())
    if role == 'student' and user != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    records = db.execute_query(
        "SELECT id, subject, `date`, status, marked_by, role "
        "FROM attendance WHERE student_id = %s ORDER BY `date` DESC",
        (student_id,)
    ) or []
    return jsonify({'success': True, 'attendance': records}), 200


# ----- attendance by date (for reports) -----
@attendance_bp.route('/date', methods=['GET'])
@jwt_required()
def attendance_by_date():
    date = request.args.get('date')
    if not date:
        return jsonify({'success': False, 'message': 'date query parameter required'}), 400

    records = db.execute_query(
        """SELECT a.*, CONCAT(s.first_name,' ',s.last_name) AS student_name
           FROM attendance a
           JOIN students s ON s.id = a.student_id
           WHERE a.`date` = %s""", (date,)
    ) or []
    return jsonify({'success': True, 'attendance': records}), 200
