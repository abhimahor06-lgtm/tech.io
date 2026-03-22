// Attendance Flow Widget for Admin Dashboard
async function loadAttendanceFlow() {
  const wrap = document.getElementById('attendance-flow-widget');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading"><div class="spinner"></div>Loading…</div>';
  const today = new Date().toISOString().split('T')[0];
  const data = await api(`/attendance/date?date=${today}`);
  if (!data?.attendance?.length) { wrap.innerHTML = '<div class="empty">No attendance records for today</div>'; return; }
  const present = data.attendance.filter(a => a.status === 'present').length;
  const absent = data.attendance.filter(a => a.status === 'absent').length;
  const leave = data.attendance.filter(a => a.status === 'leave').length;
  wrap.innerHTML = `
    <div style="display:flex;gap:18px;justify-content:center;align-items:center;">
      <div><span class="badge badge-success">Present</span><br><span style="font-size:22px;font-weight:700;">${present}</span></div>
      <div><span class="badge badge-danger">Absent</span><br><span style="font-size:22px;font-weight:700;">${absent}</span></div>
      <div><span class="badge badge-warning">Leave</span><br><span style="font-size:22px;font-weight:700;">${leave}</span></div>
    </div>
  `;
}
