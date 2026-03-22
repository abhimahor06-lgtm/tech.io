"""
hod_routes.py
HOD Routes
Poornima University Management System
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db_connect import db

hod_bp = Blueprint('hod', __name__)


# ============================================================================
# Helper: Validate HOD Access
# ============================================================================

def get_current_hod():
    claims = get_jwt()
    user_id_raw = get_jwt_identity()

    # debug tracing (remove if no longer needed)
    print('HOD identity:', user_id_raw, 'claims:', claims)

    if claims.get('role') != 'hod':
        return None, jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Ensure we use an integer user_id for lookups and formatting
    try:
        user_id = int(user_id_raw)
    except Exception:
        user_id = user_id_raw

    # HOD profile is linked via user_id, not hods.id (id is its own PK)
    hod = db.fetch_one("SELECT id, department FROM hods WHERE user_id = %s", (user_id,))
    if not hod:
        # Auto-create a minimal HOD profile if it doesn't exist (useful for seed/demo data).
        user = db.fetch_one("SELECT username, email FROM users WHERE id = %s", (user_id,))
        if not user:
            return None, jsonify({'success': False, 'message': 'HOD not found'}), 404

        username = user.get('username', '')
        first_name, _, last_name = username.partition(' ')

        # Ensure department exists (FK requires it). Use an existing department if available.
        dept = db.fetch_one("SELECT name FROM departments LIMIT 1")
        if dept:
            department = dept['name']
        else:
            department = 'Unassigned'
            # create a placeholder department record if missing
            try:
                db.execute_insert("INSERT INTO departments (name) VALUES (%s)", (department,))
            except Exception:
                pass

        employee_id = f"HOD{int(user_id):04d}" if isinstance(user_id, int) else f"HOD{user_id}"

        hod_id = db.execute_insert(
            """INSERT INTO hods (user_id, first_name, last_name, email, phone, employee_id, department, qualification, status) 
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, first_name or username, last_name or '', user.get('email'), None, employee_id, department, None, 'approved')
        )
        hod = {'id': hod_id, 'department': department}

    return hod, None, None


# ============================================================================
# DASHBOARD DATA
# ============================================================================

@hod_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_department_data():
    try:
        hod, error_response, status = get_current_hod()
        if error_response:
            return error_response, status

        department = hod['department']

        teacher_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM teachers WHERE department = %s",
            (department,)
        ) or {'count': 0}

        student_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM students WHERE department = %s",
            (department,)
        ) or {'count': 0}

        subject_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM subjects WHERE department = %s",
            (department,)
        ) or {'count': 0}

        # compute average attendance percent for department
        attendance_avg = db.fetch_one(
            """
            SELECT ROUND(AVG(
                CASE
                    WHEN a.status = 'present' THEN 100
                    WHEN a.status = 'absent' THEN 0
                    ELSE 50
                END
            ), 2) as avg
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE s.department = %s
            """, (department,)) or {'avg': 0}

        return jsonify({
            'success': True,
            'department': department,
            'teacherCount': teacher_count['count'],
            'studentCount': student_count['count'],
            'subjectCount': subject_count['count'],
            'avgAttendance': attendance_avg.get('avg', 0) or 0
        }), 200

    except Exception as e:
        print("Dashboard Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching dashboard'}), 500


# ============================================================================
# TEACHERS
# ============================================================================

@hod_bp.route('/teachers', methods=['GET'])
@jwt_required()
def get_department_teachers():
    try:
        hod, error_response, status = get_current_hod()
        if error_response:
            return error_response, status

        teachers = db.execute_query("""
            SELECT id, first_name, last_name, email, phone,
                   employee_id, qualification, experience, status
            FROM teachers
            WHERE department = %s
        """, (hod['department'],)) or []

        return jsonify({'success': True, 'teachers': teachers}), 200

    except Exception as e:
        print("Teachers Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching teachers'}), 500


# ============================================================================
# STUDENTS
# ============================================================================

@hod_bp.route('/students', methods=['GET'])
@jwt_required()
def get_department_students():
    try:
        hod, error_response, status = get_current_hod()
        if error_response:
            return error_response, status

        students = db.execute_query("""
            SELECT id, first_name, last_name, email,
                   enrollment_number, program, semester, status
            FROM students
            WHERE department = %s
            ORDER BY semester
        """, (hod['department'],)) or []

        return jsonify({'success': True, 'students': students}), 200

    except Exception as e:
        print("Students Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching students'}), 500


# ============================================================================
# ATTENDANCE STATS
# ============================================================================

@hod_bp.route('/attendance-stats', methods=['GET'])
@jwt_required()
def get_attendance_stats():
    try:
        hod, error_response, status = get_current_hod()
        if error_response:
            return error_response, status

        stats = db.execute_query("""
            SELECT s.id,
                   CONCAT(s.first_name, ' ', s.last_name) as name,
                   COALESCE(
                       AVG(
                           CASE
                               WHEN a.status = 'present' THEN 100
                               WHEN a.status = 'absent' THEN 0
                               ELSE 50
                           END
                       ), 0
                   ) as attendance_percent
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            WHERE s.department = %s
            GROUP BY s.id, s.first_name, s.last_name
            ORDER BY attendance_percent DESC
        """, (hod['department'],)) or []

        return jsonify({'success': True, 'statistics': stats}), 200

    except Exception as e:
        print("Attendance Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching attendance stats'}), 500


# ============================================================================
# PERFORMANCE STATS
# ============================================================================

@hod_bp.route('/performance-stats', methods=['GET'])
@jwt_required()
def get_performance_stats():
    try:
        hod, error_response, status = get_current_hod()
        if error_response:
            return error_response, status

        # If schema isn't fully initialized (marks table missing), return an empty result
        if not db.fetch_one("SHOW TABLES LIKE %s", ('marks',)):
            print("Performance Warning: 'marks' table not found; returning empty stats")
            return jsonify({'success': True, 'statistics': []}), 200

        stats = db.execute_query("""
            SELECT s.id,
                   CONCAT(s.first_name, ' ', s.last_name) as name,
                   COALESCE(AVG(m.total), 0) as avg_marks
            FROM students s
            LEFT JOIN marks m ON s.id = m.student_id
            WHERE s.department = %s
            GROUP BY s.id, s.first_name, s.last_name
            ORDER BY avg_marks DESC
        """, (hod['department'],)) or []

        return jsonify({'success': True, 'statistics': stats}), 200

    except Exception as e:
        print("Performance Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching performance stats'}), 500