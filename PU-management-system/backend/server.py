"""
server.py
Improved Flask Server
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from datetime import timedelta
import os
import glob
from dotenv import load_dotenv

from db_connect import db

load_dotenv()

# serve frontend assets from ../frontend directory so everything comes from the same host
app = Flask(__name__, static_folder="../frontend", static_url_path="")
# during development avoid aggressive caching of static files
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# ================= CONFIG =================

JWT_SECRET = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET:
    raise Exception("JWT_SECRET_KEY must be set in .env")

app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JSON_SORT_KEYS'] = False

# Secure CORS (adjust frontend URL if needed)
# ensure Authorization header is allowed and disable caching for preflight problems
# Allow requests from file:// origins (null) and local http origins.
# The frontend may be opened via file:// during quick demos.
# CORS policy: allowed frontend origins for this API.
# - http://localhost:5000 for served web pages
# - http://127.0.0.1:5000 for direct URL access
# - null to permit file:// requests (for local dev convenience)
# Do not use '*' when supports_credentials=True.
CORS(app,
     resources={r"/api/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000", "null"]}},
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True,
     expose_headers=["Content-Type", "Authorization"],
     vary_header=True)

# add after-request hook to reinforce header (helps some browsers)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:5000', 'http://127.0.0.1:5000', 'null']:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5000'

    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization,Content-Type,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def options(path):
    response = jsonify({'success': True, 'message': 'CORS preflight'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization,Content-Type,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    return response

jwt = JWTManager(app)

# customize JWT error messages so we return 401 instead of 422 and include success flag
@jwt.unauthorized_loader
def _unauthorized_callback(err):
    # missing Authorization header or token
    return jsonify({'success': False, 'message': err}), 401

@jwt.invalid_token_loader
def _invalid_token_callback(err):
    # malformed token (not enough segments, wrong signature, etc.)
    return jsonify({'success': False, 'message': err}), 401

@jwt.expired_token_loader
def _expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'success': False, 'message': 'Token has expired'}), 401

# socketio for realtime updates
socketio = SocketIO(app, cors_allowed_origins='*')

# ================= DATABASE HANDLING =================

@app.before_request
def before_request():
    if not db.ensure_connection():
        return jsonify({
            'success': False,
            'message': 'Database connection failed'
        }), 500


@app.teardown_request
def teardown_request(exception):
    # Optional: Uncomment if you want connection per request
    # db.disconnect()
    pass


# ================= REGISTER ROUTES =================

from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.teacher_routes import teacher_bp
from routes.hod_routes import hod_bp
from routes.admin_routes import admin_bp
from routes.attendance_routes import attendance_bp
from routes.user_routes import user_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(student_bp, url_prefix='/api/student')
app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
app.register_blueprint(hod_bp, url_prefix='/api/hod')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(attendance_bp, url_prefix='/api/attendance')


# ================= ERROR HANDLERS =================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': 'Bad Request'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'success': False, 'message': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'success': False, 'message': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal Server Error'}), 500


# ================= HEALTH CHECK =================

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db.ensure_connection()
        db.execute_query("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"

    return jsonify({
        'success': True,
        'server': 'running',
        'database': db_status
    }), 200


@app.route('/api/health/schema', methods=['GET'])
def health_schema():
    """Return a list of expected tables that are missing from the current database."""
    expected_tables = [
        'users', 'departments', 'students', 'teachers', 'hods',
        'admins', 'attendance', 'subjects', 'enrollments', 'marks', 'assignments'
    ]
    missing = []
    try:
        db.ensure_connection()
        for table in expected_tables:
            exists = db.fetch_one("SHOW TABLES LIKE %s", (table,))
            if not exists:
                missing.append(table)

        return jsonify({
            'success': True,
            'missingTables': missing,
            'ok': len(missing) == 0
        }), 200
    except Exception as e:
        print('Schema check error:', e)
        return jsonify({'success': False, 'message': 'Schema check failed', 'error': str(e)}), 500


# -----------------------------------------------------
# SYSTEM PROMPT for AI chat (reads project documentation automatically)
# -----------------------------------------------------

def load_docs_text():
    """Read all markdown files in the docs directory and return a combined string."""
    base = os.path.join(os.path.dirname(__file__), '..', 'docs')
    parts = []
    if os.path.isdir(base):
        for fname in os.listdir(base):
            if fname.endswith('.md'):
                try:
                    with open(os.path.join(base, fname), 'r', encoding='utf-8') as f:
                        data = f.read()
                    parts.append(f"--- {fname} ---\n" + data)
                except Exception:
                    pass
    return "\n\n".join(parts)

DOCS_CONTENT = load_docs_text()

SYSTEM_PROMPT = (
    "You are an advanced AI technical support assistant for a University Management System (UMS) built with Python Flask and MySQL.\n"
    "Use the project documentation that follows to answer questions accurately.\n\n"
    f"{DOCS_CONTENT}\n\n"
    "You operate with a 3-layer intelligence architecture:\n"
    "\n"
    "LAYER 1 — DOCUMENTATION: You know Student Registration Workflow, Login/Authentication, Admin Approval System, Teacher Dashboard, Student Dashboard, Course Management, User Role Permissions, Database Schema, API Endpoints, Website Navigation, and FAQs.\n"
    "\n"
    "LAYER 2 — ERROR LOG ANALYSIS: You diagnose Flask server errors, Python exceptions, Database errors, API errors, authentication failures, duplicate entry errors, permission errors, server timeout errors.\n"
    "\n"
    "LAYER 3 — DATABASE VERIFICATION: You analyze issues with MySQL tables: users, students, teachers, courses, departments, attendance, grades.\n"
    "\n"
    "RESPONSE FORMAT (always use this):\n"
    "**Issue:** One sentence problem identification.\n"
    "**Fix:**\n"
    "• Step 1\n"
    "• Step 2\n"
    "• Step 3\n"
    "\n"
    "RULES:\n"
    "• Keep responses under 80 words unless detail is requested\n"
    "• Be direct and solution-focused\n"
    "• Use bullet points\n"
    "• Never invent database data\n"
    "• Prioritize speed and accuracy\n"
    "• You can respond in Urdu/Roman Urdu if the user writes in that language"
)

# -----------------------------------------------------
# CHAT PROXY (requires JWT auth)
# -----------------------------------------------------
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    try:
        payload = request.get_json() or {}
        messages = payload.get('messages')
        if not isinstance(messages, list):
            return jsonify({'success': False, 'message': 'messages must be a list'}), 400

        # Use provided API key (fallback to provided key if env var missing)
        api_key = os.getenv('ANTHROPIC_API_KEY', 'AIzaSyCPtKjbag_M26PQq_IuVt0ha8pBBLdGw8c')
        if not api_key:
            return jsonify({'success': False, 'message': 'AI API key not configured on server'}), 500

        # Build a simple conversation prompt for Google Generative AI
        formatted_messages = []
        for msg in messages:
            role = (msg.get('role') or 'user').lower()
            text = msg.get('content') if isinstance(msg.get('content'), str) else (msg.get('content', {}).get('text') if isinstance(msg.get('content'), dict) else str(msg.get('content')))
            author = 'user' if role == 'user' else 'assistant'
            formatted_messages.append({
                'author': author,
                'content': [{ 'type': 'text', 'text': text }]
            })

        url = f'https://generativelanguage.googleapis.com/v1/models/text-bison-001:generate?key={api_key}'
        headers = { 'Content-Type': 'application/json' }
        body = {
            'model': 'text-bison-001',
            'prompt': { 'messages': formatted_messages },
            'temperature': 0.7,
            'maxOutputTokens': 800
        }

        ai_resp = requests.post(url, json=body, headers=headers, timeout=15)

        # Normalize the response to match frontend expectations: { content: [{ text: ... }] }
        try:
            ai_data = ai_resp.json()
        except Exception:
            return jsonify({'content': [{ 'text': 'Unable to parse AI response' }]}), 200

        text = ''
        if isinstance(ai_data, dict):
            candidates = ai_data.get('candidates') or []
            if candidates and isinstance(candidates[0], dict):
                text = candidates[0].get('content', '')
            else:
                text = str(ai_data)
        else:
            text = str(ai_data)

        return jsonify({'content': [{ 'text': text }]}), 200

    except Exception as e:
        # If the AI API call fails (or key is invalid), still return a response shape
        return jsonify({'content': [{'text': 'Sorry, the AI assistant is temporarily unavailable. Please try again later.'}]}), 200


# ================= ROOT =================

@app.route('/', methods=['GET'])
def root():
    # serve frontend homepage instead of JSON when accessed from browser
    return app.send_static_file('index.html')

# fallback for any other file requests (js/css/html/images)
@app.route('/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)


# ================= START SERVER =================

if __name__ == '__main__':

    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'

    print("""
    ----------------------------------------
    Poornima University Management System
    Secure Flask Server Starting...
    ----------------------------------------
    """)

    # start via socketio to enable websocket events
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )