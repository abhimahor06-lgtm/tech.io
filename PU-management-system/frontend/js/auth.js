/**
 * AUTH.JS - Authentication and Registration Logic
 * Poornima University Management System
 */

// Use the configured API base URL when available, but fall back to a global API_BASE_URL
// variable if the config file is not loaded (e.g., opened directly from file://).
const BASE_API_URL = (typeof APP_CONFIG !== 'undefined' && APP_CONFIG.API_BASE_URL)
  ? APP_CONFIG.API_BASE_URL
  : (typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : '');

/**
 * Handle login form submission
 */
async function handleLogin(role, form) {
  removeErrorMessage();
  const formData = new FormData(form);
  // backend expects email field for login; allow user to enter username or email
  const identifier = (formData.get('username') || formData.get('email') || '').toString().trim();
  const password = (formData.get('password') || '').toString().trim();

  // Debugging: log what we are sending to the backend
  console.debug('Login attempt', { role, identifier, password: password ? '***' : '' });

  const data = {
    email: identifier,
    password,
    role: role
  };

  try {
    const response = await fetch(`${BASE_API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok && result.success) {
      // Save token and user details
      localStorage.setItem('token', result.token);
      // response includes user details under `user` key
      if (result.user) {
        localStorage.setItem('userId', result.user.id);
        localStorage.setItem('userRole', result.user.role);
        localStorage.setItem('userName', result.user.username);
      }

      // Check if user is approved (can be overridden in config for demo/dev)
      // If config isn't loaded, default to allowing pending logins.
      if (!(APP_CONFIG?.ALLOW_PENDING_LOGIN ?? true) && result.status !== 'approved') {
        showErrorMessage('Your account is pending approval. Please contact admin.');
        return;
      }

      showNotification('Login successful! Redirecting...', 'success');

      // Redirect to appropriate dashboard
      setTimeout(() => {
        const dashboardUrls = {
          'admin': '../dashboard/adminDashboard.html',
          'hod': '../dashboard/hodDashboard.html',
          'teacher': '../dashboard/teacherDashboard.html',
          'student': '../dashboard/studentDashboard.html'
        };
        window.location.href = dashboardUrls[role] || '../index.html';
      }, 1000);
    } else {
      showErrorMessage(result.message || 'Login failed. Please check your credentials.');
    }
  } catch (error) {
    console.error('Login error:', error);
    showErrorMessage('Login failed. Server error.');
  }
}

/**
 * Handle registration form submission
 */
async function handleRegistration(role, form) {
  removeErrorMessage();
  
  // Validate form
  if (!form.checkValidity()) {
    showErrorMessage('Please fill all required fields correctly.');
    return;
  }

  const formData = new FormData(form);
  const data = {
    role: role,
    username: formData.get('username'),
    password: formData.get('password'),
    confirmPassword: formData.get('confirmPassword'),
    status: 'pending' // All registrations start as pending
  };

  // Validate password match
  if (data.password !== data.confirmPassword) {
    showErrorMessage('Passwords do not match.');
    return;
  }

  // Validate password strength
  const passwordCheck = validatePasswordStrength(data.password);
  if (!passwordCheck.isStrong) {
    showErrorMessage('Password must be at least 8 characters with uppercase, lowercase, numbers, and symbols.');
    return;
  }

  // Add role-specific fields
  if (role === 'admin') {
    data.adminId = formData.get('adminId');
    data.firstName = formData.get('firstName');
    data.lastName = formData.get('lastName');
    data.email = formData.get('officialEmail'); // Map officialEmail to email
    data.officialEmail = formData.get('officialEmail');
    data.accessLevel = formData.get('accessLevel');
    data.phone = formData.get('phone');
    data.securityPin = formData.get('securityPin');
    data.status = 'approved'; // First admin auto-approved
  } else if (role === 'hod' || role === 'teacher') {
    data.firstName = formData.get('firstName');
    data.lastName = formData.get('lastName');
    data.email = formData.get('email');
    data.phone = formData.get('phone');
    data.employeeId = formData.get('employeeId');
    data.department = formData.get('department');
    data.qualification = formData.get('qualification');
    data.specialization = formData.get('specialization');
    if (role === 'teacher') {
      data.experience = formData.get('experience') || 0;
    }
  } else if (role === 'student') {
    data.firstName = formData.get('firstName');
    data.lastName = formData.get('lastName');
    data.email = formData.get('email');
    data.phone = formData.get('phone');
    data.dob = formData.get('dob');
    data.gender = formData.get('gender');
    data.enrollmentNumber = formData.get('enrollmentNumber');
    data.program = formData.get('program');
    data.department = formData.get('department');
    data.semester = formData.get('semester');
  }

  try {
    const response = await fetch(`${BASE_API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok && result.success) {
      showNotification(`Registration successful! Your account is ${data.status === 'approved' ? 'active' : 'pending admin approval'}.`, 'success');

      setTimeout(() => {
        const loginUrls = {
          'admin': '../login/adminLogin.html',
          'hod': '../login/hodLogin.html',
          'teacher': '../login/teacherLogin.html',
          'student': '../login/studentLogin.html'
        };
        window.location.href = loginUrls[role] || '../login/role-selection.html';
      }, 2000);
    } else {
      showErrorMessage(result.message || 'Registration failed. Please try again.');
    }
  } catch (error) {
    console.error('Registration error:', error);
    showErrorMessage('Registration failed. Server error.');
  }
}

/**
 * Show error message on form
 */
function showErrorMessage(message) {
  const errorDiv = document.getElementById('errorMessage');
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } else {
    showNotification(message, 'error');
  }
}

/**
 * Remove error message
 */
function removeErrorMessage() {
  const errorDiv = document.getElementById('errorMessage');
  if (errorDiv) {
    errorDiv.style.display = 'none';
    errorDiv.textContent = '';
  }
}

/**
 * Check password match on keyup
 */
function checkPasswordMatch(password1Id, password2Id, messageDivId) {
  const password1 = document.getElementById(password1Id);
  const password2 = document.getElementById(password2Id);
  const messageDiv = document.getElementById(messageDivId);

  if (!password1 || !password2 || !messageDiv) return;

  if (password1.value === password2.value && password1.value) {
    messageDiv.textContent = '✓ Passwords match';
    messageDiv.style.color = '#10b981';
  } else if (password1.value !== password2.value && password2.value) {
    messageDiv.textContent = '✗ Passwords do not match';
    messageDiv.style.color = '#ef4444';
  } else {
    messageDiv.textContent = '';
  }
}

/**
 * Validate username availability
 */
async function checkUsernameAvailability(username) {
  if (username.length < 3) return false;

  try {
    const response = await fetch(`${BASE_API_URL}/auth/check-username`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username })
    });

    const result = await response.json();
    return result.available;
  } catch (error) {
    console.error('Error checking username:', error);
    return false;
  }
}

/**
 * Validate email availability
 */
async function checkEmailAvailability(email) {
  if (!isValidEmail(email)) return false;

  try {
    const response = await fetch(`${BASE_API_URL}/auth/check-email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });

    const result = await response.json();
    return result.available;
  } catch (error) {
    console.error('Error checking email:', error);
    return false;
  }
}

/**
 * Logout user
 */
function logoutUser() {
  localStorage.removeItem('token');
  localStorage.removeItem('userId');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userName');
  
  showNotification('Logged out successfully', 'success');
  setTimeout(() => {
    window.location.href = '../index.html';
  }, 1000);
}

/**
 * Validate file upload
 */
function validateFileUpload(file, maxSizeMB = 5, allowedFormats = ['pdf', 'jpg', 'jpeg', 'png']) {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  
  if (file.size > maxSizeBytes) {
    return {
      valid: false,
      error: `File size exceeds ${maxSizeMB}MB limit`
    };
  }

  const extension = file.name.split('.').pop().toLowerCase();
  if (!allowedFormats.includes(extension)) {
    return {
      valid: false,
      error: `File type not allowed. Allowed formats: ${allowedFormats.join(', ')}`
    };
  }

  return { valid: true };
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Add password confirmation check listeners on page load
document.addEventListener('DOMContentLoaded', () => {
  const confirmPassword = document.getElementById('confirmPassword');
  if (confirmPassword) {
    confirmPassword.addEventListener('keyup', () => {
      const passwordInputs = document.querySelectorAll('input[type="password"][name="password"]');
      if (passwordInputs.length > 0) {
        const passwordId = passwordInputs[0].id;
        checkPasswordMatch(passwordId, 'confirmPassword', 'passwordMatch');
      }
    });
  }
});
