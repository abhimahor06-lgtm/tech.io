# 🚀 Complete Startup and Testing Guide
# Poornima University Management System

---

## 📋 CHECKLIST BEFORE STARTING

- [ ] MySQL Server 8.0 installed and running
- [ ] Database created via `setup_database.ps1`
- [ ] `.env` file configured with MySQL credentials
- [ ] Python virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)

---

## 🔧 STARTUP SEQUENCES

### OPTION 1: Full Stack (Recommended)

#### 1. Start Backend Server (Terminal 1)
```powershell
# Navigate to project
cd C:\Poornima_university_management_system

# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Verify Python packages
python -m pip list | grep -E "Flask|scikit-learn|pandas|numpy"

# Start Flask server
python backend/server.py
```

Expected output:
```
✓ Database connected
	╔════════════════════════════════════════════════╗
	║   Poornima University Management System        ║
	║   Flask Server Starting...                     ║
	╚════════════════════════════════════════════════╝

 * Running on http://127.0.0.1:5000
```

#### 2. Start Frontend Server (Terminal 2)

**Option A: Python HTTP Server**
```powershell
# From project root
cd C:\Poornima_university_management_system\frontend
python -m http.server 8000
```

**Option B: Using Python from root**
```powershell
cd C:\Poornima_university_management_system
python -m http.server 8000 --directory frontend
```

Expected output:
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

#### 3. Open in Browser (Terminal 3 / Browser)
```
http://localhost:8000
```

---

## 🧪 TESTING ENDPOINTS

### Phase 1: Pre-Database Tests (Can run before MySQL setup)

#### Test 1: Health Check
```powershell
# Check if backend is responding
curl http://localhost:5000/api/health

# Expected response:
# {"success": true, "message": "Server is running", "status": "healthy"}
```

---

### Phase 2: Post-Database Tests (After MySQL setup)

#### Test 2: User Registration (Create Test Account)

```powershell
# Student Registration
curl -X POST http://localhost:5000/api/auth/register `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "role": "student",
  "username": "john_doe",
  "password": "SecurePass123",
  "confirmPassword": "SecurePass123",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@university.edu",
  "phone": "9876543210",
  "dob": "2000-05-15",
  "gender": "M",
  "enrollmentNumber": "STU001",
  "program": "B.Tech CSE",
  "department": "Computer Science",
  "semester": 1
}
EOF
```

Expected response:
```json
{
  "success": true,
  "message": "Student registered successfully. Awaiting admin approval.",
  "userId": 1
}
```

#### Test 3: User Login

```powershell
# Admin Login (if sample data was inserted)
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "admin"
  }'

# Expected response includes JWT token:
{
  "success": true,
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "userId": 1,
  "role": "admin",
  "userName": "Admin User"
}
```

#### Test 4: Get Admin Statistics (Requires JWT Token)

```powershell
# Save token from login response
$token = "YOUR_JWT_TOKEN_HERE"

# Get admin stats
curl -X GET http://localhost:5000/api/admin/stats `
# new combined endpoint
echo
curl -X GET http://localhost:5000/api/admin/dashboard `
  -H "Authorization: Bearer $token"

# Expected response:
{
  "success": true,
  "totalStudents": 0,
  "totalTeachers": 0,
  "totalHods": 0,
  "totalDepartments": 0
}
```

#### Test 5: Get/Create Departments

```powershell
# Get all departments
curl -X GET http://localhost:5000/api/admin/departments `
  -H "Authorization: Bearer $token"

# Create new department
curl -X POST http://localhost:5000/api/admin/departments `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d '{
    "name": "Computer Science",
    "hodId": null
  }'
```

#### Test 6: Student Academic Data

```powershell
# Get student academic data
curl -X GET http://localhost:5000/api/student/1/academic `
  -H "Authorization: Bearer $token"

# Expected response:
{
  "success": true,
  "cgpa": 3.65,
  "attendance": 85.5,
  "subjectCount": 6,
  "assignmentProgress": "12/15",
  "student": {...}
}
```

---

## 🌐 FRONTEND TESTING

### Via Browser

1. **Navigate to Home**
   ```
   http://localhost:8000
   ```

2. **Test Role Selection**
   - Click "Login" → Select Role (Admin/HOD/Teacher/Student)
   - Click "Register" → Select Role

3. **Test Registration Flow**
   - Fill form with test data
   - System checks username/email availability in real-time
   - Submit and verify success message

4. **Test Login Flow**
   - Admin Login: `admin` / `admin123` (if sample data installed)
   - Student Login: Use account created in Test 2
   - Verify JWT token received

5. **Test Dashboards**
   - After login, verify role-specific dashboard loads
   - Check sidebar navigation
   - Verify data displays (may show mock data if no actual data yet)

---

## 📊 FULL INTEGRATION TEST SCRIPT

Create `test_api.ps1`:

```powershell
# Colors for output
$success = "Green"
$error = "Red"
$info = "Cyan"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $info
Write-Host "  API Integration Test Suite" -ForegroundColor $info
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $info

$BASE_URL = "http://localhost:5000/api"

# Test 1: Health Check
Write-Host "`n[1] Testing Health Check..." -ForegroundColor $info
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
    if ($health.success) {
        Write-Host "✓ Health Check Passed" -ForegroundColor $success
    }
} catch {
    Write-Host "✗ Health Check Failed: $_" -ForegroundColor $error
}

# Test 2: Check Username Availability
Write-Host "`n[2] Testing Username Check..." -ForegroundColor $info
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/check-username" `
        -Method Post `
        -ContentType "application/json" `
        -Body '{"username":"testuser123"}'
    Write-Host "✓ Username Check: Available=$($response.available)" -ForegroundColor $success
} catch {
    Write-Host "✗ Username Check Failed: $_" -ForegroundColor $error
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $info
Write-Host "  Test Complete" -ForegroundColor $info
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $info
```

Run it:
```powershell
.\test_api.ps1
```

---

## 🐛 TROUBLESHOOTING

### Backend Issues

**Error: "Connection Error: 1045"**
- MySQL not installed or not running
- Check: `services.msc` → MySQL80 should be "Running"
- Start MySQL: `net start MySQL80`

**Error: "Port 5000 already in use"**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or change port in .env: PORT=5001
```

**Error: "ModuleNotFoundError: No module named 'sklearn'"**
```powershell
pip install scikit-learn pandas numpy
```

### Frontend Issues

**CORS Error: "No 'Access-Control-Allow-Origin'"**
- Backend not running
- Frontend and backend on different ports (expected)
- Check browser console for exact error

**Blank Dashboard**
- JWT token expired or invalid
- Database has no data yet (ok - will show empty sections)
- Check browser console for API errors

### Database Issues

**Error: "Table 'university_db.students' doesn't exist"**
- Database setup didn't complete
- Re-run: `.\setup_database.ps1`
- Verify: `mysql -u root -p -e "USE university_db; SHOW TABLES;"`

---

## 📝 TESTING CHECKLIST

- [ ] Backend starts successfully
- [ ] Health check endpoint responds
- [ ] Frontend loads and displays homepage
- [ ] Role selection works (login & register)
- [ ] Registration form validates input
- [ ] Login generates JWT token
- [ ] Admin dashboard loads with statistics
- [ ] Student academic data displays
- [ ] Can create department (admin)
- [ ] Can view attendance (after marking)
- [ ] Marks upload functionality works
- [ ] Assignment submission works
- [ ] Logout clears session

---

## 🎯 NEXT STEPS

1. **Install MySQL** (if not done) - ~15 minutes
2. **Run setup_database.ps1** - ~2 minutes
3. **Update .env with credentials** - ~1 minute
4. **Start backend** - ~5 seconds
5. **Start frontend** - ~5 seconds
6. **Test via browser** - ~10 minutes

**Total time**: ~35 minutes

---

**Need Help?** Check logs:
- Backend: `logs/server.log`
- Database: MySQL error log in `C:\ProgramData\MySQL\MySQL Server 8.0\Data\`
- Browser: F12 → Console tab

