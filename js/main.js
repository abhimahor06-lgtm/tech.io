/**
 * MAIN.JS - Home and General Frontend JavaScript
 * Poornima University Management System
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
  setupEventListeners();
  checkUserSession();
  console.log('Application initialized');
}

/**
 * Setup general event listeners
 */
function setupEventListeners() {
  // User profile dropdown
  const userProfile = document.querySelector('.user-profile');
  if (userProfile) {
    userProfile.addEventListener('click', toggleProfileMenu);
  }

  // Mobile menu toggle (if applicable)
  const navToggle = document.querySelector('.nav-toggle');
  if (navToggle) {
    navToggle.addEventListener('click', toggleMobileMenu);
  }

  // Smooth scroll for anchors
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href && href !== '#' && document.querySelector(href)) {
        e.preventDefault();
        document.querySelector(href).scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
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
  const profileMenu = document.querySelector('.profile-menu.show');
  if (profileMenu) {
    profileMenu.classList.remove('show');
  }
});

/**
 * Toggle mobile navigation menu
 */
function toggleMobileMenu() {
  const navMenu = document.querySelector('.nav-menu');
  if (navMenu) {
    navMenu.classList.toggle('show');
  }
}

/**
 * Check if user is logged in
 */
function checkUserSession() {
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('userRole');
  
  if (token && userRole) {
    console.log('User session found:', userRole);
  }
}

/**
 * Logout user
 */
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('userId');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userName');
  
  // Redirect to home
  window.location.href = '/';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background-color: ${getNotificationColor(type)};
    color: white;
    border-radius: 8px;
    z-index: 9999;
    animation: slideIn 0.3s ease-in;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

/**
 * Get notification color based on type
 */
function getNotificationColor(type) {
  const colors = {
    'success': '#10b981',
    'error': '#ef4444',
    'warning': '#f59e0b',
    'info': '#0ea5e9'
  };
  return colors[type] || colors['info'];
}

/**
 * Format date
 */
function formatDate(date) {
  return new Date(date).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

/**
 * Format time
 */
function formatTime(date) {
  return new Date(date).toLocaleTimeString('en-IN');
}

/**
 * Validate email
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 */
function validatePasswordStrength(password) {
  const requirements = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    numbers: /\d/.test(password),
    special: /[!@#$%^&*]/.test(password)
  };
  
  return {
    isStrong: Object.values(requirements).every(req => req),
    requirements
  };
}

// Add CSS animation for notifications
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
`;
document.head.appendChild(style);
