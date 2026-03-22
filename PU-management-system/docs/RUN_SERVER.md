# Run Server Guide - Poornima University Management System

Complete guide for running the University Management System backend and frontend.

## 🚀 Quick Start

### Prerequisites
- Virtual environment set up (see [SETUP_GUIDE.md](SETUP_GUIDE.md))
- MySQL database created and populated
- `.env` file configured with database credentials

### One-Command Start

```bash
# Activate virtual environment (if not already active)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start backend server
python backend/server.py

# In a new terminal, start frontend
python -m http.server 8000
# Or use: cd frontend && python -m http.server 8000

# Open browser to:
http://localhost:8000/frontend/index.html
```

---

## 📊 Backend Server

### Starting the Flask Backend

```bash
# Make sure virtual environment is activated
# (You should see (venv) in your terminal prompt)

# Navigate to project root
cd poornima_university_management_system

# Start the server
python backend/server.py
```

Expected output:
```
 * Serving Flask app 'server'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Server Configuration

The backend reads configuration from `.env` file:

```env
# Server Port
PORT=5000                    # Default: 5000

# Database
DB_HOST=localhost            # MySQL host
DB_USER=root                 # MySQL username
DB_PASSWORD=your_password    # MySQL password
DB_NAME=university_db        # Database name

# Flask
FLASK_ENV=development        # development or production
FLASK_DEBUG=True             # Enable debug mode

# JWT
JWT_SECRET_KEY=your_key      # Keep secure!
JWT_ACCESS_TOKEN_EXPIRES=2592000  # 30 days in seconds
```

### Change Server Port

If port 5000 is already in use:

```bash
# Option 1: Edit .env file
PORT=5001

# Option 2: Set environment variable (Windows)
set PORT=5001
python backend/server.py

# Option 2: Set environment variable (macOS/Linux)
export PORT=5001
python backend/server.py

# Option 3: Pass as argument
python backend/server.py --port 5001
```

### Test Backend API

```bash
# Health check
curl http://localhost:5000/api/health

# Should return:
{"status": "ok"}

# Check API documentation
curl http://localhost:5000/api

# Should return:
API Documentation: [list of available endpoints]
```

### Backend Endpoints

Once running, you can access:

- **Health Check:** `http://localhost:5000/api/health`
- **API Docs:** `http://localhost:5000/api`
- **Authentication:** `http://localhost:5000/api/auth/*`
- **Admin:** `http://localhost:5000/api/admin/*`
- **Student:** `http://localhost:5000/api/student/*`
- **Teacher:** `http://localhost:5000/api/teacher/*`
- **HOD:** `http://localhost:5000/api/hod/*`

### Debug Mode

Debug mode is enabled by default in development:

```python
# In backend/server.py
if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, port=port)
```

Debug features:
- Auto-reload on code changes
- Interactive debugger on errors
- Detailed error messages

### Stop Backend Server

```bash
# Press CTRL+C in the terminal running the server
```

---

## 🎨 Frontend Server

### Option 1: Python HTTP Server (Recommended)

```bash
# Navigate to project root
cd poornima_university_management_system

# Start server on port 8000
python -m http.server 8000

# Or specify different port
python -m http.server 3000
```

Access in browser:
```
http://localhost:8000/frontend/index.html
```

### Option 2: Node.js HTTP Server

```bash
# Install http-server (if not already installed)
npm install -g http-server

# Start server
http-server .

# Specify port
http-server . -p 3000
```

Access in browser:
```
http://localhost:8080
```

### Option 3: VS Code Live Server

1. Install "Live Server" extension in VS Code
2. Right-click on `frontend/index.html`
3. Select "Open with Live Server"
4. Browser opens automatically on `http://localhost:5500`

### Option 4: Use Development Web Server

For more control, use a proper web server:

**Using PHP (if installed):**
```bash
php -S localhost:8000
```

**Using Ruby (if installed):**
```bash
ruby -run -ehttpd . -p 8000
```

### Frontend Configuration

Update API connection in `frontend/js/api.js`:

```javascript
// Line 1-5
const API_BASE_URL = 'http://localhost:5000/api';

// Change to your backend URL if different:
// const API_BASE_URL = 'http://your-server-url:5000/api';
```

---

## 🔄 Running Both Simultaneously

### Method 1: Multiple Terminal Windows

**Terminal 1 - Backend:**
```bash
cd poornima_university_management_system
source venv/bin/activate  # or venv\Scripts\activate on Windows
python backend/server.py
```

**Terminal 2 - Frontend:**
```bash
cd poornima_university_management_system
python -m http.server 8000
```

**Terminal 3 - Browser:**
```bash
# Open http://localhost:8000/frontend/index.html
```

### Method 2: Run Backend in Background (Linux/macOS)

```bash
# Start backend in background
nohup python backend/server.py > server.log 2>&1 &

# Start frontend
python -m http.server 8000

# Later, kill backend process
kill %1  # or use the process ID
```

### Method 3: Using Process Manager (Production)

```bash
# Install Python process manager
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.server:app

# For debugging/development, use Werkzeug's development server
python backend/server.py
```

---

## 🧪 Testing the Setup

### Test 1: Health Check

```bash
# Make sure backend is running
curl http://localhost:5000/api/health

# Expected response:
{"status": "ok"}
```

### Test 2: Frontend Loading

```bash
# Make sure frontend server is running
curl http://localhost:8000/frontend/index.html

# Or open in browser
```

### Test 3: Login API

```bash
# Test the login endpoint
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_001",
    "password": "Admin@123456",
    "role": "admin"
  }'

# Expected response (if user exists):
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1,
  "role": "admin",
  "userName": "admin_001",
  "message": "Login successful"
}
```

---

## 📋 Usage Workflow

### 1. Access Application

```
Browser → http://localhost:8000/frontend/index.html
```

### 2. Select Action

- **Login:** Click "Login" → Select Role → Enter Credentials
- **Register:** Click "Register" → Select Role → Fill Form

### 3. Navigate Features

```
Based on Role:
├── Admin
│   ├── View system statistics
│   ├── Approve pending users
│   ├── Manage departments and subjects
│   └── View analytics
├── Student
│   ├── View academic records
│   ├── Submit assignments
│   ├── View marks and attendance
│   └── Get AI predictions
├── Teacher
│   ├── Mark attendance
│   ├── Upload marks
│   ├── Create assignments
│   └── Post notices
└── HOD
    ├── View department data
    ├── Manage faculty
    ├── Monitor attendance
    └── View performance analytics
```

---

## 🔐 SSL/HTTPS (Production)

For production environment, use HTTPS:

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update Flask app
python backend/server.py --ssl-certfile=cert.pem --ssl-keyfile=key.pem
```

Update frontend URL:
```javascript
const API_BASE_URL = 'https://localhost:5000/api';
```

---

## 📊 Monitoring & Logging

### Backend Logs

Logs are displayed in the terminal where the server is running:

```
[timestamp] Flask Log: message
[HTTP 200] POST /api/auth/login
[HTTP 201] POST /api/admin/departments
[HTTP 400] Bad Request
```

### Save Logs to File

```bash
# Redirect output to file
python backend/server.py > server.log 2>&1

# Monitor logs in real-time
tail -f server.log  # macOS/Linux
Get-Content server.log -Tail 10  # Windows PowerShell
```

### Database Query Logs

Enable MySQL query logging:

```sql
SET GLOBAL general_log = 'ON';
SET GLOBAL log_output = 'TABLE';

-- View logs
SELECT * FROM mysql.general_log;

-- Disable
SET GLOBAL general_log = 'OFF';
```

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Error: "Address already in use"**
```bash
# Kill process on port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

**Error: "Module not found"**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Error: "Database connection failed"**
```bash
# Check .env file
cat .env

# Verify MySQL is running
mysql -u root -p -e "SELECT 1"

# Test connection directly
python -c "from backend.db_connect import db; db.connect(); print('OK')"
```

### Frontend Won't Load

**Error: "API connection refused"**
1. Verify backend is running on port 5000
2. Check API_BASE_URL in `frontend/js/api.js`
3. Verify CORS is enabled in `backend/server.py`

**Error: "404 File not found"**
1. Verify frontend server is running
2. Check file paths are correct
3. Verify working directory

### Slow Performance

1. **Backend:** Check database for slow queries
2. **Frontend:** Check browser console for JavaScript errors
3. **Network:** Check API response times with browser DevTools

---

## 📱 Accessing from Other Devices

### Local Network Access

**Update addresses:**

Frontend:
```
http://<your-computer-ip>:8000/frontend/index.html
```

Backend API:
```
http://<your-computer-ip>:5000/api
```

Update in `frontend/js/api.js`:
```javascript
const API_BASE_URL = 'http://<your-computer-ip>:5000/api';
```

**Find your IP:**
```bash
# Windows
ipconfig

# macOS/Linux
ifconfig | grep "inet "
```

---

## 🚀 Production Deployment

### Using Gunicorn

```bash
# Install
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 backend.server:app

# With timeout and logging
gunicorn -w 4 -b 0.0.0.0:5000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  backend.server:app
```

### Using Nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/university
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /frontend {
        alias /path/to/frontend;
    }
}
```

### Environment Variables for Production

```bash
# .env (production)
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=strong_random_key_here
JWT_SECRET_KEY=strong_random_key_here
CORS_ORIGINS=https://yourdomain.com
```

---

## 📞 Support & Help

For issues:
1. Check the troubleshooting section above
2. Review `docs/SETUP_GUIDE.md` for installation help
3. Check server logs for error messages
4. Contact: support@poornima-university.edu

---

**Last Updated:** December 2024
**Version:** 1.0.0
**Status:** Production Ready
