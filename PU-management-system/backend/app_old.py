"""
app.py
Main Flask Application
University Management System API
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import bcrypt
import os
import glob
import requests
from predictor import get_student_prediction
from db_connect import db


# serve frontend assets from ../frontend directory; using same origin simplifies AJAX
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

# disable caching during development
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


# =====================================================
# HEALTH CHECK ROUTE
# =====================================================
# serve API home status under /api for clarity
@app.route("/api/", methods=["GET"])
def home():
    return jsonify({
        "message": "University Management System API Running",
        "status": "success"
    })

# catch-all route to deliver frontend files
@app.route("/<path:filename>")
def static_files(filename):
    return app.send_static_file(filename)

# if user hits root, send index.html (frontend entry)
@app.route("/")
def root_index():
    return app.send_static_file("index.html")


# =====================================================
# DATABASE TEST ROUTE
# =====================================================
@app.route("/test-db", methods=["GET"])
def test_db():
    try:
        result = db.execute_query("SELECT 1 AS test")
        return jsonify({
            "database": "connected",
            "result": result
        })
    except Exception as e:
        return jsonify({
            "database": "error",
            "error": str(e)
        }), 500


# =====================================================
# REGISTER ROUTE
# =====================================================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        # Basic validation
        if not name or not email or not password or not role:
            return jsonify({"error": "All fields are required"}), 400

        if role not in ["admin", "hod", "teacher", "student"]:
            return jsonify({"error": "Invalid role"}), 400

        # Check duplicate email
        existing = db.fetch_one(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        if existing:
            return jsonify({"error": "Email already registered"}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        # Insert user
        db.execute_insert(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )

        db.commit()  # 🔥 VERY IMPORTANT

        return jsonify({
            "status": "success",
            "message": f"{role} registered successfully"
        })

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


# =====================================================
# LOGIN ROUTE
# =====================================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        user = db.fetch_one(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# STUDENT PREDICTION ROUTE
# =====================================================
@app.route("/student/<int:student_id>/prediction", methods=["GET"])
def student_prediction(student_id):
    try:
        result = get_student_prediction(student_id)

        if not result:
            return jsonify({
                "error": "Student not found or insufficient data"
            }), 404

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# -----------------------------------------------------
# AI CHAT PROXY
# -----------------------------------------------------

def load_docs_text():
    base = os.path.join(os.path.dirname(__file__), '..', 'docs')
    parts = []
    if os.path.isdir(base):
        for fname in os.listdir(base):
            if fname.endswith('.md'):
                try:
                    with open(os.path.join(base, fname), 'r', encoding='utf-8') as f:
                        parts.append(f"--- {fname} ---\n" + f.read())
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


@app.route("/chat", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def chat_proxy():
    try:
        payload = request.get_json() or {}
        messages = payload.get("messages")
        if not isinstance(messages, list):
            return jsonify({"error": "messages must be a list"}), 400

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({"error": "AI API key not configured on server"}), 500

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "system": SYSTEM_PROMPT,
            "messages": messages
        }
        ai_resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json=body,
            headers=headers,
            timeout=15
        )
        return jsonify(ai_resp.json()), ai_resp.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)