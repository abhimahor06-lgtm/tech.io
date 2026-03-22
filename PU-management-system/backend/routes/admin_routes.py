"""
admin_routes.py
Admin Routes (Fixed & Secured Version)
Poornima University Management System
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db_connect import db
import os

admin_bp = Blueprint('admin', __name__)


def emit_event(event, data):
    # helper to emit via socketio if available
    try:
        sio = current_app.extensions.get('socketio')
        if sio:
            sio.emit(event, data, namespace='/')
    except Exception as _:
        pass



# ------------------ Helper: Admin Role Check ------------------ #

def admin_required():
    # identity is just the user id; role comes from the JWT claims
    claims = get_jwt()
    if claims.get("role") != "admin":
        return False
    return True


# ------------------ Admin Stats ------------------ #

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_admin_dashboard():
    """Combined data used by the admin overview panel.
    Returns basic counts plus pending approvals info for a single request.
    """

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        # helper to safely fetch single numeric counts
        def safe_count(query, params=()):
            row = db.fetch_one(query, params) or {}
            return int(row.get('count') or 0)

        student_count = safe_count('SELECT COUNT(*) as count FROM students')
        teacher_count = safe_count('SELECT COUNT(*) as count FROM teachers')
        hod_count = safe_count('SELECT COUNT(*) as count FROM hods')
        dept_count = safe_count('SELECT COUNT(*) as count FROM departments')

        pending_students = safe_count('SELECT COUNT(*) as count FROM students WHERE status=%s', ('pending',))
        pending_teachers = safe_count('SELECT COUNT(*) as count FROM teachers WHERE status=%s', ('pending',))
        pending_hods = safe_count('SELECT COUNT(*) as count FROM hods WHERE status=%s', ('pending',))
        total_pending = pending_students + pending_teachers + pending_hods

        # Grab latest pending approvals (combined across roles)
        recent = db.execute_query(
            """
            SELECT role, name, email, created_at
            FROM (
                SELECT 'student' as role, CONCAT(first_name,' ',last_name) as name, email, created_at
                FROM students WHERE status='pending'
                UNION ALL
                SELECT 'teacher' as role, CONCAT(first_name,' ',last_name) as name, email, created_at
                FROM teachers WHERE status='pending'
                UNION ALL
                SELECT 'hod' as role, CONCAT(first_name,' ',last_name) as name, email, created_at
                FROM hods WHERE status='pending'
            ) t
            ORDER BY created_at DESC
            LIMIT 5
            """, ()
        ) or []

        response_data = {
            'totalStudents': student_count,
            'totalTeachers': teacher_count,
            'totalHods': hod_count,
            'totalDepartments': dept_count,
            'pendingUsers': total_pending,
            'pendingBreakdown': {
                'students': pending_students,
                'teachers': pending_teachers,
                'hods': pending_hods
            },
            'recentApprovals': recent
        }

        return jsonify({
            'success': True,
            'data': response_data,
            **response_data
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error fetching dashboard data', 'error': str(e)}), 500


@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        student_count = db.fetch_one('SELECT COUNT(*) as count FROM students')['count']
        teacher_count = db.fetch_one('SELECT COUNT(*) as count FROM teachers')['count']
        hod_count = db.fetch_one('SELECT COUNT(*) as count FROM hods')['count']
        dept_count = db.fetch_one('SELECT COUNT(*) as count FROM departments')['count']

        return jsonify({
            'success': True,
            'totalStudents': student_count,
            'totalTeachers': teacher_count,
            'totalHods': hod_count,
            'totalDepartments': dept_count
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching stats'}), 500


# ------------------ Pending Approvals ------------------ #

@admin_bp.route('/pending-approvals', methods=['GET'])
@jwt_required()
def get_pending_approvals():

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        approvals = []

        students = db.execute_query("""
            SELECT s.id, u.username, CONCAT(s.first_name,' ',s.last_name) as name,
                   'student' as role, u.email, u.status, s.created_at as appliedDate
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE u.status='pending'
        """, ()) or []

        teachers = db.execute_query("""
            SELECT t.id, u.username, CONCAT(t.first_name,' ',t.last_name) as name,
                   'teacher' as role, u.email, u.status, t.created_at as appliedDate
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            WHERE u.status='pending'
        """, ()) or []

        hods = db.execute_query("""
            SELECT h.id, u.username, CONCAT(h.first_name,' ',h.last_name) as name,
                   'hod' as role, u.email, u.status, h.created_at as appliedDate
            FROM hods h
            JOIN users u ON h.user_id = u.id
            WHERE u.status='pending'
        """, ()) or []

        approvals.extend(students)
        approvals.extend(teachers)
        approvals.extend(hods)

        response_data = {'approvals': approvals}
        return jsonify({'success': True, 'data': response_data, **response_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error fetching approvals', 'error': str(e)}), 500


# ------------------ Approve User (SAFE VERSION) ------------------ #

@admin_bp.route('/approve-user/<string:role>/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_user(role, user_id):

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        if role not in ['student', 'teacher', 'hod']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400

        table = role + "s"  # student -> students

        updated = db.execute_update(
            f"UPDATE {table} SET status=%s WHERE id=%s",
            ('approved', user_id)
        )

        if updated == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        return jsonify({'success': True, 'message': 'User approved'}), 200

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error approving user'}), 500


# ------------------ Reject User (SAFE VERSION) ------------------ #

@admin_bp.route('/reject-user/<string:role>/<int:user_id>', methods=['POST'])
@jwt_required()
def reject_user(role, user_id):

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        if role not in ['student', 'teacher', 'hod']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400

        table = role + "s"

        deleted = db.execute_delete(
            f"DELETE FROM {table} WHERE id=%s",
            (user_id,)
        )

        if deleted == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        return jsonify({'success': True, 'message': 'User rejected'}), 200

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error rejecting user'}), 500


# ------------------ Create Department (With Validation) ------------------ #

@admin_bp.route('/departments', methods=['POST'])
@jwt_required()
def create_department():

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        name = data.get('name')
        hod_id = data.get('hodId')

        if not name:
            return jsonify({'success': False, 'message': 'Department name required'}), 400

        # Validate HOD if provided
        if hod_id:
            hod = db.fetch_one("SELECT id FROM hods WHERE id=%s", (hod_id,))
            if not hod:
                return jsonify({'success': False, 'message': 'Invalid HOD ID'}), 400

        dept_id = db.execute_insert(
            "INSERT INTO departments (name, hod_id) VALUES (%s,%s)",
            (name, hod_id)
        )

        return jsonify({
            'success': True,
            'message': 'Department created',
            'departmentId': dept_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error creating department'}), 500

# ================= Additional Read Endpoints for Admin Dashboard ================= #

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        role = request.args.get('role')
        if role and role not in ['student', 'teacher', 'hod', 'admin']:
            return jsonify({'success': False, 'message': 'Invalid role filter'}), 400

        if role:
            users = db.execute_query(
                "SELECT id, username, email, role, status FROM users WHERE role=%s",
                (role,)
            )
        else:
            users = db.execute_query(
                "SELECT id, username, email, role, status FROM users",
                ()
            )
        return jsonify({'success': True, 'users': users or []}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching users'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        user = db.fetch_one('SELECT id, role FROM users WHERE id=%s', (user_id,))
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Remove role-specific details first (foreign key dependencies)
        if user['role'] == 'student':
            db.execute_delete('DELETE FROM students WHERE user_id=%s', (user_id,))
        elif user['role'] == 'teacher':
            db.execute_delete('DELETE FROM teachers WHERE user_id=%s', (user_id,))
        elif user['role'] == 'hod':
            db.execute_delete('DELETE FROM hods WHERE user_id=%s', (user_id,))
        elif user['role'] == 'admin':
            db.execute_delete('DELETE FROM admins WHERE user_id=%s', (user_id,))

        db.execute_delete('DELETE FROM users WHERE id=%s', (user_id,))
        emit_event('user_update', {'id': user_id, 'action': 'deleted'})
        return jsonify({'success': True, 'message': 'User deleted'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error deleting user'}), 500


@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
def list_departments():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        depts = db.execute_query(
            "SELECT d.id, d.name, h.first_name AS hod_first, h.last_name AS hod_last "
            "FROM departments d LEFT JOIN hods h ON d.hod_id = h.id",
            ()
        ) or []
        for d in depts:
            d['hod'] = f"{d.pop('hod_first','') or ''} {d.pop('hod_last','') or ''}".strip()
        return jsonify({'success': True, 'departments': depts}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching departments'}), 500


@admin_bp.route('/subjects', methods=['GET'])
@jwt_required()
def list_subjects():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        subjects = db.execute_query(
            "SELECT id, subject_code, subject_name, credits, department, teacher_id FROM subjects",
            ()
        ) or []
        return jsonify({'success': True, 'subjects': subjects}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching subjects'}), 500


@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def system_analytics():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        student_count = db.fetch_one('SELECT COUNT(*) as count FROM students')['count']
        teacher_count = db.fetch_one('SELECT COUNT(*) as count FROM teachers')['count']
        avg_att = db.fetch_one(
            """
            SELECT ROUND(AVG(
                CASE
                    WHEN status='present' THEN 100
                    WHEN status='absent' THEN 0
                    ELSE 50
                END
            ), 2) as avg
            FROM attendance
            """,
            ()
        )['avg'] or 0
        avg_gpa = db.fetch_one('SELECT ROUND(AVG(current_cgpa),2) as avg FROM students')['avg'] or 0
        dropout_rate = db.fetch_one(
            "SELECT ROUND((SUM(CASE WHEN status='suspended' THEN 1 ELSE 0 END)/COUNT(*))*100,2) as rate FROM students",
            ()
        )['rate'] or 0

        return jsonify({
            'success': True,
            'totalStudents': student_count,
            'totalTeachers': teacher_count,
            'avgAttendance': avg_att,
            'avgGPA': avg_gpa,
            'dropoutRate': dropout_rate
        }), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching analytics'}), 500


@admin_bp.route('/ai-insights', methods=['GET'])
@jwt_required()
def ai_insights():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        at_risk = db.fetch_one(
            """
            SELECT COUNT(*) as count FROM (
                SELECT s.id,
                       AVG(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as avg_att,
                       AVG(m.total) as avg_marks
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id
                LEFT JOIN marks m ON s.id = m.student_id
                GROUP BY s.id
            ) t
            WHERE (avg_att < 0.5 OR avg_marks < 40)
            """,
            ()
        )['count'] or 0
        top_performers = db.fetch_one(
            """
            SELECT COUNT(*) as count FROM (
                SELECT s.id, AVG(m.total) as avg_marks
                FROM students s
                LEFT JOIN marks m ON s.id = m.student_id
                GROUP BY s.id
            ) t
            WHERE avg_marks > 80
            """,
            ()
        )['count'] or 0
        low_attendance = db.fetch_one(
            """
            SELECT COUNT(*) as count FROM (
                SELECT s.id, AVG(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as avg_att
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id
                GROUP BY s.id
            ) t
            WHERE avg_att < 0.75
            """,
            ()
        )['count'] or 0
        return jsonify({
            'success': True,
            'atRisk': at_risk,
            'topPerformers': top_performers,
            'lowAttendance': low_attendance
        }), 200
    except Exception as e:
        # If the optional analytics tables don't exist yet (e.g., 'marks'),
        # return zeroed insights instead of crashing the endpoint.
        err_text = str(e).lower()
        if '1146' in err_text or 'doesn\'t exist' in err_text:
            return jsonify({
                'success': True,
                'atRisk': 0,
                'topPerformers': 0,
                'lowAttendance': 0,
                'message': 'Analytics data not available yet'
            }), 200

        print(e)
        return jsonify({'success': False, 'message': 'Error fetching AI insights'}), 500


@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_logs():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    logs = []
    try:
        if os.path.exists('logs/server.log'):
            with open('logs/server.log', 'r') as f:
                lines = f.readlines()[-50:]
                logs = [line.strip() for line in lines]
    except Exception as e:
        print('Log read error:', e)
    return jsonify({'success': True, 'logs': logs}), 200

# Backup endpoints could be added later or stubbed

# ------------------ Create Subject (With FK Validation) ------------------ #

@admin_bp.route('/subjects', methods=['POST'])
@jwt_required()
def create_subject():

    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()

        # Validate Department
        dept = db.fetch_one(
            "SELECT name FROM departments WHERE name=%s",
            (data.get('department'),)
        )
        if not dept:
            return jsonify({'success': False, 'message': 'Invalid department'}), 400

        # Validate Teacher
        if data.get('teacherId'):
            teacher = db.fetch_one(
                "SELECT id FROM teachers WHERE id=%s",
                (data.get('teacherId'),)
            )
            if not teacher:
                return jsonify({'success': False, 'message': 'Invalid teacher ID'}), 400

        subject_id = db.execute_insert("""
            INSERT INTO subjects (subject_code, subject_name, credits, department, teacher_id)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            data.get('subjectCode'),
            data.get('subjectName'),
            data.get('credits', 3),
            data.get('department'),
            data.get('teacherId')
        ))

        return jsonify({
            'success': True,
            'message': 'Subject created',
            'subjectId': subject_id
        }), 201

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error creating subject'}), 500


# ------------------ Dashboard & utility endpoints ------------------ #

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_summary():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        # reuse stats logic
        student_count = db.fetch_one('SELECT COUNT(*) as count FROM students')['count']
        teacher_count = db.fetch_one('SELECT COUNT(*) as count FROM teachers')['count']
        hod_count = db.fetch_one('SELECT COUNT(*) as count FROM hods')['count']
        dept_count = db.fetch_one('SELECT COUNT(*) as count FROM departments')['count']
        pending = db.execute_query(
            "SELECT id FROM users WHERE status='pending'",
            ()
        ) or []
        # also count HODs, teachers, students pending (for detailed breakdown)
        pending_hods = db.fetch_one('SELECT COUNT(*) as count FROM hods WHERE status="pending"')['count'] or 0
        pending_teachers = db.fetch_one('SELECT COUNT(*) as count FROM teachers WHERE status="pending"')['count'] or 0
        pending_students = db.fetch_one('SELECT COUNT(*) as count FROM students WHERE status="pending"')['count'] or 0
        return jsonify({
            'success': True,
            'totalStudents': student_count,
            'totalTeachers': teacher_count,
            'totalHods': hod_count,
            'totalDepartments': dept_count,
            'pendingUsers': len(pending),
            'pendingBreakdown': {
                'students': pending_students,
                'teachers': pending_teachers,
                'hods': pending_hods
            }
        }), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching dashboard summary'}), 500


@admin_bp.route('/pending-users', methods=['GET'])
@jwt_required()
def pending_users():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        pending = []
        # get pending students
        students = db.execute_query(
            "SELECT u.id, u.username, u.email, 'student' as role, u.status FROM users u JOIN students s ON u.id=s.user_id WHERE u.status='pending'",
            ()
        ) or []
        pending.extend(students)
        # get pending teachers
        teachers = db.execute_query(
            "SELECT u.id, u.username, u.email, 'teacher' as role, u.status FROM users u JOIN teachers t ON u.id=t.user_id WHERE u.status='pending'",
            ()
        ) or []
        pending.extend(teachers)
        # get pending hods
        hods = db.execute_query(
            "SELECT u.id, u.username, u.email, 'hod' as role, u.status FROM users u JOIN hods h ON u.id=h.user_id WHERE u.status='pending'",
            ()
        ) or []
        pending.extend(hods)
        return jsonify({'success': True, 'users': pending}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching pending users'}), 500


@admin_bp.route('/approve/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_short(user_id):
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        updated = db.execute_update(
            "UPDATE users SET status='approved' WHERE id=%s",
            (user_id,)
        )
        if updated == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        emit_event('user_update', {'id': user_id, 'action': 'approved'})
        return jsonify({'success': True, 'message': 'User approved'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error approving user'}), 500


@admin_bp.route('/reject/<int:user_id>', methods=['POST'])
@jwt_required()
def reject_short(user_id):
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        deleted = db.execute_delete(
            "DELETE FROM users WHERE id=%s",
            (user_id,)
        )
        if deleted == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        emit_event('user_update', {'id': user_id, 'action': 'rejected'})
        return jsonify({'success': True, 'message': 'User rejected'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error rejecting user'}), 500


@admin_bp.route('/attendance', methods=['GET'])
@jwt_required()
def attendance_data():
    if not admin_required():
        return jsonify({'message': 'Unauthorized'}), 403
    try:
        records = db.execute_query(
            "SELECT DATE(date) as date, \
                    SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as present, \
                    SUM(CASE WHEN status='absent' THEN 1 ELSE 0 END) as absent \
             FROM attendance \
             GROUP BY DATE(date) \
             ORDER BY DATE(date) DESC \
             LIMIT 30",
            ()
        ) or []
        # if no records, return demo data for chart
        if not records:
            from datetime import datetime, timedelta
            import random
            records = []
            for i in range(15):
                date = (datetime.now() - timedelta(days=i)).date()
                present = random.randint(20, 80)
                absent = random.randint(5, 30)
                records.append({'date': date, 'present': present, 'absent': absent})
        # convert dates to string
        for r in records:
            r['date'] = r['date'].strftime('%Y-%m-%d') if hasattr(r['date'], 'strftime') else str(r['date'])
        return jsonify({'success': True, 'records': records}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Error fetching attendance data'}), 500