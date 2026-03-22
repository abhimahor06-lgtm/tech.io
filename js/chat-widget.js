/* chat-widget.js - embeddable AI support chat widget */
(function(){
  const serverOrigin = (location.origin && location.origin.startsWith('http'))
    ? location.origin
    : 'http://localhost:5000';

  // ensure chatbot stylesheet is present (every page may not have linked it)
  if (!document.getElementById('chatbot-css')) {
    const link = document.createElement('link');
    link.id = 'chatbot-css';
    link.rel = 'stylesheet';
    link.href = `${serverOrigin}/css/chatbot.css`;
    document.head.appendChild(link);
  }

  const markup = `
<!-- Floating Toggle Button -->
<button id="chat-toggle" title="Open Support Chat" aria-label="Toggle Chat">
  <!-- Chat icon -->
  <svg class="icon-chat" width="26" height="26" fill="none" viewBox="0 0 24 24">
    <path d="M20 2H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4l4 4 4-4h4a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
    <circle cx="8" cy="11" r="1.2" fill="white"/><circle cx="12" cy="11" r="1.2" fill="white"/><circle cx="16" cy="11" r="1.2" fill="white"/>
  </svg>
  <!-- Close icon -->
  <svg class="icon-close" width="22" height="22" fill="none" viewBox="0 0 24 24">
    <path d="M18 6L6 18M6 6l12 12" stroke="white" stroke-width="2.2" stroke-linecap="round"/>
  </svg>
</button>

<!-- Chat Window -->
<div id="chat-window">
  <!-- Header -->
  <div class="chat-header">
    <div class="bot-avatar">🤖</div>
    <div class="header-info">
      <div class="name">UMS AI Support</div>
      <div class="status">● Online — Instant Response</div>
    </div>
    <div class="header-actions">
      <button class="hbtn" id="clear-btn" title="Clear Chat">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
    </div>
  </div>

  <!-- Messages -->
  <div id="messages">
    <div class="chat-divider">Today</div>
    <div class="msg bot">
      <div class="msg-avatar">🤖</div>
      <div class="bubble">
        <span class="label">UMS SUPPORT</span><br/>
        👋 Hello there! I'm here to help you with the <strong>University Management System AI</strong>.<br/><br/>
        I can help with:<br/>
        • Registration &amp; Login issues<br/>
        • Admin approvals<br/>
        • Database errors<br/>
        • Course management<br/><br/>
        Ask About Your Issues! 🎓
      </div>
    </div>
  </div>

  <!-- Quick Replies -->
  <div class="quick-replies" id="quick-replies">
    <button class="qr">Login problem</button>
    <button class="qr">Registration failed</button>
    <button class="qr">Admin approval</button>
    <button class="qr">DB error</button>
    <button class="qr">Course not loading</button>
  </div>

  <!-- Input -->
  <div class="chat-input-area">
    <div class="input-row">
      <textarea id="user-input" rows="1" placeholder="Type your message here..."></textarea>
      <button id="send-btn" title="Send">
        <svg width="17" height="17" fill="none" viewBox="0 0 24 24">
          <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    <div class="input-footer">University Support System</div>
  </div>
</div>
`;

  document.body.insertAdjacentHTML('beforeend', markup);

  // after markup is added, initialize logic
  const SYSTEM_PROMPT = `You are an advanced AI technical support assistant for a University Management System (UMS) built with Python Flask and MySQL.

You operate with a 3-layer intelligence architecture:

LAYER 1 — DOCUMENTATION: You know Student Registration Workflow, Login/Authentication, Admin Approval System, Teacher Dashboard, Student Dashboard, Course Management, User Role Permissions, Database Schema, API Endpoints, Website Navigation, and FAQs.

LAYER 2 — ERROR LOG ANALYSIS: You diagnose Flask server errors, Python exceptions, Database errors, API errors, authentication failures, duplicate entry errors, permission errors, server timeout errors.

LAYER 3 — DATABASE VERIFICATION: You analyze issues with MySQL tables: users, students, teachers, courses, departments, attendance, grades.

RESPONSE FORMAT (always use this):
**Issue:** One sentence problem identification.
**Fix:**
• Step 1
• Step 2
• Step 3

RULES:
• Keep responses under 80 words unless detail is requested
• Be direct and solution-focused
• Use bullet points
• Never invent database data
• Prioritize speed and accuracy
• You can respond in Urdu/Roman Urdu if the user writes in that language`;

  // offline alert if loaded from file://
  if (location.protocol === 'file:') {
    alert('⚠️ Chatbot must be accessed via http://localhost:5000 or another web server.');
  }

  const toggle   = document.getElementById('chat-toggle');
  const chatWin  = document.getElementById('chat-window');
  const msgArea  = document.getElementById('messages');
  const inputEl  = document.getElementById('user-input');
  const sendBtn  = document.getElementById('send-btn');
  const clearBtn = document.getElementById('clear-btn');
  const qrDiv    = document.getElementById('quick-replies');

  let isOpen     = false;
  let history    = [];
  let unread     = 0;
  let badgeEl    = null;

  toggle.addEventListener('click', () => {
    isOpen = !isOpen;
    toggle.classList.toggle('open', isOpen);
    chatWin.classList.toggle('open', isOpen);
    if (isOpen) {
      removeBadge();
      inputEl.focus();
      scrollBottom();
    }
  });

  clearBtn.addEventListener('click', () => {
    history = [];
    msgArea.innerHTML = '<div class="chat-divider">Chat Cleared</div>';
    appendBot('Chat cleared! Koi naya sawaal poochein. 😊');
    showQuickReplies();
  });

  qrDiv.addEventListener('click', e => {
    if (e.target.classList.contains('qr')) {
      sendMessage(e.target.textContent);
    }
  });

  inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 90) + 'px';
  });
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
  sendBtn.addEventListener('click', send);

  function send() {
    const text = inputEl.value.trim();
    if (!text) return;
    sendMessage(text);
  }

  function sendMessage(text) {
    inputEl.value = '';
    inputEl.style.height = 'auto';
    hideQuickReplies();
    appendUser(text);
    history.push({ role: 'user', content: text });
    showTyping();
    callClaude();
  }

  async function callClaude() {
    if (!navigator.onLine) {
      removeTyping();
      appendBot('⚠️ You appear to be offline. Please check your internet connection.');
      return;
    }

    sendBtn.disabled = true;
    try {
      const headers = { 'Content-Type': 'application/json' };
      const token = localStorage.getItem('token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      // use absolute path so widget works from any route
      const resp = await fetch(`${serverOrigin}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ messages: history })
      });
      const data = await resp.json();
      removeTyping();
      if (data.content && data.content[0]) {
        const reply = data.content.map(b => b.text || '').join('');
        history.push({ role: 'assistant', content: reply });
        appendBot(reply);
        if (!isOpen) showBadge();
      } else {
        appendBot('⚠️ Response error. Please try again.');
      }
    } catch (err) {
      removeTyping();
      appendBot('⚠️ Unable to reach AI service. Ensure the backend is running and has network access.');
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  function appendUser(text) {
    const div = document.createElement('div');
    div.className = 'msg user';
    div.innerHTML = `
      <div class="msg-avatar">U</div>
      <div class="bubble">${escHtml(text)}</div>`;
    msgArea.appendChild(div);
    scrollBottom();
  }

  function appendBot(text) {
    const formatted = formatBot(text);
    const div = document.createElement('div');
    div.className = 'msg bot';
    div.innerHTML = `
      <div class="msg-avatar">🤖</div>
      <div class="bubble">${formatted}</div>`;
    msgArea.appendChild(div);
    scrollBottom();
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'msg bot'; div.id = 'typing-msg';
    div.innerHTML = `<div class="msg-avatar">🤖</div><div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
    msgArea.appendChild(div);
    scrollBottom();
  }
  function removeTyping() {
    const t = document.getElementById('typing-msg');
    if (t) t.remove();
  }

  function formatBot(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/^(Issue:|Fix:|Problem Analysis:|Possible Cause:|Recommended Solution:)/gm, '<span class="label">$1</span>')
      .replace(/^• (.*)/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, match => `<ul>${match}</ul>`)
      .replace(/\n/g, '<br/>');
  }

  function escHtml(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function scrollBottom() {
    setTimeout(() => { msgArea.scrollTop = msgArea.scrollHeight; }, 50);
  }

  window.addEventListener('offline', () => {
    appendBot('🔌 Connection lost — you are offline.');
  });
  window.addEventListener('online', () => {
    appendBot('✅ You are back online.');
  });

  function showBadge() {
    unread++;
    if (!badgeEl) {
      badgeEl = document.createElement('div');
      badgeEl.className = 'notif-badge';
      toggle.style.position = 'fixed';
      toggle.appendChild(badgeEl);
    }
    badgeEl.textContent = unread;
  }
  function removeBadge() {
    unread = 0;
    if (badgeEl) { badgeEl.remove(); badgeEl = null; }
  }
  function hideQuickReplies() { qrDiv.style.display = 'none'; }
  function showQuickReplies()  { qrDiv.style.display = 'flex'; }

})();
