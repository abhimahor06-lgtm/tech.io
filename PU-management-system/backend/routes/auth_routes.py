import os

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from db_connect import db
from datetime import datetime

auth_bp = Blueprint('auth_bp', __name__)


# ================= REGISTER =================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        username = data.get('username')
        # Handle both 'email' and 'officialEmail' (for admins)
        email = data.get('email') or data.get('officialEmail')
        password = data.get('password')
        role = data.get('role')

        if not username or not email or not password or not role:
            return jsonify({"success": False, "message": "All fields are required"}), 400

        if role not in ['student', 'teacher', 'hod', 'admin']:
            return jsonify({"success": False, "message": "Invalid role"}), 400

        # Check duplicate username
        existing_user = db.fetch_one("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if existing_user:
            return jsonify({"success": False, "message": "Username or email already exists"}), 400

        hashed_password = generate_password_hash(password)

        # Determine status
        status = 'approved' if role == 'admin' else 'pending'

        # Insert into users table
        user_id = db.execute_insert(
            "INSERT INTO users (username, email, password, role, status, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
            (username, email, hashed_password, role, status, datetime.now())
        )

        # Insert role-specific data
        if role == 'student':
            # Check duplicate enrollment number
            existing_enrollment = db.fetch_one("SELECT id FROM students WHERE enrollment_number = %s", (data.get('enrollmentNumber'),))
            if existing_enrollment:
                return jsonify({"success": False, "message": "Enrollment number already exists"}), 400
            
            db.execute_insert(
                """INSERT INTO students 
                   (user_id, first_name, last_name, email, phone, dob, gender, 
                    enrollment_number, program, department, semester, status) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (user_id, data.get('firstName'), data.get('lastName'), email,
                 data.get('phone'), data.get('dob'), data.get('gender'),
                 data.get('enrollmentNumber'), data.get('program'),
                 data.get('department'), data.get('semester'), status)
            )
        elif role == 'teacher':
            department = data.get('department')
            # Validate department exists
            dept_exists = db.fetch_one("SELECT id FROM departments WHERE name = %s", (department,))
            if not dept_exists:
                return jsonify({"success": False, "message": f"Department '{department}' does not exist"}), 400
            
            # Check duplicate employee ID
            existing_employee = db.fetch_one("SELECT id FROM teachers WHERE employee_id = %s", (data.get('employeeId'),))
            if existing_employee:
                return jsonify({"success": False, "message": "Employee ID already exists"}), 400
            
            db.execute_insert(
                """INSERT INTO teachers 
                   (user_id, first_name, last_name, email, phone, employee_id,
                    department, qualification, specialization, status) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (user_id, data.get('firstName'), data.get('lastName'), email,
                 data.get('phone'), data.get('employeeId'), department,
                 data.get('qualification'), data.get('specialization'), status)
            )
        elif role == 'hod':
            department = data.get('department')
            # Validate department exists
            dept_exists = db.fetch_one("SELECT id FROM departments WHERE name = %s", (department,))
            if not dept_exists:
                return jsonify({"success": False, "message": f"Department '{department}' does not exist"}), 400
            
            # Check duplicate employee ID
            existing_employee = db.fetch_one("SELECT id FROM hods WHERE employee_id = %s", (data.get('employeeId'),))
            if existing_employee:
                return jsonify({"success": False, "message": "Employee ID already exists"}), 400
            
            db.execute_insert(
                """INSERT INTO hods 
                   (user_id, first_name, last_name, email, phone, employee_id,
                    department, qualification, status) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (user_id, data.get('firstName'), data.get('lastName'), email,
                 data.get('phone'), data.get('employeeId'), department,
                 data.get('qualification'), status)
            )
        elif role == 'admin':
            # Check duplicate admin ID
            existing_admin = db.fetch_one("SELECT id FROM admins WHERE admin_id = %s", (data.get('adminId'),))
            if existing_admin:
                return jsonify({"success": False, "message": "Admin ID already exists"}), 400
            
            db.execute_insert(
                """INSERT INTO admins 
                   (user_id, admin_id, first_name, last_name, email, phone,
                    access_level, security_pin, status) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (user_id, data.get('adminId'), data.get('firstName'), data.get('lastName'),
                 email, data.get('phone'), data.get('accessLevel'), 
                 data.get('securityPin'), status)
            )

        db.commit()
        # notify admins of a new pending registration via socketio if available
        try:
            sio = current_app.extensions.get('socketio')
            if sio and status == 'pending':
                sio.emit('notification', { 'type': 'new_user', 'userId': user_id, 'role': role }, namespace='/')
        except Exception:
            pass

        return jsonify({
            "success": True,
            "message": f"{role.capitalize()} registered successfully",
            "status": status,
            "userId": user_id
        })

    except Exception as e:
        db.rollback()
        print("Registration Error:", e)
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500


# ================= LOGIN =================
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        from flask_jwt_extended import create_access_token
        
        data = request.get_json()

        email = data.get('email')
        password = data.get('password')

        # Debugging: print the incoming login identifier so we can trace why users are not found.
        print(f"[LOGIN] identifier={email}")

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400

        # allow login by email OR username
        user = db.fetch_one(
            "SELECT * FROM users WHERE email = %s OR username = %s",
            (email, email)
        )
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        if not check_password_hash(user['password'], password):
            return jsonify({"success": False, "message": "Invalid password"}), 401

        # in dev/demo mode, allow pending accounts to login (but still flag status)
        allow_pending = os.getenv('ALLOW_PENDING_LOGIN', 'true').lower() in ('1','true','yes')
        if user['status'] != 'approved' and not allow_pending:
            return jsonify({
                "success": False, 
                "message": f"Account is {user['status']}. Please wait for admin approval."
            }), 403

        # Create JWT token
        # always cast identity to string; PyJWT enforces sub to be a string
        access_token = create_access_token(
            identity=str(user['id']),
            additional_claims={
                'role': user['role'],
                'email': user['email'],
                'username': user['username']
            }
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": access_token,
            "status": user['status'],
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "role": user['role']
            }
        })

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"success": False, "message": f"Login failed: {str(e)}"}), 500
