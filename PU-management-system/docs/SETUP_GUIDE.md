# Setup Guide - Poornima University Management System

Complete step-by-step guide to set up and configure the University Management System.

## 📋 Prerequisites

Ensure you have the following installed:
- **Python:** 3.8 or higher ([Download](https://www.python.org/downloads/))
- **MySQL:** 5.7 or higher ([Download](https://dev.mysql.com/downloads/mysql/))
- **Git:** Latest version ([Download](https://git-scm.com/))
- **Text Editor/IDE:** VS Code recommended ([Download](https://code.visualstudio.com/))

### Verify Installations

```bash
# Check Python version
python --version
# Should show: Python 3.x.x

# Check MySQL version
mysql --version
# Should show: mysql  Ver X.X.X

# Check Git version
git --version
# Should show: git version X.X.X
```

---

## 🚀 Installation Steps

### Step 1: Clone Repository

```bash
# Navigate to your desired directory
cd Desktop

# Clone the repository
git clone https://github.com/poornima-university/management-system.git

# Navigate to project folder
cd poornima_university_management_system
```

### Step 2: Set Up MySQL Database

#### Option A: Using MySQL Command Line

```bash
# Start MySQL server
# Windows: MySQL is usually started as a service
# macOS: brew services start mysql
# Linux: sudo systemctl start mysql

# Log in to MySQL
mysql -u root -p
# Enter password when prompted (or leave blank if no password set)

# Create database and tables
mysql -u root -p < database/university-db.sql
# Enter password when prompted
```

#### Option B: Using MySQL Workbench

1. Open MySQL Workbench
2. Create a new connection or use existing
3. Open `database/university-db.sql` file
4. Execute the script (Ctrl+Shift+Enter)
5. Verify all tables are created

#### Option C: Using Command Prompt (Windows)

```cmd
# Navigate to MySQL installation directory
cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"

# Log in
mysql -u root -p

# Execute SQL file
source C:\path\to\database\university-db.sql
```

#### Verify Database Creation

```bash
# Log in to MySQL
mysql -u root -p

# List databases
SHOW DATABASES;
# Should see: university_db

# Select the database
USE university_db;

# List tables
SHOW TABLES;
# Should see 17 tables
```

### Step 3: Set Up Python Environment

#### Create Virtual Environment

```bash
# Navigate to project directory
cd poornima_university_management_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

After activation, your terminal should show `(venv)` prefix.

#### Install Dependencies

```bash
# Make sure you're in the virtual environment
# Install all required packages
pip install -r requirements.txt

# Verify installations
pip list
# Should show: Flask, Flask-CORS, Flask-JWT-Extended, mysql-connector-python, etc.
```

### Step 4: Configure Environment Variables

#### Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your settings
# (Use your favorite text editor)
```

#### Configure Database Connection

Edit `.env` file with your MySQL credentials:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=university_db

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=change_this_to_random_string_in_production

# JWT Configuration
JWT_SECRET_KEY=change_this_to_random_string_in_production
JWT_ACCESS_TOKEN_EXPIRES=2592000

# Server Configuration
PORT=5000
API_BASE_URL=http://localhost:5000/api

# AI / Chatbot Configuration
# (optional) Set your Anthropic API key so the chatbot proxy can function.
# register at https://www.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_key_here

# If you do not plan to run the AI assistant, leave the key blank.

```

#### Generate Secure Keys (Recommended for Production)

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Replace the keys in `.env` with generated values.

### Step 5: Run the Application

All frontend files are served statically by the Flask server. Launch the backend and open the pages from `http://localhost:5000` so that AJAX calls (e.g. chat proxy) work correctly.

```bash
# make sure .env is loaded (using python-dotenv or set variables manually)
set FLASK_APP=backend/app.py
set FLASK_ENV=development
python -m flask run --port=5000
```

Now visit:
- http://localhost:5000/            → main site (index.html)
- http://localhost:5000/chatbot.html → chat demo page

Accessing the HTML files directly via `file://` will **not** allow the chatbot to function because the API proxy is unavailable.

---

## 🗄️ Database Setup Details

### Database Structure

The system creates the following tables:

**User Tables:**
- `credentials` - Login credentials for all users
- `students` - Student information
- `teachers` - Faculty information
- `hods` - Department head information
- `admins` - Administrator information

**Academic Tables:**
- `departments` - Department management
- `subjects` - Course information
- `enrollments` - Student-course mappings
- `marks` - Grades and assessments
- `attendance` - Attendance records
- `assignments` - Assignment details
- `submissions` - Assignment submissions

**Analytics Tables:**
- `exam_schedule` - Exam scheduling
- `notices` - System notifications
- `analytics_cache` - Cached analytics
- `ai_predictions` - ML predictions
- `system_logs` - Activity logs

### Sample Data (Optional)

To populate with sample data:

```bash
# Log in to MySQL
mysql -u root -p university_db

# Insert sample admin
INSERT INTO admins (admin_id, official_email, access_level, status)
VALUES ('ADM001', 'admin@poornima.edu', 'super', 'approved');

INSERT INTO credentials (user_id, role, username, email, password_hash)
VALUES (1, 'admin', 'admin_001', 'admin@poornima.edu', 'hashed_password');
```

---

## 🔧 Backend Configuration

### Flask App Settings

File: `backend/server.py`

Key configurations:
```python
app = Flask(__name__)
app.config['CORS_ORIGINS'] = '*'  # Restrict in production
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 2592000  # 30 days
```

### Database Connection

File: `backend/db_connect.py`

The connection uses environment variables:
```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
```

---

## 🎨 Frontend Configuration

### Update API Base URL

In `frontend/js/api.js`, verify the API base URL:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

Change this if your backend is running on a different URL.

### Serve Frontend Locally

**Option A: Using Python**
```bash
# Navigate to project directory
cd poornima_university_management_system

# Start HTTP server
python -m http.server 8000

# Open browser to: http://localhost:8000/frontend/index.html
```

**Option B: Using Node.js**
```bash
# Install http-server globally
npm install -g http-server

# Start server
http-server .

# Open browser to: http://localhost:8080/frontend/index.html
```

**Option C: Using VS Code Live Server**
1. Install "Live Server" extension in VS Code
2. Right-click on `frontend/index.html`
3. Select "Open with Live Server"

---

## ✅ Verification Checklist

Before starting the application, verify:

- [ ] MySQL database created and tables visible
- [ ] Virtual environment activated
- [ ] All Python packages installed (`pip list`)
- [ ] `.env` file configured with correct credentials
- [ ] Database connection test passed
- [ ] API base URL correct in frontend files
- [ ] Port 5000 is available (or configured alternative port)

---

## 🚨 Common Setup Issues & Solutions

### Issue: "Access Denied for user 'root'@'localhost'"

**Solution:**
```bash
# Try without password
mysql -u root < database/university-db.sql

# Or set MySQL password first
mysql -u root -p

# Then create user with specific permissions
GRANT ALL PRIVILEGES ON university_db.* TO 'root'@'localhost' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
# Activate virtual environment first
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Then install requirements
pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"

**Solution:**
```bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000

# Kill the process
taskkill /PID <PID> /F

# Or change port in .env file
PORT=5001
```

### Issue: "Can't connect to MySQL server"

**Solution:**
```bash
# Check if MySQL is running
# Windows: Services app -> Look for MySQL
# macOS: brew services list
# Linux: systemctl status mysql

# Start MySQL if not running
# Windows: net start MySQL80
# macOS: brew services start mysql
# Linux: sudo systemctl start mysql
```

### Issue: "CORS Policy: No 'Access-Control-Allow-Origin' header"

**Solution:** Already handled in `backend/server.py` with Flask-CORS. If still occurring:
```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8000"}})
```

---

## 📱 Testing the Setup

### Test 1: Database Connection

```bash
# Log into MySQL
mysql -u root -p

# Use the database
USE university_db;

# Check tables
SHOW TABLES;

# View table structure
DESCRIBE students;
```

### Test 2: Backend API

```bash
# Start the server first (see RUN_SERVER.md)
python backend/server.py

# In another terminal, test health endpoint
curl http://localhost:5000/api/health

# Should return:
{"status": "ok"}
```

### Test 3: Frontend Loading

```bash
# Start frontend server
python -m http.server 8000

# Open browser to:
http://localhost:8000/frontend/index.html

# Should see: Home page with navigation and features
```

---

## 🔄 Troubleshooting Connection

### Test Database Connection

Create file `test_connection.py`:

```python
from backend.db_connect import Database

db = Database()
try:
    conn = db.connect()
    if conn:
        print("✓ Database connection successful!")
        db.disconnect()
    else:
        print("✗ Database connection failed")
except Exception as e:
    print(f"✗ Error: {e}")
```

Run test:
```bash
python test_connection.py
```

---

## 🔐 Production Setup Recommendations

### Security Hardening

1. **Change Default Passwords:**
   - Update `.env` with strong passwords
   - Update MySQL root password

2. **Update CORS Settings:**
   ```python
   CORS(app, resources={
       "/api/*": {"origins": ["https://yourdomain.com"]}
   })
   ```

3. **Use HTTPS:**
   - Obtain SSL certificate
   - Configure Flask for HTTPS

4. **Database Backups:**
   ```bash
   mysqldump -u root -p university_db > backup.sql
   ```

5. **Update JWT Secret:**
   ```python
   # Generate strong key
   import secrets
   JWT_SECRET_KEY = secrets.token_urlsafe(32)
   ```

---

## 📚 Next Steps

After successful setup:

1. **Start Backend Server** → See [RUN_SERVER.md](RUN_SERVER.md)
2. **Access Frontend** → Navigate to `http://localhost:8000/frontend/`
3. **Login/Register** → Use test credentials provided in README
4. **Explore Features** → Test different dashboards and functions

---

## 📞 Support

If you encounter any issues:

1. Check this guide and troubleshooting section
2. Review server logs and error messages
3. Check database connectivity
4. Verify all environment variables
5. Contact support at: support@poornima-university.edu

---

**Last Updated:** December 2024
**Version:** 1.0.0
