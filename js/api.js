/**
 * API.JS - API Communication Functions
 * Poornima University Management System
 */



/**
 * Generic API request handler
 */
async function apiRequest(endpoint, method = 'GET', data = null, headers = {}) {
  // Ensure endpoint is a string to avoid malformed URLs (e.g., /api/users/[object Object])
  if (typeof endpoint !== 'string') {
    console.error('apiRequest called with invalid endpoint:', endpoint);
    return null;
  }

  if (endpoint.includes('[object Object]')) {
    console.error('apiRequest called with malformed endpoint containing [object Object]:', endpoint);
    return {
      success: false,
      status: 400,
      data: { message: 'Malformed endpoint: object passed instead of ID', endpoint }
    };
  }

  const token = localStorage.getItem('token');
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...headers
  };

  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers: defaultHeaders
  };

  if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(`${BASE_API_URL}${endpoint}`, options);
    
    if (response.status === 401) {
      // Token expired, logout user
      logout();
      return null;
    }

    if (response.status === 403) {
      showNotification('You do not have permission to access this resource', 'error');
      return null;
    }

    const contentType = response.headers.get('content-type') || '';
    let result;

    if (contentType.includes('application/json')) {
      try {
        result = await response.json();
      } catch (err) {
        console.error('API Response JSON parse error:', err);
        const text = await response.text();
        result = { success: false, message: 'Invalid JSON response from API', body: text };
      }
    } else {
      const text = await response.text();
      console.warn('API responded with non-JSON body:', `${BASE_API_URL}${endpoint}`, 'status:', response.status, 'body:', text);
      result = { success: false, message: 'Non-JSON response from API', body: text };
    }

    if (!response.ok) {
      console.error('API Error:', result);
    }

    return {
      success: response.ok,
      status: response.status,
      data: result
    };
  } catch (error) {
    console.error('API Request Error:', error);
    showNotification('Network error. Please try again.', 'error');
    return null;
  }
}

// ============================================================================
// AUTHENTICATION ENDPOINTS
// ============================================================================

/**
 * User login
 */
async function loginUser(username, password, role) {
  return apiRequest('/auth/login', 'POST', {
    username,
    password,
    role
  });
}

/**
 * User registration
 */
async function registerUser(userData) {
  return apiRequest('/auth/register', 'POST', userData);
}

/**
 * Check username availability
 */
async function checkUsernameAPI(username) {
  return apiRequest('/auth/check-username', 'POST', { username });
}

/**
 * Check email availability
 */
async function checkEmailAPI(email) {
  return apiRequest('/auth/check-email', 'POST', { email });
}

/**
 * Verify token
 */
async function verifyToken() {
  return apiRequest('/auth/verify', 'GET');
}

// ============================================================================
// USER ENDPOINTS
// ============================================================================

/**
 * Get user profile
 */
function normalizeUserId(userId) {
  if (userId == null) return null;
  if (typeof userId === 'object') {
    // support passing object with id/userId key
    const fromOpts = userId.id || userId.userId || userId.user_id;
    if (fromOpts) {
      return String(fromOpts);
    }
    console.warn('normalizeUserId got object; expected primitive', userId);
    return null;
  }
  return String(userId);
}

async function getUserProfile(userId) {
  const normalized = normalizeUserId(userId);
  if (!normalized) {
    console.error('getUserProfile called with invalid userId:', userId);
    return { success: false, status: 400, data: { message: 'Invalid userId' } };
  }
  return apiRequest(`/users/${normalized}`, 'GET');
}

/**
 * Update user profile
 */
async function updateUserProfile(userId, userData) {
  const normalized = normalizeUserId(userId);
  if (!normalized) {
    console.error('updateUserProfile called with invalid userId:', userId);
    return { success: false, status: 400, data: { message: 'Invalid userId' } };
  }
  return apiRequest(`/users/${normalized}`, 'PUT', userData);
}

/**
 * Change password
 */
async function changePassword(userId, currentPassword, newPassword) {
  return apiRequest(`/users/${userId}/change-password`, 'POST', {
    currentPassword,
    newPassword
  });
}

// ============================================================================
// ADMIN ENDPOINTS
// ============================================================================

/**
 * Get admin statistics
 */
async function getAdminStats() {
  return apiRequest('/admin/stats', 'GET');
}

/**
 * Get admin dashboard (combined stats + pending approvals)
 */
async function getAdminDashboard() {
  return apiRequest('/admin/dashboard', 'GET');
}

/**
 * Get pending approvals
 */
async function getPendingApprovals() {
  return apiRequest('/admin/pending-approvals', 'GET');
}

/**
 * Approve user registration
 */
async function approveUserAPI(userId) {
  return apiRequest(`/admin/approve-user/${userId}`, 'POST');
}

/**
 * Reject user registration
 */
async function rejectUserAPI(userId) {
  return apiRequest(`/admin/reject-user/${userId}`, 'POST');
}

/**
 * Get all users
 */
async function getAllUsers(role = null) {
  const endpoint = role ? `/admin/users?role=${role}` : '/admin/users';
  return apiRequest(endpoint, 'GET');
}

/**
 * Delete user
 */
async function deleteUser(userId) {
  return apiRequest(`/admin/users/${userId}`, 'DELETE');
}

/**
 * Get all departments
 */
async function getAllDepartments() {
  return apiRequest('/admin/departments', 'GET');
}

/**
 * Create department
 */
async function createDepartment(deptData) {
  return apiRequest('/admin/departments', 'POST', deptData);
}

/**
 * Update department
 */
async function updateDepartment(deptId, deptData) {
  return apiRequest(`/admin/departments/${deptId}`, 'PUT', deptData);
}

/**
 * Get all subjects
 */
async function getAllSubjects() {
  return apiRequest('/admin/subjects', 'GET');
}

/**
 * Create subject
 */
async function createSubject(subjectData) {
  return apiRequest('/admin/subjects', 'POST', subjectData);
}

// ============================================================================
// ATTENDANCE ENDPOINTS
// ============================================================================

/**
 * List students for attendance (teacher/hod)
 */
async function listAttendanceStudents() {
  return apiRequest('/attendance/students', 'GET');
}

/**
 * Save attendance entries
 */
async function saveAttendance(entries) {
  return apiRequest('/attendance', 'POST', entries);
}

/**
 * Get attendance for a given student
 */
async function getStudentAttendance(studentId) {
  return apiRequest(`/attendance/student/${studentId}`, 'GET');
}

/**
 * Get attendance records by date
 */
async function getAttendanceByDate(date) {
  return apiRequest(`/attendance/date?date=${date}`, 'GET');
}

// ============================================================================
// HOD ENDPOINTS
// ============================================================================

/**
 * Get HOD department data
 */
async function getHodDepartment(hodId) {
  return apiRequest(`/hod/${hodId}/department`, 'GET');
}

/**
 * Get department teachers
 */
async function getDepartmentTeachers(deptId) {
  return apiRequest(`/hod/departments/${deptId}/teachers`, 'GET');
}

/**
 * Get department students
 */
async function getDepartmentStudents(deptId) {
  return apiRequest(`/hod/departments/${deptId}/students`, 'GET');
}

/**
 * Get department attendance stats
 */
async function getDepartmentAttendanceStats(deptId) {
  return apiRequest(`/hod/departments/${deptId}/attendance-stats`, 'GET');
}

/**
 * Get department performance stats
 */
async function getDepartmentPerformanceStats(deptId) {
  return apiRequest(`/hod/departments/${deptId}/performance-stats`, 'GET');
}

// ============================================================================
// TEACHER ENDPOINTS
// ============================================================================

/**
 * Get teacher subjects
 */
async function getTeacherDashboard(teacherId) {
  return apiRequest(`/teacher/${teacherId}/dashboard`, 'GET');
}

/**
 * Get teacher subjects
 */
async function getTeacherSubjects(teacherId) {
  return apiRequest(`/teacher/${teacherId}/subjects`, 'GET');
}

/**
 * Get subject students
 */
async function getSubjectStudents(subjectId) {
  return apiRequest(`/teacher/subjects/${subjectId}/students`, 'GET');
}

/**
 * Submit attendance
 */
async function submitAttendance(subjectId, attendanceData) {
  return apiRequest(`/teacher/subjects/${subjectId}/attendance`, 'POST', attendanceData);
}

/**
 * Upload marks
 */
async function uploadMarks(subjectId, marksData) {
  return apiRequest(`/teacher/subjects/${subjectId}/marks`, 'POST', marksData);
}

/**
 * Create assignment
 */
async function createAssignment(subjectId, assignmentData) {
  return apiRequest(`/teacher/subjects/${subjectId}/assignments`, 'POST', assignmentData);
}

/**
 * Get assignment submissions
 */
async function getAssignmentSubmissions(assignmentId) {
  return apiRequest(`/teacher/assignments/${assignmentId}/submissions`, 'GET');
}

/**
 * Grade assignment
 */
async function gradeAssignment(submissionId, grade, feedback) {
  return apiRequest(`/teacher/submissions/${submissionId}/grade`, 'POST', {
    grade,
    feedback
  });
}

/**
 * Post notice
 */
async function postNotice(noticeData) {
  return apiRequest('/teacher/notices', 'POST', noticeData);
}

// ============================================================================
// STUDENT ENDPOINTS
// ============================================================================

/**
 * Get student academic data
 */
async function getStudentAcademic(studentId) {
  return apiRequest(`/student/${studentId}/academic`, 'GET');
}

/**
 * Get student attendance
 */
async function getStudentAttendance(studentId) {
  return apiRequest(`/student/${studentId}/attendance`, 'GET');
}

/**
 * Get student marks
 */
async function getStudentMarks(studentId) {
  return apiRequest(`/student/${studentId}/marks`, 'GET');
}

/**
 * Get student subjects
 */
async function getStudentSubjects(studentId) {
  return apiRequest(`/student/${studentId}/subjects`, 'GET');
}

/**
 * Get student assignments
 */
async function getStudentAssignments(studentId) {
  return apiRequest(`/student/${studentId}/assignments`, 'GET');
}

/**
 * Submit assignment
 */
async function submitAssignment(assignmentId, submissionData) {
  return apiRequest(`/student/assignments/${assignmentId}/submit`, 'POST', submissionData);
}

/**
 * Get student notices
 */
async function getStudentNotices(studentId) {
  return apiRequest(`/student/${studentId}/notices`, 'GET');
}

/**
 * Get exam schedule
 */
async function getExamSchedule(studentId) {
  return apiRequest(`/student/${studentId}/exam-schedule`, 'GET');
}

/**
 * Get AI prediction
 */
async function getAIPrediction(studentId) {
  return apiRequest(`/student/${studentId}/ai-prediction`, 'GET');
}

// ============================================================================
// ANALYTICS ENDPOINTS
// ============================================================================

/**
 * Get system analytics
 */
async function getSystemAnalytics() {
  return apiRequest('/analytics/system', 'GET');
}

/**
 * Get attendance analytics
 */
async function getAttendanceAnalytics(deptId = null) {
  const endpoint = deptId ? `/analytics/attendance?dept=${deptId}` : '/analytics/attendance';
  return apiRequest(endpoint, 'GET');
}

/**
 * Get performance analytics
 */
async function getPerformanceAnalytics(deptId = null) {
  const endpoint = deptId ? `/analytics/performance?dept=${deptId}` : '/analytics/performance';
  return apiRequest(endpoint, 'GET');
}

/**
 * Generate SAS report
 */
async function generateSASReport(reportType, params = {}) {
  return apiRequest('/analytics/sas-report', 'POST', {
    reportType,
    ...params
  });
}

// ============================================================================
// AI/ML ENDPOINTS
// ============================================================================

/**
 * Get performance prediction
 */
async function getPerformancePrediction(studentId) {
  return apiRequest(`/ai/predict-performance/${studentId}`, 'GET');
}

/**
 * Get dropout risk
 */
async function getDropoutRisk(studentId) {
  return apiRequest(`/ai/dropout-risk/${studentId}`, 'GET');
}

/**
 * Get attendance anomaly detection
 */
async function getAttendanceAnomalies() {
  return apiRequest('/ai/attendance-anomalies', 'GET');
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

/**
 * Upload file
 */
async function uploadFile(file, uploadType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('uploadType', uploadType);

  const token = localStorage.getItem('token');
  const headers = {};
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${BASE_API_URL}/upload`, {
      method: 'POST',
      headers,
      body: formData
    });

    const result = await response.json();
    return {
      success: response.ok,
      status: response.status,
      data: result
    };
  } catch (error) {
    console.error('File Upload Error:', error);
    return {
      success: false,
      error: 'Upload failed'
    };
  }
}

/**
 * Download file
 */
function downloadFile(fileId, filename) {
  const token = localStorage.getItem('token');
  const link = document.createElement('a');
  link.href = `${BASE_API_URL}/download/${fileId}`;
  link.setAttribute('download', filename || 'download');
  
  if (token) {
    link.setAttribute('Authorization', `Bearer ${token}`);
  }
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
