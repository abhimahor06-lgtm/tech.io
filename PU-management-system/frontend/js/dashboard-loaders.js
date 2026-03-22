/**
 * DASHBOARD-LOADERS.JS
 * Comprehensive Dynamic Dashboard Data Loader
 * Poornima University Management System
 * 
 * This centralized module handles all API calls for loading dashboard sections
 * across all four user roles: Admin, HOD, Teacher, Student
 */

const API_BASE_URL = 'http://localhost:5000/api';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format date string to readable format
 */
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  } catch (e) {
    return dateStr;
  }
}

/**
 * Make authenticated API request
 */
async function apiCall(endpoint, method = 'GET', data = null) {
  try {
    const token = localStorage.getItem('token');
    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (response.status === 401) {
      localStorage.clear();
      window.location.href = '../login/role-selection.html';
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    return { success: false, message: error.message };
  }
}

/**
 * Update section with loading state
 */
function setLoading(sectionId, isLoading = true) {
  const section = document.querySelector(`#${sectionId}`);
  if (!section) return;
  
  if (isLoading) {
    section.innerHTML = '<div class="loading">⏳ Loading...</div>';
  }
}

/**
 * Show error message in section
 */
function showError(sectionId, message = 'Error loading data') {
  const section = document.querySelector(`#${sectionId}`);
  if (!section) return;
  
  section.innerHTML = `<div class="error-message">❌ ${message}</div>`;
}

// ============================================================================
// ADMIN DASHBOARD LOADERS
// ============================================================================

/**
 * Load admin overview stats
 */
async function loadAdminOverview() {
  const sectionId = 'overview-section';
  setLoading(sectionId);

  // use combined dashboard endpoint to reduce round trips
  const result = await apiCall('/admin/dashboard');
  
  if (result.success) {
    const stats = [
      { key: 'totalStudents', icon: '👨‍🎓', title: 'Total Students' },
      { key: 'totalTeachers', icon: '👨‍🏫', title: 'Total Teachers' },
      { key: 'totalHods', icon: '🧑‍💼', title: 'Total HODs' },
      { key: 'totalDepartments', icon: '🏢', title: 'Departments' }
    ];

    const section = document.querySelector(`#${sectionId}`);
    if (section) {
      let html = '<div class="stats-grid">' + stats.map(stat => `
        <div class="stat-card">
          <div class="stat-icon">${stat.icon}</div>
          <h3>${stat.title}</h3>
          <p class="stat-number">${result[stat.key] || 0}</p>
        </div>
      `).join('') + '</div>';

      // show pending approvals summary if available
      if (typeof result.pendingApprovals !== 'undefined') {
        html += `<div class="pending-summary">
                  <p>Pending approvals: <strong>${result.pendingApprovals}</strong></p>
                </div>`;
      }

      section.innerHTML = html;
    }

    // if we also received recent approvals, add to approvals list section
    if (Array.isArray(result.recentApprovals) && result.recentApprovals.length) {
      const listSection = document.querySelector('#approvals-section');
      if (listSection) {
        let html = '<h4>Recent Requests</h4><div class="approvals-list">';
        result.recentApprovals.forEach(ap => {
          html += `
            <div class="approval-card">
              <div class="approval-info">
                <div class="approval-role role-${ap.role}">${ap.role}</div>
                <h4>${ap.name}</h4>
                <p>${ap.email}</p>
                <small>${formatDate(ap.created_at)}</small>
              </div>
            </div>
          `;
        });
        html += '</div>';
        listSection.innerHTML = html;
      }
    }

  } else {
    showError(sectionId, result.message);
  }
}

/**
 * Load admin approvals
 */
async function loadAdminApprovals() {
  const sectionId = 'approvals-section';
  setLoading(sectionId);

  const result = await apiCall('/admin/pending-approvals');
  
  if (result.success) {
    const approvals = result.approvals || [];
    
    if (approvals.length === 0) {
      const section = document.querySelector(`#${sectionId}`);
      if (section) section.innerHTML = '<p class="info-message">✅ No pending approvals</p>';
      return;
    }

    const section = document.querySelector(`#${sectionId}`);
    if (section) {
      let html = '<div class="approvals-list">';
      
      approvals.forEach(approval => {
        html += `
          <div class="approval-card">
            <div class="approval-info">
              <div class="approval-role role-${approval.role}">${approval.role}</div>
              <h4>${approval.name}</h4>
              <p>${approval.email}</p>
              <small>${formatDate(approval.appliedDate)}</small>
            </div>
            <div class="approval-actions">
              <button class="btn-approve" onclick="approveUser('${approval.role}', ${approval.id})">✅ Approve</button>
              <button class="btn-reject" onclick="rejectUser('${approval.role}', ${approval.id})">❌ Reject</button>
            </div>
          </div>
        `;
      });
      
      html += '</div>';
      section.innerHTML = html;
    }
  } else {
    showError(sectionId, result.message);
  }
}

/**
 * Approve user (callback)
 */
async function approveUser(role, userId) {
  const result = await apiCall(`/admin/approve-user/${role}/${userId}`, 'POST');
  
  if (result.success) {
    alert('✅ User approved');
    loadAdminApprovals();
  } else {
    alert('❌ Error: ' + result.message);
  }
}

/**
 * Reject user (callback)
 */
async function rejectUser(role, userId) {
  if (confirm('Are you sure you want to reject this user?')) {
    const result = await apiCall(`/admin/reject-user/${role}/${userId}`, 'POST');
    
    if (result.success) {
      alert('✅ User rejected');
      loadAdminApprovals();
    } else {
      alert('❌ Error: ' + result.message);
    }
  }
}

async function loadAdminUsers() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/admin/users', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#users-section tbody');
    if (!table) return;
    table.innerHTML = '';
    (data.users || []).forEach(u => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${u.username || ''}</td><td>${u.role}</td><td>${u.email}</td><td>${u.status}</td>`;
      table.appendChild(tr);
    });
  } catch (e) {
    console.error('loadAdminUsers error:', e);
  }
}

async function loadAdminDepartments() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/admin/departments', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#departments-section tbody');
    if (table) table.innerHTML = ((data.departments || [])).map(d => `<tr><td>${d.name}</td><td>${d.hod || 'N/A'}</td></tr>`).join('');
  } catch (e) {
    console.error('loadAdminDepartments error:', e);
  }
}

async function loadAdminSubjects() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/admin/subjects', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#subjects-section tbody');
    if (table) table.innerHTML = ((data.subjects || [])).map(s => `<tr><td>${s.subject_code}</td><td>${s.subject_name}</td><td>${s.department}</td></tr>`).join('');
  } catch (e) {
    console.error('loadAdminSubjects error:', e);
  }
}

async function loadAdminAnalytics() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/admin/analytics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const stats = await res.json();
    const items = document.querySelectorAll('#analytics-section .analytics-item p.highlight');
    if (items[0]) items[0].textContent = (stats.avgAttendance || 0) + '%';
    if (items[1]) items[1].textContent = (stats.avgGPA || 0).toFixed(2);
    if (items[2]) items[2].textContent = (stats.dropoutRate || 0) + '%';
  } catch (e) {
    console.error('loadAdminAnalytics error:', e);
  }
}

async function loadAdminAIInsights() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/admin/ai-insights', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const card = document.querySelector('#ai-insights-section .card');
    if (card) {
      card.innerHTML = `<h3>AI Insights</h3><p>At-Risk: ${data.atRisk || 0}</p><p>Top: ${data.topPerformers || 0}</p>`;
    }
  } catch (e) {
    console.error('loadAdminAIInsights error:', e);
  }
}

// HOD LOADERS
async function loadHodTeachers() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/teachers', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#teachers-section tbody');
    if (table) {
      table.innerHTML = ((data.teachers || [])).map(t => {
        const name = `${t.first_name || ''} ${t.last_name || ''}`.trim();
        return `<tr><td>${name}</td><td>${t.email}</td><td>${t.status}</td></tr>`;
      }).join('');
    }
  } catch (e) {
    console.error('loadHodTeachers error:', e);
  }
}

async function loadHodStudents() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/students', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#students-section tbody');
    if (table) {
      table.innerHTML = ((data.students || [])).map(s => {
        const name = `${s.first_name || ''} ${s.last_name || ''}`.trim();
        return `<tr><td>${name}</td><td>${s.enrollment_number}</td><td>${s.program}</td></tr>`;
      }).join('');
    }
  } catch (e) {
    console.error('loadHodStudents error:', e);
  }
}

async function loadHodAttendanceStats() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/attendance-stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#attendance-section tbody');
    if (table) {
      table.innerHTML = ((data.statistics || [])).map(s => `<tr><td>${s.name}</td><td>${(s.attendance_percent || 0).toFixed(1)}%</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadHodAttendanceStats error:', e);
  }
}

async function loadHodPerformanceStats() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/performance-stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#performance-section tbody');
    if (table) {
      table.innerHTML = ((data.statistics || [])).map(s => `<tr><td>${s.name}</td><td>${(s.avg_marks || 0).toFixed(1)}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadHodPerformanceStats error:', e);
  }
}

// TEACHER LOADERS
async function loadTeacherSubjects() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/teacher/subjects', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#subjects-section tbody');
    if (table) {
      table.innerHTML = ((data.subjects || [])).map(s => `<tr><td>${s.subject_code}</td><td>${s.subject_name}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadTeacherSubjects error:', e);
  }
}

async function loadTeacherStudents() {
  // Placeholder - implement when needed
}

// STUDENT LOADERS
async function loadStudentProfile() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/academic`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.student) {
      const info = document.querySelector('#profile-section .profile-info');
      if (info) {
        const name = `${data.student.first_name || ''} ${data.student.last_name || ''}`.trim();
        info.innerHTML = `
          <p><strong>Name:</strong> ${name}</p>
          <p><strong>Enrollment:</strong> ${data.student.enrollment_number}</p>
          <p><strong>Program:</strong> ${data.student.program}</p>
          <p><strong>CGPA:</strong> ${(data.cgpa || 0).toFixed(2)}</p>
        `;
      }
    }
  } catch (e) {
    console.error('loadStudentProfile error:', e);
  }
}

async function loadStudentAttendance() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/attendance`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#attendance-section tbody');
    if (table) {
      table.innerHTML = ((data.attendance || [])).map(a => `<tr><td>Subject ${a.subject_id}</td><td>${(a.percentage || 0).toFixed(1)}%</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentAttendance error:', e);
  }
}

async function loadStudentMarks() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/marks`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#marks-section tbody');
    if (table) {
      table.innerHTML = ((data.marks || [])).map(m => `<tr><td>Subject ${m.subject_id}</td><td>${m.total || 'N/A'}</td><td>${m.grade || 'N/A'}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentMarks error:', e);
  }
}

async function loadStudentSubjects() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/subjects`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#subjects-section tbody');
    if (table) {
      table.innerHTML = ((data.subjects || [])).map(s => `<tr><td>${s.subject_code}</td><td>${s.subject_name}</td><td>${s.credits}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentSubjects error:', e);
  }
}

async function loadStudentAssignments() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/assignments`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#assignments-section tbody');
    if (table) {
      table.innerHTML = ((data.assignments || [])).map(a => `<tr><td>${a.title}</td><td>${a.subject_name}</td><td>${formatDate(a.due_date)}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentAssignments error:', e);
  }
}

async function loadStudentExamSchedule() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/exam-schedule`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#exam-schedule-section tbody');
    if (table) {
      table.innerHTML = ((data.exams || [])).map(e => `<tr><td>${e.subject_name}</td><td>${e.exam_type}</td><td>${formatDate(e.exam_date)}</td><td>${e.location}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentExamSchedule error:', e);
  }
}

async function loadStudentNotices() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/notices`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const div = document.querySelector('#notices-section');
    if (div) {
      div.innerHTML = ((data.notices || [])).map(n => `<div class="notice"><h4>${n.title}</h4><p>${n.content}</p><small>${formatDate(n.posted_date)}</small></div>`).join('');
    }
  } catch (e) {
    console.error('loadStudentNotices error:', e);
  }
}

async function loadStudentAIPrediction() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/ai-prediction`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const card = document.querySelector('#ai-prediction-section .card');
    if (card) {
      card.innerHTML = `<h3>AI Predictions</h3><p>Risk: ${data.dropout_risk}</p><p>Suggestion: ${data.recommendation}</p>`;
    }
  } catch (e) {
    console.error('loadStudentAIPrediction error:', e);
  }
}


// ============================================================================
// HOD DASHBOARD LOADERS
// ============================================================================

/**
 * Load HOD dashboard overview
 */
async function loadHodDashboard() {
  const sectionId = 'overview-section';
  setLoading(sectionId);

  const result = await apiCall('/hod/dashboard');
  
  if (result.success) {
    const stats = [
      { key: 'studentCount', icon: '👨‍🎓', title: 'Total Students' },
      { key: 'teacherCount', icon: '👨‍🏫', title: 'Total Teachers' },
      { key: 'subjectCount', icon: '📚', title: 'Total Subjects' },
      { key: 'avgAttendance', icon: '📊', title: 'Avg Attendance' }
    ];

    const section = document.querySelector(`#${sectionId}`);
    if (section) {
      section.innerHTML = '<div class="stats-grid">' + stats.map(stat => `
        <div class="stat-card">
          <div class="stat-icon">${stat.icon}</div>
          <h3>${stat.title}</h3>
          <p class="stat-number">${result[stat.key] || 0}${stat.key === 'avgAttendance' ? '%' : ''}</p>
        </div>
      `).join('') + '</div>';
    }
  } else {
    showError(sectionId, result.message);
  }
}

// HOD LOADERS
async function loadHodTeachers() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/teachers', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#teachers-section tbody');
    if (table) {
      table.innerHTML = ((data.teachers || [])).map(t => {
        const name = `${t.first_name || ''} ${t.last_name || ''}`.trim();
        return `<tr><td>${name}</td><td>${t.email}</td><td>${t.status}</td></tr>`;
      }).join('');
    }
  } catch (e) {
    console.error('loadHodTeachers error:', e);
  }
}

async function loadHodStudents() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/students', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#students-section tbody');
    if (table) {
      table.innerHTML = ((data.students || [])).map(s => {
        const name = `${s.first_name || ''} ${s.last_name || ''}`.trim();
        return `<tr><td>${name}</td><td>${s.enrollment_number}</td><td>${s.program}</td></tr>`;
      }).join('');
    }
  } catch (e) {
    console.error('loadHodStudents error:', e);
  }
}

async function loadHodAttendanceStats() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/attendance-stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#attendance-section tbody');
    if (table) {
      table.innerHTML = ((data.statistics || [])).map(s => `<tr><td>${s.name}</td><td>${(s.attendance_percent || 0).toFixed(1)}%</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadHodAttendanceStats error:', e);
  }
}

async function loadHodPerformanceStats() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch('http://localhost:5000/api/hod/performance-stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#performance-section tbody');
    if (table) {
      table.innerHTML = ((data.statistics || [])).map(s => `<tr><td>${s.name}</td><td>${(s.avg_marks || 0).toFixed(1)}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadHodPerformanceStats error:', e);
  }
}

// ============================================================================
// TEACHER DASHBOARD LOADERS
// ============================================================================

/**
 * Load teacher dashboard overview
 */
async function loadTeacherDashboard() {
  const sectionId = 'overview-section';
  setLoading(sectionId);

  const teacherId = localStorage.getItem('userId');
  const result = await apiCall(`/teacher/${teacherId}/dashboard`);
  
  if (result.success) {
    const stats = [
      { key: 'subjectCount', icon: '📚', title: 'My Subjects' },
      { key: 'totalStudents', icon: '👨‍🎓', title: 'Total Students' },
      { key: 'avgAttendance', icon: '📊', title: 'Avg Attendance' },
      { key: 'pendingUploads', icon: '📋', title: 'Pending Uploads' }
    ];

    const statsContainer = document.getElementById('teacher-overview-stats');
    const gridContainer = document.getElementById('teacher-overview-grid');
    
    if (statsContainer) {
      statsContainer.innerHTML = stats.map(stat => `
        <div class="stat-card">
          <div class="stat-icon">${stat.icon}</div>
          <h3>${stat.title}</h3>
          <p class="stat-number">${result[stat.key] || 0}${stat.key === 'avgAttendance' ? '%' : ''}</p>
        </div>
      `).join('');
    }
    
    if (gridContainer) {
      gridContainer.innerHTML = `
        <div class="card">
          <h3>Quick Actions</h3>
          <a href="#" onclick="switchSection('attendance')" class="btn btn-small" style="display: block; margin: 5px 0;">Take Attendance</a>
          <a href="#" onclick="switchSection('marks')" class="btn btn-small" style="display: block; margin: 5px 0;">Upload Marks</a>
          <a href="#" onclick="switchSection('notices')" class="btn btn-small" style="display: block; margin: 5px 0;">Post Notice</a>
        </div>
        <div class="card">
          <h3>Today's Timetable</h3>
          <p>${result.timetable ? result.timetable.map(t => `${t.time} - ${t.subject} (${t.students} students)`).join('<br>') : 'No classes today'}</p>
        </div>
        <div class="card">
          <h3>Recent Activity</h3>
          <p>${result.recentActivity ? result.recentActivity.map(a => a).join('<br>') : 'No recent activity'}</p>
        </div>
      `;
    }
  } else {
    showError(sectionId, result.message);
  }
}

// TEACHER LOADERS
async function loadTeacherSubjects() {
  const sectionId = 'subjects-section';
  setLoading(sectionId);

  try {
    const result = await apiCall('/teacher/subjects');
    if (result.success) {
      const tbody = document.getElementById('teacher-subjects-tbody');
      if (tbody) {
        tbody.innerHTML = (result.subjects || []).map(s => `
          <tr>
            <td>${s.subject_code || s.code}</td>
            <td>${s.subject_name || s.name}</td>
            <td>${s.semester || 'N/A'}</td>
            <td>${s.student_count || s.students || 0}</td>
            <td><button class="btn btn-small" onclick="manageSubject('${s.subject_code || s.code}')">Manage</button></td>
          </tr>
        `).join('');
      }
    } else {
      showError(sectionId, result.message);
    }
  } catch (e) {
    console.error('loadTeacherSubjects error:', e);
    showError(sectionId, 'Failed to load subjects');
  }
}

async function loadTeacherStudents() {
  const sectionId = 'students-section';
  setLoading(sectionId);

  try {
    const result = await apiCall('/teacher/students');
    if (result.success) {
      // Populate subject filter
      const subjectFilter = document.getElementById('subject-filter');
      if (subjectFilter && result.subjects) {
        subjectFilter.innerHTML = '<option>All Subjects</option>' + 
          result.subjects.map(s => `<option value="${s.code}">${s.code} - ${s.name}</option>`).join('');
      }

      // Populate students table
      const tbody = document.getElementById('teacher-students-tbody');
      if (tbody) {
        tbody.innerHTML = (result.students || []).map(s => `
          <tr>
            <td>${s.name}</td>
            <td>${s.roll_number || s.roll_no}</td>
            <td>${s.email}</td>
            <td><span class="badge badge-success">Active</span></td>
            <td><button class="btn btn-small" onclick="viewStudentDetails('${s.id}')">View Details</button></td>
          </tr>
        `).join('');
      }
    } else {
      showError(sectionId, result.message);
    }
  } catch (e) {
    console.error('loadTeacherStudents error:', e);
    showError(sectionId, 'Failed to load students');
  }
}

// ============================================================================
// STUDENT DASHBOARD LOADERS
// ============================================================================

/**
 * Load student overview
 */
async function loadStudentOverview() {
  const sectionId = 'overview-section';
  setLoading(sectionId);

  const studentId = localStorage.getItem('userId');
  const result = await apiCall(`/student/${studentId}/academic`);
  
  if (result.success) {
    const stats = [
      { key: 'cgpa', icon: '📊', title: 'Current GPA' },
      { key: 'attendance', icon: '📋', title: 'Attendance' },
      { key: 'subjectCount', icon: '📚', title: 'Enrolled Subjects' },
      { key: 'assignmentProgress', icon: '📤', title: 'Assignments' }
    ];

    const statsContainer = document.getElementById('student-overview-stats');
    const gridContainer = document.getElementById('student-overview-grid');
    
    if (statsContainer) {
      statsContainer.innerHTML = stats.map(stat => `
        <div class="stat-card">
          <div class="stat-icon">${stat.icon}</div>
          <h3>${stat.title}</h3>
          <p class="stat-number">${result[stat.key] || 0}${stat.key === 'attendance' || stat.key === 'assignmentProgress' ? '%' : ''}</p>
        </div>
      `).join('');
    }
    
    if (gridContainer) {
      gridContainer.innerHTML = `
        <div class="card">
          <h3>Quick Links</h3>
          <a href="#" onclick="switchSection('marks')" class="btn btn-small" style="display: block; margin: 5px 0;">View Marks</a>
          <a href="#" onclick="switchSection('assignments')" class="btn btn-small" style="display: block; margin: 5px 0;">Submit Assignment</a>
          <a href="#" onclick="switchSection('notices')" class="btn btn-small" style="display: block; margin: 5px 0;">View Notices</a>
        </div>
        <div class="card">
          <h3>Academic Status</h3>
          <p>📊 Semester: ${result.semester || 'N/A'}</p>
          <p>✓ ${result.standing || 'Good Standing'}</p>
          <p>🎓 ${result.backlogs || 'No Backlogs'}</p>
        </div>
        <div class="card">
          <h3>Recent Marks</h3>
          ${result.recentMarks ? result.recentMarks.map(m => `<p>${m.subject}: ${m.marks}</p>`).join('') : '<p>No recent marks</p>'}
        </div>
      `;
    }
  } else {
    showError(sectionId, result.message);
  }
}

// STUDENT LOADERS
async function loadStudentProfile() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/academic`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.student) {
      const info = document.querySelector('#profile-section .profile-info');
      if (info) {
        const name = `${data.student.first_name || ''} ${data.student.last_name || ''}`.trim();
        info.innerHTML = `
          <p><strong>Name:</strong> ${name}</p>
          <p><strong>Enrollment:</strong> ${data.student.enrollment_number}</p>
          <p><strong>Program:</strong> ${data.student.program}</p>
          <p><strong>CGPA:</strong> ${(data.cgpa || 0).toFixed(2)}</p>
        `;
      }
    }
  } catch (e) {
    console.error('loadStudentProfile error:', e);
  }
}

async function loadStudentAttendance() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/attendance`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#attendance-section tbody');
    if (table) {
      table.innerHTML = ((data.attendance || [])).map(a => `<tr><td>Subject ${a.subject_id}</td><td>${(a.percentage || 0).toFixed(1)}%</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentAttendance error:', e);
  }
}

async function loadStudentMarks() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/marks`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#marks-section tbody');
    if (table) {
      table.innerHTML = ((data.marks || [])).map(m => `<tr><td>Subject ${m.subject_id}</td><td>${m.total || 'N/A'}</td><td>${m.grade || 'N/A'}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentMarks error:', e);
  }
}

async function loadStudentSubjects() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/subjects`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#subjects-section tbody');
    if (table) {
      table.innerHTML = ((data.subjects || [])).map(s => `<tr><td>${s.subject_code}</td><td>${s.subject_name}</td><td>${s.credits}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentSubjects error:', e);
  }
}

async function loadStudentAssignments() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/assignments`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#assignments-section tbody');
    if (table) {
      table.innerHTML = ((data.assignments || [])).map(a => `<tr><td>${a.title}</td><td>${a.subject_name}</td><td>${formatDate(a.due_date)}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentAssignments error:', e);
  }
}

async function loadStudentExamSchedule() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/exam-schedule`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#exam-schedule-section tbody');
    if (table) {
      table.innerHTML = ((data.exams || [])).map(e => `<tr><td>${e.subject_name}</td><td>${e.exam_type}</td><td>${formatDate(e.exam_date)}</td><td>${e.location}</td></tr>`).join('');
    }
  } catch (e) {
    console.error('loadStudentExamSchedule error:', e);
  }
}

async function loadStudentNotices() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/notices`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const div = document.querySelector('#notices-section');
    if (div) {
      div.innerHTML = ((data.notices || [])).map(n => `<div class="notice"><h4>${n.title}</h4><p>${n.content}</p><small>${formatDate(n.posted_date)}</small></div>`).join('');
    }
  } catch (e) {
    console.error('loadStudentNotices error:', e);
  }
}

async function loadStudentAIPrediction() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const res = await fetch(`http://localhost:5000/api/student/${userId}/ai-prediction`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const card = document.querySelector('#ai-prediction-section .card');
    if (card) {
      card.innerHTML = `<h3>AI Predictions</h3><p>Risk: ${data.dropout_risk}</p><p>Suggestion: ${data.recommendation}</p>`;
    }
  } catch (e) {
    console.error('loadStudentAIPrediction error:', e);
  }
}

// ============================================================================
// GLOBAL LOADER DISPATCHER
// ============================================================================

function loadSectionData(section) {
  const role = localStorage.getItem('userRole');
  if (role === 'admin') {
    if (section === 'overview') loadAdminOverview();
    else if (section === 'approvals') loadAdminApprovals();
    else if (section === 'users') loadAdminUsers();
    else if (section === 'departments') loadAdminDepartments();
    else if (section === 'subjects') loadAdminSubjects();
    else if (section === 'analytics') loadAdminAnalytics();
    else if (section === 'ai-insights') loadAdminAIInsights();
  } else if (role === 'hod') {
    if (section === 'overview') loadHodDashboard();
    else if (section === 'teachers') loadHodTeachers();
    else if (section === 'students') loadHodStudents();
    else if (section === 'attendance') loadHodAttendanceStats();
    else if (section === 'performance') loadHodPerformanceStats();
  } else if (role === 'teacher') {
    if (section === 'overview') loadTeacherDashboard();
    else if (section === 'subjects') loadTeacherSubjects();
    else if (section === 'students') loadTeacherStudents();
  } else if (role === 'student') {
    if (section === 'overview') loadStudentOverview();
    else if (section === 'profile') loadStudentProfile();
    else if (section === 'attendance') loadStudentAttendance();
    else if (section === 'marks') loadStudentMarks();
    else if (section === 'subjects') loadStudentSubjects();
    else if (section === 'assignments') loadStudentAssignments();
    else if (section === 'exam-schedule') loadStudentExamSchedule();
    else if (section === 'notices') loadStudentNotices();
    else if (section === 'ai-prediction') loadStudentAIPrediction();
  }
}

// ============================================================================
// AUTO-INITIALIZATION
// ============================================================================

/**
 * Setup global event delegation for section loading
 */
function setupDashboardSectionLoaders() {
  document.addEventListener('click', (e) => {
    const menuItem = e.target.closest('.menu-item');
    if (menuItem) {
      e.preventDefault();
      const section = menuItem.dataset.section;
      
      // Remove active class from all menu items
      document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
      });
      
      // Add active class to clicked item
      menuItem.classList.add('active');
      
      // Load the section
      loadSectionData(section);
      
      // Update section title if exists
      const sectionTitle = document.querySelector('#sectionTitle');
      if (sectionTitle) {
        sectionTitle.textContent = menuItem.textContent.trim();
      }
    }
  });
}

// Auto-initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupDashboardSectionLoaders);
} else {
  setupDashboardSectionLoaders();
}
