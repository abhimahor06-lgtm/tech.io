"""
student_routes.py
Secure Student Routes
Poornima University Management System
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from db_connect import db

student_bp = Blueprint('student', __name__)


def _table_exists(table_name):
    return bool(db.fetch_one("SHOW TABLES LIKE %s", (table_name,)))


def _table_has_column(table_name, column_name):
    return bool(
        db.fetch_one(
            f"SHOW COLUMNS FROM {table_name} LIKE %s",
            (column_name,),
        )
    )


def _student_profile_by_user_id(user_id):
    return db.fetch_one(
        """
        SELECT id, user_id, first_name, last_name, email,
               enrollment_number, program, department,
               semester, status, current_cgpa
        FROM students
        WHERE user_id = %s
        """,
        (user_id,),
    )


def _student_profile_by_student_id(student_id):
    return db.fetch_one(
        """
        SELECT id, user_id, first_name, last_name, email,
               enrollment_number, program, department,
               semester, status, current_cgpa
        FROM students
        WHERE id = %s
        """,
        (student_id,),
    )


def resolve_student_access(requested_student_id):
    claims = get_jwt()
    role = claims.get('role')

    try:
        auth_user_id = int(get_jwt_identity())
    except Exception:
        return None, jsonify({'success': False, 'message': 'Unauthorized'}), 403

    if role == 'admin':
        student = _student_profile_by_student_id(requested_student_id)
        if not student:
            student = _student_profile_by_user_id(requested_student_id)
        if not student:
            return None, jsonify({'success': False, 'message': 'Student not found'}), 404
        return student, None, None

    if role != 'student':
        return None, jsonify({'success': False, 'message': 'Unauthorized'}), 403

    student = _student_profile_by_user_id(auth_user_id)
    if not student:
        return None, jsonify({'success': False, 'message': 'Student profile not found'}), 404

    allowed_ids = {student['id'], student['user_id']}
    if requested_student_id not in allowed_ids:
        return None, jsonify({'success': False, 'message': 'Unauthorized'}), 403

    return student, None, None


def _format_date(value):
    return value.isoformat() if value is not None else None


def _format_datetime(value):
    return value.isoformat() if value is not None else None


def _load_marks(student_pk):
    if not _table_exists('marks'):
        return []

    if all(_table_has_column('marks', column) for column in ('internal', 'midterm', 'final', 'total')):
        return db.execute_query(
            """
            SELECT m.subject_id, s.subject_code, s.subject_name,
                   m.internal, m.midterm, m.final, m.total, m.grade,
                   m.mark_type, m.uploaded_date
            FROM marks m
            LEFT JOIN subjects s ON s.id = m.subject_id
            WHERE m.student_id = %s
            ORDER BY s.subject_name, m.uploaded_date DESC
            """,
            (student_pk,),
        ) or []

    if not _table_has_column('marks', 'marks'):
        return []

    legacy_rows = db.execute_query(
        """
        SELECT m.subject_id, s.subject_code, s.subject_name,
               m.mark_type, m.marks, m.uploaded_date
        FROM marks m
        LEFT JOIN subjects s ON s.id = m.subject_id
        WHERE m.student_id = %s
        ORDER BY s.subject_name, m.uploaded_date DESC
        """,
        (student_pk,),
    ) or []

    grouped = {}
    for row in legacy_rows:
        subject_id = row.get('subject_id')
        existing = grouped.setdefault(
            subject_id,
            {
                'subject_id': subject_id,
                'subject_code': row.get('subject_code'),
                'subject_name': row.get('subject_name'),
                'internal': None,
                'midterm': None,
                'final': None,
                'total': 0,
                'grade': None,
                'uploaded_date': row.get('uploaded_date'),
            },
        )

        mark_type = (row.get('mark_type') or '').lower()
        mark_value = row.get('marks')
        if mark_type in ('internal', 'midterm', 'final'):
            existing[mark_type] = mark_value

        numeric_value = float(mark_value or 0)
        existing['total'] = round(float(existing.get('total') or 0) + numeric_value, 2)

        if existing.get('uploaded_date') is None or (
            row.get('uploaded_date') and row.get('uploaded_date') > existing.get('uploaded_date')
        ):
            existing['uploaded_date'] = row.get('uploaded_date')

    return list(grouped.values())


def _load_attendance(student_pk):
    if not _table_exists('attendance'):
        return []

    if _table_has_column('attendance', 'subject_id'):
        return db.execute_query(
            """
            SELECT s.id as subject_id,
                   s.subject_code,
                   s.subject_name,
                   COUNT(a.id) as total_classes,
                   SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as attended_classes,
                   ROUND(
                       COALESCE(AVG(
                           CASE
                               WHEN a.status = 'present' THEN 100
                               WHEN a.status = 'absent' THEN 0
                               ELSE 50
                           END
                       ), 0),
                       2
                   ) as percentage
            FROM enrollments e
            JOIN subjects s ON s.id = e.subject_id
            LEFT JOIN attendance a
                ON a.student_id = e.student_id
               AND a.subject_id = e.subject_id
            WHERE e.student_id = %s
            GROUP BY s.id, s.subject_code, s.subject_name
            ORDER BY s.subject_name
            """,
            (student_pk,),
        ) or []

    if not _table_has_column('attendance', 'subject'):
        return []

    return db.execute_query(
        """
        SELECT subject as subject_name,
               subject as subject_code,
               COUNT(*) as total_classes,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as attended_classes,
               ROUND(AVG(
                   CASE
                       WHEN status = 'present' THEN 100
                       WHEN status = 'absent' THEN 0
                       ELSE 50
                   END
               ), 2) as percentage
        FROM attendance
        WHERE student_id = %s
        GROUP BY subject
        ORDER BY subject
        """,
        (student_pk,),
    ) or []


def _load_assignments(student_pk):
    if not _table_exists('assignments'):
        return []

    try:
        return db.execute_query(
            """
            SELECT a.id, a.title, a.description, a.due_date,
                   a.created_date, s.subject_name
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            JOIN enrollments e ON e.subject_id = a.subject_id
            WHERE e.student_id = %s
            ORDER BY a.due_date ASC, a.created_date DESC
            """,
            (student_pk,),
        ) or []
    except Exception as err:
        print("Assignments query failed:", err)
        return []


def _load_exam_schedule(student_pk):
    if not _table_exists('exam_schedule'):
        return []

    if all(_table_has_column('exam_schedule', column) for column in ('duration_minutes', 'room_no')):
        return db.execute_query(
            """
            SELECT es.id, es.exam_type, es.exam_date, es.exam_time,
                   es.duration_minutes, es.room_no, s.subject_name, s.subject_code
            FROM exam_schedule es
            JOIN subjects s ON es.subject_id = s.id
            JOIN enrollments e ON e.subject_id = s.id
            WHERE e.student_id = %s
              AND (es.student_id IS NULL OR es.student_id = %s)
            ORDER BY es.exam_date ASC, es.exam_time ASC
            """,
            (student_pk, student_pk),
        ) or []

    if not all(_table_has_column('exam_schedule', column) for column in ('duration', 'location')):
        return []

    return db.execute_query(
        """
        SELECT es.id, es.exam_type, es.exam_date, es.exam_time,
               es.duration, es.location, s.subject_name, s.subject_code
        FROM exam_schedule es
        JOIN subjects s ON es.subject_id = s.id
        JOIN enrollments e ON e.subject_id = s.id
        WHERE e.student_id = %s
        ORDER BY es.exam_date ASC, es.exam_time ASC
        """,
        (student_pk,),
    ) or []


def _load_notices():
    if not _table_exists('notices'):
        return []

    if _table_has_column('notices', 'visibility'):
        return db.execute_query(
            """
            SELECT n.id, n.title, n.content, n.posted_date, n.posted_by,
                   u.role as posted_by_role, u.username as posted_by_name
            FROM notices n
            LEFT JOIN users u ON u.id = n.posted_by
            WHERE n.visibility IN ('all', 'students')
            ORDER BY n.posted_date DESC
            LIMIT 20
            """
        ) or []

    return db.execute_query(
        """
        SELECT id, title, content, posted_date, posted_by
        FROM notices
        ORDER BY posted_date DESC
        LIMIT 20
        """
    ) or []


# ============================================================================
# ACADEMIC DATA
# ============================================================================

@student_bp.route('/<int:student_id>/academic', methods=['GET'])
@jwt_required()
def get_academic_data(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        student_pk = student['id']

        att = {'percentage': 0}
        if _table_exists('attendance'):
            att = db.fetch_one(
                """
                SELECT ROUND(AVG(
                    CASE
                        WHEN status = 'present' THEN 100
                        WHEN status = 'absent' THEN 0
                        ELSE 50
                    END
                ), 2) as percentage
                FROM attendance
                WHERE student_id = %s
                """,
                (student_pk,),
            ) or {'percentage': 0}

        subj_count = {'count': 0}
        if _table_exists('enrollments'):
            subj_count = db.fetch_one(
                "SELECT COUNT(*) as count FROM enrollments WHERE student_id = %s",
                (student_pk,),
            ) or {'count': 0}

        total_assignments = {'count': 0}
        if _table_exists('assignments'):
            total_assignments = db.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM assignments a
                JOIN enrollments e ON e.subject_id = a.subject_id
                WHERE e.student_id = %s
                """,
                (student_pk,),
            ) or {'count': 0}

        submitted = {'count': 0}
        if _table_exists('submissions'):
            submitted = db.fetch_one(
                "SELECT COUNT(*) as count FROM submissions WHERE student_id = %s",
                (student_pk,),
            ) or {'count': 0}

        progress = 0
        if total_assignments['count'] > 0:
            progress = round((submitted['count'] / total_assignments['count']) * 100, 2)

        return jsonify({
            'success': True,
            'student': student,
            'cgpa': float(student.get('current_cgpa', 0) or 0),
            'attendance': float(att.get('percentage', 0) or 0),
            'subjectCount': subj_count['count'],
            'assignmentProgress': progress,
        }), 200

    except Exception as e:
        print("Academic Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching academic data'}), 500


# ============================================================================
# ATTENDANCE
# ============================================================================

@student_bp.route('/<int:student_id>/attendance', methods=['GET'])
@jwt_required()
def get_attendance(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        attendance = _load_attendance(student['id'])
        return jsonify({'success': True, 'attendance': attendance}), 200

    except Exception as e:
        print("Attendance Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching attendance'}), 500


# ============================================================================
# MARKS
# ============================================================================

@student_bp.route('/<int:student_id>/marks', methods=['GET'])
@jwt_required()
def get_marks(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        marks = _load_marks(student['id'])
        return jsonify({'success': True, 'marks': marks}), 200

    except Exception as e:
        print("Marks Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching marks'}), 500


# ============================================================================
# SUBJECTS
# ============================================================================

@student_bp.route('/<int:student_id>/subjects', methods=['GET'])
@jwt_required()
def get_subjects(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        if not (_table_exists('subjects') and _table_exists('enrollments')):
            return jsonify({'success': True, 'subjects': []}), 200

        subjects = db.execute_query(
            """
            SELECT s.id, s.subject_code, s.subject_name, s.credits,
                   t.first_name, t.last_name
            FROM subjects s
            JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN teachers t ON s.teacher_id = t.id
            WHERE e.student_id = %s
            ORDER BY s.subject_name
            """,
            (student['id'],),
        ) or []

        return jsonify({'success': True, 'subjects': subjects}), 200

    except Exception as e:
        print("Subjects Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching subjects'}), 500


# ============================================================================
# ASSIGNMENT SUBMISSION
# ============================================================================

@student_bp.route('/<int:student_id>/assignments/<int:assignment_id>/submit', methods=['POST'])
@jwt_required()
def submit_assignment(student_id, assignment_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        if not _table_exists('submissions'):
            return jsonify({'success': False, 'message': 'Assignment submissions are not configured'}), 503

        data = request.get_json() or {}
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'message': 'Submission content required'}), 400

        existing = db.fetch_one(
            """
            SELECT id FROM submissions
            WHERE assignment_id = %s AND student_id = %s
            """,
            (assignment_id, student['id']),
        )

        if existing:
            return jsonify({'success': False, 'message': 'Assignment already submitted'}), 409

        submission_id = db.execute_insert(
            """
            INSERT INTO submissions
            (assignment_id, student_id, submission_text, submitted_date, assignment_status)
            VALUES (%s, %s, %s, NOW(), 'submitted')
            """,
            (assignment_id, student['id'], content),
        )

        return jsonify({
            'success': True,
            'message': 'Assignment submitted successfully',
            'submissionId': submission_id,
        }), 201

    except Exception as e:
        print("Submission Error:", e)
        return jsonify({'success': False, 'message': 'Error submitting assignment'}), 500


# ============================================================================
# ASSIGNMENTS (LIST)
# ============================================================================

@student_bp.route('/<int:student_id>/assignments', methods=['GET'])
@jwt_required()
def get_assignments(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        assignments = _load_assignments(student['id'])
        return jsonify({
            'success': True,
            'assignments': [
                {
                    'id': assignment['id'],
                    'title': assignment['title'],
                    'description': assignment['description'],
                    'due_date': _format_date(assignment.get('due_date')),
                    'created_date': _format_datetime(assignment.get('created_date')),
                    'subject_name': assignment.get('subject_name'),
                }
                for assignment in assignments
            ],
        }), 200

    except Exception as e:
        print("Get Assignments Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching assignments'}), 500


# ============================================================================
# EXAM SCHEDULE
# ============================================================================

@student_bp.route('/<int:student_id>/exam-schedule', methods=['GET'])
@jwt_required()
def get_exam_schedule(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        exams = _load_exam_schedule(student['id'])
        return jsonify({
            'success': True,
            'exams': [
                {
                    'id': exam['id'],
                    'exam_type': exam.get('exam_type'),
                    'exam_date': _format_date(exam.get('exam_date')),
                    'exam_time': str(exam.get('exam_time')) if exam.get('exam_time') is not None else None,
                    'duration': exam.get('duration_minutes', exam.get('duration')),
                    'location': exam.get('room_no', exam.get('location')),
                    'subject_name': exam.get('subject_name'),
                    'subject_code': exam.get('subject_code'),
                }
                for exam in exams
            ],
        }), 200

    except Exception as e:
        print("Get Exam Schedule Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching exam schedule'}), 500


# ============================================================================
# NOTICES
# ============================================================================

@student_bp.route('/<int:student_id>/notices', methods=['GET'])
@jwt_required()
def get_notices(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        notices = _load_notices()
        return jsonify({
            'success': True,
            'notices': [
                {
                    'id': notice['id'],
                    'title': notice.get('title'),
                    'content': notice.get('content'),
                    'posted_date': _format_datetime(notice.get('posted_date')),
                    'posted_by': notice.get('posted_by_name') or notice.get('posted_by'),
                    'posted_by_role': notice.get('posted_by_role'),
                }
                for notice in notices
            ],
        }), 200

    except Exception as e:
        print("Get Notices Error:", e)
        return jsonify({'success': False, 'message': 'Error fetching notices'}), 500


# ============================================================================
# AI PREDICTION
# ============================================================================

@student_bp.route('/<int:student_id>/ai-prediction', methods=['GET'])
@jwt_required()
def get_ai_prediction(student_id):
    try:
        student, error_response, status = resolve_student_access(student_id)
        if error_response:
            return error_response, status

        student_pk = student['id']
        cgpa = float(student.get('current_cgpa', 0) or 0)

        cached_prediction = None
        if _table_exists('ai_predictions'):
            cached_prediction = db.fetch_one(
                """
                SELECT prediction_score, prediction_label, confidence, generated_date
                FROM ai_predictions
                WHERE student_id = %s AND prediction_type = 'dropout'
                ORDER BY generated_date DESC
                LIMIT 1
                """,
                (student_pk,),
            )

        if cached_prediction:
            dropout_risk = cached_prediction.get('prediction_label') or 'Unknown'
            recommendation = 'Keep following your study plan.'
            if dropout_risk.lower() == 'high':
                recommendation = 'Seek academic advising immediately'
            elif dropout_risk.lower() == 'medium':
                recommendation = 'Consider tutoring for struggling subjects'

            return jsonify({
                'success': True,
                'dropout_risk': dropout_risk,
                'cgpa': cgpa,
                'recommendation': recommendation,
                'confidence': float(cached_prediction.get('confidence') or 0),
                'prediction_score': float(cached_prediction.get('prediction_score') or 0),
                'generated_date': _format_datetime(cached_prediction.get('generated_date')),
            }), 200

        dropout_risk = 'Low'
        recommendation = 'Keep up your excellent work!'

        if cgpa < 2.0:
            dropout_risk = 'High'
            recommendation = 'Seek academic advising immediately'
        elif cgpa < 3.0:
            dropout_risk = 'Medium'
            recommendation = 'Consider tutoring for struggling subjects'

        return jsonify({
            'success': True,
            'dropout_risk': dropout_risk,
            'cgpa': cgpa,
            'recommendation': recommendation,
        }), 200

    except Exception as e:
        print("AI Prediction Error:", e)
        return jsonify({'success': False, 'message': 'Error getting prediction'}), 500
