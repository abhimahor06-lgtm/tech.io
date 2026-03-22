/**
 * DASHBOARD.JS - Dashboard Functionality
 * Poornima University Management System
 */

/**
 * Initialize dashboard on load
 */
document.addEventListener('DOMContentLoaded', () => {
  initializeDashboard();
});

/**
 * Initialize dashboard
 */
function initializeDashboard() {
  // Check authentication
  const token = localStorage.getItem('token');
  if (!token) {
    showNotification('Please login first', 'error');
    window.location.href = '../login/role-selection.html';
    return;
  }

  // Load user data
  loadUserData();

  // Setup event listeners
  setupDashboardListeners();

  // Load initial overview data
  const userRole = localStorage.getItem('userRole');
  if (userRole) {
    // Load overview section by default
    setTimeout(() => {
      if (typeof loadSectionData === 'function') {
        loadSectionData('overview');
      }
    }, 100);
  }
}

/**
 * Load user data into dashboard
 */
async function loadUserData() {
  try {
    const userId = localStorage.getItem('userId');
    const token = localStorage.getItem('token');
    const userRole = localStorage.getItem('userRole');
    const userName = localStorage.getItem('userName');

    // For admins, skip fetching profile (no endpoint exists yet)
    if (userRole === 'admin') {
      if (userName) {
        renderUserProfile({ name: userName });
      }
      return;
    }

    // For other roles, fetch user data from their endpoint
    const response = await fetch(`${API_BASE_URL}/${userRole}/${userId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const userData = await response.json();
      localStorage.setItem('userName', userData.name);
      renderUserProfile(userData);
    } else if (response.status === 401) {
      logoutUser();
    }
  } catch (error) {
    console.error('Error loading user data:', error);
  }
}

/**
 * Update user profile display
 */
function renderUserProfile(userData) {
  const userNameElement = document.querySelector('.user-name');
  if (userNameElement) {
    userNameElement.textContent = userData.name || 'User';
  }
}

/**
 * Setup dashboard event listeners
 */
function setupDashboardListeners() {
  // Logout button
  const logoutButtons = document.querySelectorAll('[data-action="logout"]');
  logoutButtons.forEach(btn => {
    btn.addEventListener('click', logoutUser);
  });

  // Menu items
  const menuItems = document.querySelectorAll('.menu-item');
  menuItems.forEach(item => {
    item.addEventListener('click', handleMenuClick);
  });

  // Profile menu
  const userProfile = document.querySelector('.user-profile');
  if (userProfile) {
    userProfile.addEventListener('click', toggleProfileMenu);
  }

  // Settings save buttons
  const saveBtns = document.querySelectorAll('[data-action="save-settings"]');
  saveBtns.forEach(btn => {
    btn.addEventListener('click', saveSettings);
  });
}

/**
 * Handle menu item clicks
 */
function handleMenuClick(e) {
  e.preventDefault();
  // Navigation is handled in the HTML with data attributes
}

/**
 * Load dashboard data based on role
 */
async function loadDashboardData() {
  const userRole = localStorage.getItem('userRole');

  try {
    if (userRole === 'admin') {
      loadAdminData();
    } else if (userRole === 'hod') {
      loadHodData();
    } else if (userRole === 'teacher') {
      loadTeacherData();
    } else if (userRole === 'student') {
      loadStudentData();
    }
  } catch (error) {
    console.error('Error loading dashboard data:', error);
  }
}

/**
 * Load admin dashboard data
 */
async function loadAdminData() {
  try {
    const token = localStorage.getItem('token');

    // Fetch combined dashboard data
    const dashResponse = await fetch(`${API_BASE_URL}/admin/dashboard`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (dashResponse.ok) {
      const data = await dashResponse.json();
      updateAdminStats(data);
      if (data.pendingApprovals !== undefined) {
        const approvalsArray = data.recentApprovals || [];
        displayPendingApprovals(approvalsArray);
      }
    }
  } catch (error) {
    console.error('Error loading admin data:', error);
  }
}

/**
 * Update admin statistics
 */
function updateAdminStats(stats) {
  const statCards = document.querySelectorAll('.stat-card');
  
  if (stats.totalStudents && statCards[0]) {
    statCards[0].querySelector('.stat-number').textContent = stats.totalStudents;
  }
  if (stats.totalTeachers && statCards[1]) {
    statCards[1].querySelector('.stat-number').textContent = stats.totalTeachers;
  }
  if (stats.totalHods && statCards[2]) {
    statCards[2].querySelector('.stat-number').textContent = stats.totalHods;
  }
  if (stats.totalDepartments && statCards[3]) {
    statCards[3].querySelector('.stat-number').textContent = stats.totalDepartments;
  }
}

/**
 * Display pending approvals
 */
function displayPendingApprovals(approvals) {
  const approvalsTable = document.querySelector('#approvals-section tbody');
  if (!approvalsTable) return;

  approvalsTable.innerHTML = '';

  approvals.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.name}</td>
      <td>${item.role}</td>
      <td>${item.email}</td>
      <td>${formatDate(item.appliedDate)}</td>
      <td class="action-buttons">
        <button class="btn btn-small btn-success" onclick="approveUser('${item.id}')">✓ Approve</button>
        <button class="btn btn-small btn-danger" onclick="rejectUser('${item.id}')">✗ Reject</button>
      </td>
    `;
    approvalsTable.appendChild(row);
  });
}


// ----------------- ADMIN SECTION HELPERS -----------------

async function loadAdminUsers(filterRole = null) {
  try {
    const token = localStorage.getItem('token');
    let endpoint = '/admin/users';
    if (filterRole) endpoint += `?role=${filterRole}`;
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    updateAdminUsers(data.users || []);
  } catch (e) {
    console.error('Error loading users:', e);
  }
}

function updateAdminUsers(users) {
  const table = document.querySelector('#users-section tbody');
  if (!table) return;
  table.innerHTML = '';
  users.forEach(u => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${u.username || ''}</td>
      <td>${u.role}</td>
      <td>${u.email}</td>
      <td>${u.status}</td>
      <td><button class="btn btn-small" onclick="deleteUser(${u.id})">Delete</button></td>
    `;
    table.appendChild(tr);
  });
}

async function loadAdminDepartments() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/admin/departments`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#departments-section tbody');
    if (!table) return;
    table.innerHTML = '';
    (data.departments || []).forEach(d => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${d.name}</td>
        <td>${d.hod || ''}</td>
        <td>${d.studentCount || ''}</td>
        <td>${d.teacherCount || ''}</td>
        <td><button class="btn btn-small">Edit</button></td>
      `;
      table.appendChild(tr);
    });
  } catch (e) {
    console.error('Error loading departments:', e);
  }
}

async function loadAdminSubjects() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/admin/subjects`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const table = document.querySelector('#subjects-section tbody');
    if (!table) return;
    table.innerHTML = '';
    (data.subjects || []).forEach(s => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${s.subject_code}</td>
        <td>${s.subject_name}</td>
        <td>${s.department}</td>
        <td>${s.teacher_id || ''}</td>
        <td><button class="btn btn-small">Edit</button></td>
      `;
      table.appendChild(tr);
    });
  } catch (e) {
    console.error('Error loading subjects:', e);
  }
}

async function loadAdminAnalytics() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/admin/analytics`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const stats = await res.json();
    const items = document.querySelectorAll('#analytics-section .analytics-item .highlight');
    if (items[0]) items[0].textContent = stats.avgAttendance + '%';
    if (items[1]) items[1].textContent = stats.avgGPA;
    if (items[2]) items[2].textContent = stats.dropoutRate + '%';
  } catch (e) {
    console.error('Error loading analytics:', e);
  }
}

async function loadAdminAIInsights() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/admin/ai-insights`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const card = document.querySelector('#ai-insights-section .card');
    if (!card) return;
    card.innerHTML = `
      <h3>AI-Powered Insights</h3>
      <p>🤖 <strong>At-Risk Students:</strong> System has identified ${data.atRisk} students at risk of dropout</p>
      <p>📈 <strong>Top Performers:</strong> ${data.topPerformers} students with high marks</p>
      <p>⚠️ <strong>Low Attendance:</strong> ${data.lowAttendance} students with attendance under 75%</p>
    `;
  } catch (e) {
    console.error('Error loading AI insights:', e);
  }
}

async function loadServerLogs() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/admin/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const viewer = document.querySelector('#logs-section .log-viewer');
    if (!viewer) return;
    viewer.innerHTML = '';
    (data.logs || []).forEach(line => {
      const p = document.createElement('p');
      p.textContent = line;
      viewer.appendChild(p);
    });
  } catch (e) {
    console.error('Error loading logs:', e);
  }
}

// simple backup info stub
async function loadBackupInfo() {
  const section = document.getElementById('backup-section');
  if (!section) return;
  // this example keeps static text; could call backend if implemented
}


/**
 * Approve user registration
 */
async function approveUser(roleOrUserId, maybeUserId) {
  // adminDashboard provides (role, id), old code path provides just userId (legacy/misuse)
  let role, userId;
  if (maybeUserId !== undefined) {
    role = roleOrUserId;
    userId = maybeUserId;
  } else {
    role = 'student'; // default if no role provided (legacy behavior)
    userId = roleOrUserId;
  }

  if (!role || !userId) {
    console.error('approveUser: missing role or userId', role, userId);
    showNotification('Invalid approval operation', 'error');
    return;
  }

  if (!confirm('Are you sure you want to approve this user?')) return;

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/admin/approve-user/${role}/${userId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      showNotification('User approved successfully', 'success');
      loadDashboardData();
    } else {
      showNotification('Failed to approve user', 'error');
    }
  } catch (error) {
    console.error('Error approving user:', error);
    showNotification('Error approving user', 'error');
  }
}

/**
 * Reject user registration
 */
async function rejectUser(roleOrUserId, maybeUserId) {
  let role, userId;
  if (maybeUserId !== undefined) {
    role = roleOrUserId;
    userId = maybeUserId;
  } else {
    role = 'student';
    userId = roleOrUserId;
  }

  if (!role || !userId) {
    console.error('rejectUser: missing role or userId', role, userId);
    showNotification('Invalid rejection operation', 'error');
    return;
  }

  if (!confirm('Are you sure you want to reject this user?')) return;

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/admin/reject-user/${role}/${userId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      showNotification('User rejected', 'success');
      loadDashboardData();
    } else {
      showNotification('Failed to reject user', 'error');
    }
  } catch (error) {
    console.error('Error rejecting user:', error);
    showNotification('Error rejecting user', 'error');
  }
}

/**
 * Load HOD dashboard data
 */
async function loadHodData() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');

    // Load department data (includes avg attendance now)
    const deptResponse = await fetch(`${API_BASE_URL}/hod/${userId}/department`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (deptResponse.ok) {
      const deptData = await deptResponse.json();
      updateHodStats(deptData);
    }
  } catch (error) {
    console.error('Error loading HOD data:', error);
  }
}

/**
 * Update HOD statistics
 */
function updateHodStats(deptData) {
  const statCards = document.querySelectorAll('.stat-card');
  
  if (deptData.teacherCount && statCards[0]) {
    statCards[0].querySelector('.stat-number').textContent = deptData.teacherCount;
  }
  if (deptData.studentCount && statCards[1]) {
    statCards[1].querySelector('.stat-number').textContent = deptData.studentCount;
  }
  if (deptData.subjectCount && statCards[2]) {
    statCards[2].querySelector('.stat-number').textContent = deptData.subjectCount;
  }
  if (deptData.avgAttendance && statCards[3]) {
    statCards[3].querySelector('.stat-number').textContent = deptData.avgAttendance.toFixed(1) + '%';
  }
}

/**
 * Load teacher dashboard data
 */
async function loadTeacherData() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');

    // Load dashboard summary for the teacher
    const dashResponse = await fetch(`${API_BASE_URL}/teacher/${userId}/dashboard`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (dashResponse.ok) {
      const teachingData = await dashResponse.json();
      updateTeacherStats(teachingData);
    }
  } catch (error) {
    console.error('Error loading teacher data:', error);
  }
}

/**
 * Update teacher statistics
 */
function updateTeacherStats(teachingData) {
  const statCards = document.querySelectorAll('.stat-card');
  
  if (teachingData.subjectCount && statCards[0]) {
    statCards[0].querySelector('.stat-number').textContent = teachingData.subjectCount;
  }
  if (teachingData.totalStudents && statCards[1]) {
    statCards[1].querySelector('.stat-number').textContent = teachingData.totalStudents;
  }
  if (teachingData.avgAttendance && statCards[2]) {
    statCards[2].querySelector('.stat-number').textContent = teachingData.avgAttendance.toFixed(1) + '%';
  }
  if (teachingData.pendingUploads && statCards[3]) {
    statCards[3].querySelector('.stat-number').textContent = teachingData.pendingUploads;
  }
}

/**
 * Load student dashboard data
 */
async function loadStudentData() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');

    // Load academic data (now computes real cgpa, attendance & progress)
    const academicResponse = await fetch(`${API_BASE_URL}/student/${userId}/academic`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (academicResponse.ok) {
      const academicData = await academicResponse.json();
      updateStudentStats(academicData);
    }
  } catch (error) {
    console.error('Error loading student data:', error);
  }
}

/**
 * Update student statistics
 */
function updateStudentStats(academicData) {
  const statCards = document.querySelectorAll('.stat-card');
  
  if (academicData.cgpa && statCards[0]) {
    statCards[0].querySelector('.stat-number').textContent = academicData.cgpa.toFixed(2);
  }
  if (academicData.attendance && statCards[1]) {
    statCards[1].querySelector('.stat-number').textContent = academicData.attendance.toFixed(1) + '%';
  }
  if (academicData.subjectCount && statCards[2]) {
    statCards[2].querySelector('.stat-number').textContent = academicData.subjectCount;
  }
  if (academicData.assignmentProgress && statCards[3]) {
    statCards[3].querySelector('.stat-number').textContent = academicData.assignmentProgress;
  }
}

/**
 * Save settings
 */
async function saveSettings() {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');

    // Get form data
    const settings = {
      emailNotifications: document.querySelector('input[name="emailNotifications"]')?.checked || false,
      apiAccess: document.querySelector('input[name="apiAccess"]')?.checked || false,
      maintenanceMode: document.querySelector('input[name="maintenanceMode"]')?.checked || false,
      // Add more settings as needed
    };

    const response = await fetch(`${API_BASE_URL}/settings/${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    });

    if (response.ok) {
      showNotification('Settings saved successfully', 'success');
    } else {
      showNotification('Failed to save settings', 'error');
    }
  } catch (error) {
    console.error('Error saving settings:', error);
    showNotification('Error saving settings', 'error');
  }
}

/**
 * Toggle profile dropdown menu
 */
function toggleProfileMenu(e) {
  e.stopPropagation();
  const profileMenu = this.querySelector('.profile-menu');
  if (profileMenu) {
    profileMenu.classList.toggle('show');
  }
}

/**
 * Close profile menu when clicking outside
 */
document.addEventListener('click', () => {
  const profileMenus = document.querySelectorAll('.profile-menu.show');
  profileMenus.forEach(menu => {
    menu.classList.remove('show');
  });
});

/**
 * Export data to CSV
 */
function exportToCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) {
    showNotification('Table not found', 'error');
    return;
  }

  let csv = [];
  const rows = table.querySelectorAll('tr');

  rows.forEach(row => {
    const cols = row.querySelectorAll('td, th');
    const rowData = Array.from(cols).map(col => col.textContent).join(',');
    csv.push(rowData);
  });

  downloadCSV(csv.join('\n'), filename);
}

/**
 * Download CSV file
 */
function downloadCSV(csv, filename) {
  const link = document.createElement('a');
  const blob = new Blob([csv], { type: 'text/csv' });
  link.href = window.URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}

/**
 * Print dashboard section
 */
function printSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (!section) {
    showNotification('Section not found', 'error');
    return;
  }

  const printWindow = window.open('', '', 'width=900,height=600');
  printWindow.document.write('<pre>' + section.innerHTML + '</pre>');
  printWindow.document.close();
  printWindow.print();
}
