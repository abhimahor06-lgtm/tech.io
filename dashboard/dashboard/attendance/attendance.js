// configuration
// API_BASE_URL is declared in api.js; ensure api.js is loaded before this file.
let students = [];

const table = document.getElementById("studentTable");

// helper to read token (null if missing)
function token() {
    const t = localStorage.getItem('token');
    if (!t || t === 'null' || t === 'undefined') return null;
    return t;
}

async function loadStudents() {
    if (!token()) {
        alert('Please login first');
        window.location.href = '../../login/role-selection.html';
        return;
    }
    table.innerHTML = '<tr><td colspan="4" class="loading"><div class="spinner"></div>Loading…</td></tr>';

    // use shared API client to ensure proper headers and logout handling
    try {
        const result = await listAttendanceStudents();
        if (result && result.success) {
            students = result.data.students.map(s => ({ ...s, status: 'Not Marked' }));
            renderTable();
            // if a date is selected (e.g. today prefilled), merge any existing attendance
            if (document.getElementById('date') && document.getElementById('date').value) {
                loadExistingForDate();
            }
        } else if (result) {
            alert(result.data.message || 'Failed to load students');
        }
    } catch (e) {
        console.error('Load students error', e);
        alert('Network error');
    }
}

function renderTable() {
    table.innerHTML = '';
    students.forEach((student, index) => {
        let row = `
<tr>
<td>${student.id}</td>
<td>${student.name}</td>
<td class="status">${student.status}</td>
<td>
<button class="present" onclick="mark(${index},'Present')">Present</button>
<button class="absent"  onclick="mark(${index},'Absent')">Absent</button>
</td>
</tr>`;
        table.innerHTML += row;
    });
    updateStats();
}

function mark(index,status){
    students[index].status = status;
}

// when first loaded
window.addEventListener('DOMContentLoaded', () => {
    // prefill date selector with today's date
    const dateEl = document.getElementById('date');
    if (dateEl) {
        const today = new Date().toISOString().split('T')[0];
        dateEl.value = today;
        // fetch any records for today if the table is already populated later
        dateEl.addEventListener('change', loadExistingForDate);
    }

    loadStudents();
    // realtime update via socket (optional)
    try {
        const base = API_BASE_URL.replace('/api','');
        const socket = io(base);
        socket.on('attendance_update', () => {
            loadStudents();
        });
    } catch (e) {
        // socket not available or not needed
        console.warn('socket init failed', e);
    }
});



// compute counters from the array
function updateStats(){
    let present = students.filter(s => s.status === "Present").length;
    let absent  = students.filter(s => s.status === "Absent").length;
    document.getElementById("total").innerText = students.length;
    document.getElementById("presentCount").innerText = present;
    document.getElementById("absentCount").innerText  = absent;
}

// when a date is selected, try to fetch and merge existing records
async function loadExistingForDate() {
    const date = document.getElementById('date').value;
    if (!date || students.length === 0) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/attendance/date?date=${date}`, {
            headers: { 'Authorization': 'Bearer ' + token() }
        });
        const data = await resp.json();
        if (data.success && data.attendance) {
            const map = {};
            data.attendance.forEach(a => {
                map[a.student_id] = a;
            });
            students.forEach(s => {
                if (map[s.id]) {
                    s.status = map[s.id].status.charAt(0).toUpperCase() + map[s.id].status.slice(1);
                } else {
                    s.status = 'Not Marked';
                }
            });
            renderTable();
        }
    } catch (e) {
        console.warn('Unable to load existing attendance', e);
    }
}

async function saveAttendance() {
    if (!token()) { alert('Not logged in'); return; }
    const date = document.getElementById("date").value;
    if (!date) { alert('Select a date'); return; }
    const payload = { date, attendance: students };
    try {
        const resp = await fetch(`${API_BASE_URL}/attendance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token()
            },
            body: JSON.stringify(payload)
        });
        const result = await resp.json();
        if (result.success) {
            alert('Attendance saved');
            // optionally reload or clear table
        } else {
            alert(result.message || 'Save failed');
        }
    } catch (e) {
        console.error('Save error', e);
        alert('Network error');
    }
}

document.getElementById("search").addEventListener("input",function(){

let value=this.value.toLowerCase()

let rows=document.querySelectorAll("#studentTable tr")

rows.forEach(row=>{

let name=row.children[1].innerText.toLowerCase()

row.style.display=name.includes(value)?"":"none"

})

})

// initial population is handled by the DOMContentLoaded listener above
