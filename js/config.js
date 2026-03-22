/**
 * CONFIG.JS - Application Configuration
 * Poornima University Management System
 */

// Use a fixed API base URL for frontend requests.
// This ensures the frontend always talks to the backend on localhost:5000.
const API_BASE = 'http://localhost:5000/api';

// Explicitly force API endpoint for file:// and local testing.
const API_BASE_URL = API_BASE;

if (window.location.protocol === 'file:' || window.location.origin === 'null') {
  console.warn('Running from file:// (or null origin). API requests will be routed to ' + API_BASE_URL);
}

const APP_CONFIG = {
  API_BASE_URL,
  // When true, users can login even if their account status is still "pending" (dev/demo convenience).
  // Set to false to enforce admin approval for non-admin roles.
  ALLOW_PENDING_LOGIN: true,
};