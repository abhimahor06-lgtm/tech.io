# Poornima University Management System

A comprehensive, role-based **University Management System** built with modern web technologies. The system provides integrated management of students, teachers, HODs (Heads of Department), and administrators with advanced analytics, AI/ML-powered predictions, and SAS reporting capabilities.

## 🎯 Features

### 📊 Four Role-Based Dashboards
- **Admin Dashboard:** System-wide management, user approvals, department & subject management
- **HOD Dashboard:** Department oversight, teacher/student management, attendance & performance analytics
- **Teacher Dashboard:** Class management, attendance tracking, marking, assignments, student notices
- **Student Dashboard:** Academic tracking, marks, attendance, assignments, AI performance predictions

### 🔐 Authentication & Authorization
- Role-based registration and login system
- Secure JWT-based authentication
- Password hashing using Werkzeug
- Different registration requirements per role

### 📈 Advanced Analytics
- Real-time attendance analytics
- Performance tracking and reporting
- Department-level statistics
- SAS integration for statistical analysis

### 🤖 AI/ML Capabilities
- **Performance Prediction:** Predict student semester GPA
- **Dropout Risk Detection:** Identify at-risk students
- **Attendance Anomaly Detection:** Flag unusual attendance patterns
- **Scikit-learn Models:** Machine learning models trained on historical data

### 🎨 Modern UI/UX
- **Neumorphism Design:** Soft shadows, smooth animations, intuitive layout
- **Responsive Design:** Mobile, tablet, and desktop support
- **Interactive Dashboards:** Dynamic data visualization and management
- **Form Validation:** Client-side and server-side validation

### 📱 Multi-Platform Support
- **Frontend:** HTML5, CSS3, JavaScript ES6+
- **Backend:** Python Flask with REST API
- **Database:** MySQL
- **Analytics:** SAS scripts
- **ML Models:** Scikit-learn

## 🤖 AI Support Chat

The frontend includes a floating **AI support chatbot** widget that appears on every page. It is powered by an Anthropic Claude model via the `/api/chat` endpoint.

- The widget script (`/js/chat-widget.js`) is injected into all HTML pages and automatically loads its stylesheet.
- Anyone visiting any page can open the chat without logging in; no authentication is required.
- The backend automatically reads the markdown files in the `docs/` directory at startup and prepends them to the AI system prompt, so the assistant is aware of every detail of the project.

You can customize the `SYSTEM_PROMPT` in `backend/server.py` (or `app.py` for the simpler server) if you wish to add more context.

## 📂 Project Structure

```
poornima_university_management_system/
├── frontend/
│   ├── index.html                    # Home page
│   ├── about.html                    # About page
│   ├── admissions.html               # Admissions information
│   ├── privacy-policy.html           # Privacy policy
│   ├── login/
│   │   ├── role-selection.html       # Choose login role
│   │   ├── adminLogin.html           # Admin login
│   │   ├── hodLogin.html             # HOD login
│   │   ├── teacherLogin.html         # Teacher login
│   │   └── studentLogin.html         # Student login
│   ├── register/
│   │   ├── registration-selection.html  # Choose registration role
│   │   ├── adminReg.html             # Admin registration
│   │   ├── hodReg.html               # HOD registration
│   │   ├── teacherReg.html           # Teacher registration
│   │   └── studentReg.html           # Student registration
│   ├── dashboard/
│   │   ├── adminDashboard.html       # Admin control panel
│   │   ├── hodDashboard.html         # HOD management panel
│   │   ├── teacherDashboard.html     # Teacher panel
│   │   └── studentDashboard.html     # Student panel
│   ├── css/
│   │   └── style.css                 # Global neumorphism stylesheet
│   └── js/
│       ├── main.js                   # Global utilities and initialization
│       ├── auth.js                   # Authentication handlers
│       ├── dashboard.js              # Dashboard functionality
│       └── api.js                    # API client with 50+ endpoints
├── backend/
│   ├── server.py                     # Flask app initialization
│   ├── db_connect.py                 # MySQL connection wrapper
│   ├── routes/
│   │   ├── auth_routes.py            # Authentication endpoints
│   │   ├── student_routes.py         # Student endpoints
│   │   ├── teacher_routes.py         # Teacher endpoints
│   │   ├── hod_routes.py             # HOD endpoints
│   │   └── admin_routes.py           # Admin endpoints
│   └── ai_ml/
│       └── predictor.py              # ML models & predictions
├── database/
│   └── university-db.sql             # Database schema & migrations
├── sas/
│   ├── student_analysis.sas          # Student statistics analysis
│   ├── attendance_analysis.sas       # Attendance reporting
│   └── performance_report.sas        # Performance analytics
├── docs/
│   ├── README.md                     # Project overview (this file)
│   ├── SETUP_GUIDE.md                # Installation & setup instructions
│   └── RUN_SERVER.md                 # Server startup guide
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
└── .gitignore                        # Git ignore file

```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- Node.js (optional, for any build tools)
- Git

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/poornima-university/management-system.git
   cd poornima_university_management_system
   ```

2. **Setup Database**
   ```bash
   mysql -u root -p < database/university-db.sql
   ```

3. **Install Backend Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and configuration
   ```

5. **Start Backend Server**
   ```bash
   python backend/server.py
   ```

6. **Open Frontend**
   Open `frontend/index.html` in your web browser or serve with a local server:
   ```bash
   # Using Python
   python -m http.server 8000
   # Open http://localhost:8000/frontend/index.html
   ```

## 🔑 Default Test Credentials

### Admin Account
- **Username:** admin_001
- **Password:** Admin@123456
- **Role:** Admin

### Sample Student Account
- **Username:** student_001
- **Password:** Student@123456
- **Role:** Student

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/auth/register              Register new user
POST /api/auth/login                 User login
GET  /api/auth/verify                Verify JWT token
POST /api/auth/check-username        Check username availability
POST /api/auth/check-email           Check email availability
```

### Admin Endpoints
```
GET  /api/admin/stats                System statistics
GET  /api/admin/dashboard            Combined dashboard data (stats + pending approvals)
GET  /api/admin/pending-approvals    Get pending user approvals
POST /api/admin/approve-user/{id}    Approve user registration
POST /api/admin/reject-user/{id}     Reject user registration
GET  /api/admin/users                Get all users
GET  /api/admin/departments          Get all departments
POST /api/admin/departments          Create new department
GET  /api/admin/subjects             Get all subjects
POST /api/admin/subjects             Create new subject
```

### Student Endpoints
```
GET  /api/student/{id}/academic      Get academic data
GET  /api/student/{id}/attendance    Get attendance records
GET  /api/student/{id}/marks         Get marks & grades
GET  /api/student/{id}/subjects      Get enrolled subjects
GET  /api/student/{id}/assignments   Get assignments
GET  /api/student/{id}/notices       Get notices
GET  /api/student/{id}/exam-schedule Get exam schedule
GET  /api/student/{id}/ai-prediction Get AI predictions
POST /api/student/{id}/assignments/{assignmentId}/submit  Submit assignment
```

### Attendance Endpoints
```
GET  /api/attendance/students              List students available to logged‑in teacher/HOD
POST /api/attendance                       Save attendance array (teacher/HOD only)
GET  /api/attendance/student/{id}          Get history for a single student
GET  /api/attendance/date?date=YYYY-MM-DD  Get all records for a particular date
```


### Teacher Endpoints
```
GET  /api/teacher/{id}/subjects      Get teaching subjects
GET  /api/teacher/subjects/{subjectId}/students     Get subject students
POST /api/teacher/subjects/{id}/attendance         Mark attendance
POST /api/teacher/subjects/{id}/marks              Upload marks
POST /api/teacher/subjects/{id}/assignments        Create assignment
GET  /api/teacher/assignments/{id}/submissions     Get submissions
POST /api/teacher/submissions/{id}/grade           Grade submission
POST /api/teacher/notices                          Post notice
```

### HOD Endpoints
```
GET  /api/hod/{id}/department        Get department data
GET  /api/hod/departments/{dept}/teachers         Get department teachers
GET  /api/hod/departments/{dept}/students         Get department students
GET  /api/hod/departments/{dept}/attendance-stats Get attendance analytics
GET  /api/hod/departments/{dept}/performance-stats Get performance analytics
```

## 🤖 AI/ML Models

### Performance Predictor
Predicts student's semester GPA based on:
- Internal marks
- Midterm exam scores
- Attendance records
- Subject credits

### Dropout Risk Detector
Identifies at-risk students using:
- Attendance percentage
- Average marks
- Class participation

### Attendance Anomaly Detector
Flags unusual attendance patterns and alerts for:
- Consistent low attendance
- Sudden drops in participation
- At-risk indicators

## 🔒 Security Features

- **JWT Authentication:** 30-day token expiry
- **Password Hashing:** Werkzeug password hashing (PBKDF2)
- **Role-Based Access Control:** Middleware validates user roles
- **CORS Protection:** Restricted cross-origin requests
- **Input Validation:** Server-side and client-side validation
- **SQL Injection Prevention:** Parameterized queries

## 📊 Database Schema

### Core Tables
- `users` - User credentials and authentication
- `students` - Student information
- `teachers` - Faculty information
- `hods` - Department head information
- `admins` - Administrator information

### Academic Tables
- `departments` - Department information
- `subjects` - Course information
- `enrollments` - Student-course mappings
- `marks` - Student grades and assessments
- `attendance` - Attendance records
- `assignments` - Assignment information
- `submissions` - Assignment submissions

### Analytics Tables
- `analytics_cache` - Cached analytics data
- `ai_predictions` - ML model predictions
- `system_logs` - System activity logs

## 🎨 Design System

### Color Palette
- **Primary:** Indigo (#6366f1)
- **Success:** Green (#10b981)
- **Danger:** Red (#ef4444)
- **Warning:** Amber (#f59e0b)
- **Info:** Cyan (#0ea5e9)

### Typography
- **Font Family:** -apple-system, BlinkMacSystemFont, Segoe UI, Roboto
- **Primary Font Size:** 16px
- **Heading Sizes:** 32px, 28px, 24px, 20px

### Neumorphism Style
- **Border Radius:** 12px (default), 16px (large), 8px (small)
- **Shadows:** Multi-layer soft shadows for depth
- **Transitions:** 0.3s smooth animations

## 🧪 Testing

### Manual Testing
1. Navigate to `frontend/index.html`
2. Click "Login as Student" or "Register as Student"
3. Use test credentials provided above
4. Explore dashboard features

### API Testing
```bash
# Test health check
curl http://localhost:5000/api/health

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student_001","password":"Student@123456","role":"student"}'
```

## 🔄 Workflow Examples

### Student Registration & Login
1. Student fills registration form with personal, academic, and document info
2. Admin approves registration via admin dashboard
3. Student logs in with approved credentials
4. Dashboard shows academic data, marks, assignments, and AI predictions

### Teacher Marking Attendance
1. Teacher navigates to attendance section
2. Selects subject and date
3. Marks attendance for each student
4. System updates attendance records
5. Analytics reflect updated attendance data

### HOD Viewing Analytics
1. HOD logs in and views department dashboard
2. Reviews attendance analytics per student
3. Checks performance statistics
4. Verifies teacher qualifications

## 📈 Performance & Scalability

- **Database:** Optimized indexes on frequently queried columns
- **API:** RESTful design with proper caching
- **Frontend:** Lazy loading and optimized asset delivery
- **ML Models:** Batch prediction support

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```
Solution: Check .env file, verify MySQL is running, check credentials
```

**JWT Token Expired**
```
Solution: User will be logged out, re-login to get new token
```

**Port Already in Use**
```
Solution: Change PORT in .env or kill process using port 5000
```

## 📝 Documentation

Detailed documentation available in:
- [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) - Installation and configuration
- [RUN_SERVER.md](docs/RUN_SERVER.md) - Server startup and deployment
- [API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API documentation (if available)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👥 Support & Contact

For support, email: support@poornima-university.edu
Or create an issue in the GitHub repository.

## 🙏 Acknowledgments

- Poornima University Administration
- Open-source community (Flask, Scikit-learn, MySQL)
- Design inspiration from modern neumorphism design patterns

---

**Last Updated:** December 2024
**Version:** 1.0.0
**Status:** Production Ready
