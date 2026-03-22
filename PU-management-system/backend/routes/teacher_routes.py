"""
teacher_routes.py
Teacher Routes - Fixed Version
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from db_connect import db

teacher_bp = Blueprint('teacher', __name__)


# ------------------ Helper Function ------------------

def verify_teacher_subject(subject_id, teacher_id):
    query = "SELECT id FROM subjects WHERE id = %s AND teacher_id = %s"
    result = db.execute_query(query, (subject_id, teacher_id))
    return True if result else False


def get_current_teacher_record():
    """Return teacher record for current authenticated user."""
    user_id = int(get_jwt_identity())
    return db.fetch_one("SELECT id, user_id FROM teachers WHERE user_id = %s", (user_id,))


# ------------------ Dashboard Summary ------------------

@teacher_bp.route('/<int:teacher_id>/dashboard', methods=['GET'])
@jwt_required()
def get_teacher_dashboard(teacher_id):
    """Return high-level statistics for the logged-in teacher."""
    claims = get_jwt()
    user_id = int(get_jwt_identity())

    if claims.get('role') != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    if user_id != teacher_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_record = get_current_teacher_record()
    if not teacher_record:
        return jsonify({'success': False, 'message': 'Teacher profile not found'}), 404

    teacher_pk = teacher_record['id']

    try:
        # subject count
        subj = db.fetch_one(
            "SELECT COUNT(*) as count FROM subjects WHERE teacher_id = %s",
            (teacher_pk,)
        ) or {'count': 0}

        # total distinct students across those subjects
        students = db.fetch_one(
            """
            SELECT COUNT(DISTINCT e.student_id) as count
            FROM enrollments e
            JOIN subjects s ON e.subject_id = s.id
            WHERE s.teacher_id = %s
            """,
            (teacher_pk,)
        ) or {'count': 0}

        # average attendance percentage for this teacher's classes
        try:
            avg_att = db.fetch_one(
                """
                SELECT ROUND(AVG(
                    CASE
                        WHEN a.status = 'present' THEN 100
                        WHEN a.status = 'absent' THEN 0
                        ELSE 50
                    END
                ), 2) as avg
                FROM attendance a
                JOIN subjects s ON (a.subject = s.subject_name OR a.subject = s.subject_code)
                WHERE s.teacher_id = %s
                """,
                (teacher_pk,)
            ) or {'avg': 0}
        except Exception:
            # fallback to older attendance schema with subject_id column (if it exists)
            avg_att = db.fetch_one(
                """
                SELECT ROUND(AVG(
                    CASE
                        WHEN a.status = 'present' THEN 100
                        WHEN a.status = 'absent' THEN 0
                        ELSE 50
                    END
                ), 2) as avg
                FROM attendance a
                JOIN subjects s ON a.subject_id = s.id
                WHERE s.teacher_id = %s
                """,
                (teacher_pk,)
            ) or {'avg': 0}

        # pending submissions needing grading (submitted but not graded)
        try:
            pending = db.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM submissions sub
                JOIN assignments a ON sub.assignment_id = a.id
                JOIN subjects s ON a.subject_id = s.id
                WHERE s.teacher_id = %s AND sub.assignment_status = 'submitted'
                """,
                (teacher_pk,)
            ) or {'count': 0}
        except Exception as exc:
            print('Teacher dashboard pending query error:', exc)
            pending = {'count': 0}

        return jsonify({
            'success': True,
            'subjectCount': subj['count'],
            'totalStudents': students['count'],
            'avgAttendance': avg_att.get('avg', 0) or 0,
            'pendingUploads': pending['count']
        }), 200

    except Exception as e:
        print('Teacher dashboard error:', e)
        return jsonify({'success': False, 'message': 'Error fetching teacher dashboard'}), 500


# ------------------ Get Subjects ------------------

@teacher_bp.route('/subjects', methods=['GET'])
@jwt_required()
def get_teaching_subjects():
    try:
        teacher_record = get_current_teacher_record()
        if not teacher_record:
            return jsonify({'success': False, 'message': 'Teacher profile not found'}), 404

        teacher_id = teacher_record['id']

        query = '''
        SELECT id, subject_code, subject_name, credits, department
        FROM subjects WHERE teacher_id = %s
        '''

        subjects = db.execute_query(query, (teacher_id,))

        return jsonify({
            'success': True,
            'subjects': subjects or [],
            'count': len(subjects) if subjects else 0
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ------------------ Get Students ------------------

@teacher_bp.route('/subjects/<int:subject_id>/students', methods=['GET'])
@jwt_required()
def get_subject_students(subject_id):
    try:
        teacher_record = get_current_teacher_record()
        if not teacher_record:
            return jsonify({'success': False, 'message': 'Teacher profile not found'}), 404

        teacher_id = teacher_record['id']

        if not verify_teacher_subject(subject_id, teacher_id):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        query = '''
        SELECT s.id, s.first_name, s.last_name, s.enrollment_number, s.email
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        WHERE e.subject_id = %s
        '''

        students = db.execute_query(query, (subject_id,))

        return jsonify({'success': True, 'students': students or []}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ------------------ Mark Attendance ------------------

@teacher_bp.route('/subjects/<int:subject_id>/attendance', methods=['POST'])
@jwt_required()
def mark_attendance(subject_id):
    try:
        teacher_record = get_current_teacher_record()
        if not teacher_record:
            return jsonify({'success': False, 'message': 'Teacher profile not found'}), 404

        teacher_id = teacher_record['id']

        if not verify_teacher_subject(subject_id, teacher_id):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        attendance_data = data.get('attendanceData', [])

        # Determine subject key used in attendance table (support both subject_id + subject text versions)
        subject_info = db.fetch_one('SELECT subject_name, subject_code FROM subjects WHERE id = %s', (subject_id,))
        if not subject_info:
            return jsonify({'success': False, 'message': 'Subject not found'}), 404

        subject_label = subject_info.get('subject_code') or subject_info.get('subject_name')

        for record in attendance_data:
            student_id = record.get('studentId')
            status = record.get('status')

            # Try legacy schema with subject_id column first
            existing = None
            try:
                check_query = '''
                SELECT id FROM attendance 
                WHERE student_id = %s AND subject_id = %s AND date = CURDATE()
                '''
                existing = db.execute_query(check_query, (student_id, subject_id))

                if existing:
                    update_query = '''
                    UPDATE attendance 
                    SET status = %s 
                    WHERE student_id = %s AND subject_id = %s AND date = CURDATE()
                    '''
                    db.execute_update(update_query, (status, student_id, subject_id))
                else:
                    insert_query = '''
                    INSERT INTO attendance (student_id, subject_id, date, status)
                    VALUES (%s, %s, CURDATE(), %s)
                    '''
                    db.execute_insert(insert_query, (student_id, subject_id, status))

                continue
            except Exception:
                # legacy schema missing subject_id; fallback to subject text id
                pass

            # Fallback for older attendance schema using subject text
            check_query = '''
            SELECT id FROM attendance 
            WHERE student_id = %s AND subject = %s AND date = CURDATE()
            '''
            existing = db.execute_query(check_query, (student_id, subject_label))

            if existing:
                update_query = '''
                UPDATE attendance 
                SET status = %s 
                WHERE student_id = %s AND subject = %s AND date = CURDATE()
                '''
                db.execute_update(update_query, (status, student_id, subject_label))
            else:
                insert_query = '''
                INSERT INTO attendance (student_id, subject, date, status, marked_by, role)
                VALUES (%s, %s, CURDATE(), %s, %s, 'teacher')
                '''
                db.execute_insert(insert_query, (student_id, subject_label, status, teacher_id))

        return jsonify({'success': True, 'message': 'Attendance saved'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ------------------ Upload Marks ------------------

@teacher_bp.route('/subjects/<int:subject_id>/marks', methods=['POST'])
@jwt_required()
def upload_marks(subject_id):
    try:
        teacher_record = get_current_teacher_record()
        if not teacher_record:
            return jsonify({'success': False, 'message': 'Teacher profile not found'}), 404

        teacher_id = teacher_record['id']

        if not verify_teacher_subject(subject_id, teacher_id):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        marks_data = data.get('marksData', [])

        for record in marks_data:
            student_id = record.get('studentId')
            mark_type = record.get('markType')
            marks = record.get('marks')

            check_query = '''
            SELECT id FROM marks 
            WHERE student_id = %s AND subject_id = %s AND mark_type = %s
            '''
            existing = db.execute_query(check_query, (student_id, subject_id, mark_type))

            if existing:
                update_query = '''
                UPDATE marks 
                SET marks = %s, uploaded_date = NOW()
                WHERE student_id = %s AND subject_id = %s AND mark_type = %s
                '''
                db.execute_update(update_query, (marks, student_id, subject_id, mark_type))
            else:
                insert_query = '''
                INSERT INTO marks (student_id, subject_id, mark_type, marks, uploaded_date)
                VALUES (%s, %s, %s, %s, NOW())
                '''
                db.execute_insert(insert_query, (student_id, subject_id, mark_type, marks))

        return jsonify({'success': True, 'message': 'Marks saved'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500