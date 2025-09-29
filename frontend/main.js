const API = "http://localhost:8000";

const authDiv = document.getElementById('auth');
const dashDiv = document.getElementById('dashboard');
const notesList = document.getElementById('notesList');
const profileDiv = document.getElementById('profile');
const loginEmailInput = document.getElementById('loginEmail');
const loginPasswordInput = document.getElementById('loginPassword');
const noteTitleInput = document.getElementById('noteTitle');
const noteContentInput = document.getElementById('noteContent');
const verifyEmailInput = document.getElementById('verifyEmail');
const verifyOtpInput = document.getElementById('verifyOtp');

function showDashboard() {
    authDiv.classList.add('hidden');
    dashDiv.classList.remove('hidden');
    fetchNotes();
}

function showAuth() {
    authDiv.classList.remove('hidden');
    dashDiv.classList.add('hidden');
    notesList.innerHTML = '';
    profileDiv.innerHTML = '';
}

function logout() {
    localStorage.removeItem('token');
    showAuth();
}

document.getElementById('registerForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const res = await fetch(`${API}/register`, {
        method: 'POST',
        body: formData
    });

    if (res.ok) {
        alert('Registered! OTP printed in server console. Verify your email below.');
        verifyEmailInput.value = formData.get('email');
        e.target.reset();
    } else {
        const error = await res.json();
        alert(`Registration failed: ${error.detail}`);
    }
};

document.getElementById('verifyForm').onsubmit = async (e) => {
    e.preventDefault();
    const res = await fetch(`${API}/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: verifyEmailInput.value,
            otp: verifyOtpInput.value
        })
    });

    if (res.ok) {
        alert('Email verified! You can now log in.');
        e.target.reset();
    } else {
        const err = await res.json().catch(() => ({}));
        alert(`Verification failed: ${err.detail || res.status}`);
    }
};

document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();
    const data = new URLSearchParams();
    data.append('username', loginEmailInput.value);
    data.append('password', loginPasswordInput.value);

    const res = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data
    });

    if (res.ok) {
        const json = await res.json();
        localStorage.setItem('token', json.access_token);
        showDashboard();
    } else {
        alert('Login failed. Please check your email and password.');
    }
};

document.getElementById('getProfileBtn').onclick = async () => {
    const token = localStorage.getItem('token');
    if (!token) return alert('Please login first!');

    const res = await fetch(`${API}/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (res.ok) {
        const user = await res.json();
        profileDiv.innerHTML = `
            <p><strong>Username:</strong> ${user.username}</p>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>Verified:</strong> ${user.is_verified ? 'Yes' : 'No'}</p>
        `;
    } else {
        alert('Failed to fetch profile.');
    }
};

document.getElementById('noteForm').onsubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    const res = await fetch(`${API}/notes`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            title: noteTitleInput.value,
            content: noteContentInput.value
        })
    });
    if (res.ok) {
        e.target.reset();
        fetchNotes();
    } else {
        alert('Failed to add note.');
    }
};

async function fetchNotes() {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API}/notes`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (res.status === 401) {
        logout();
        return;
    }

    if (res.ok) {
        const notes = await res.json();
        notesList.innerHTML = '';
        notes.forEach(note => {
            const div = document.createElement('div');
            div.className = 'note';
            div.innerHTML = `<b>${note.title}</b><br>${note.content}<button onclick="deleteNote('${note.id}')">Delete</button>`;
            notesList.appendChild(div);
        });
    }
}

window.deleteNote = async function (id) {
    if (!confirm('Are you sure you want to delete this note?')) return;
    const token = localStorage.getItem('token');
    const res = await fetch(`${API}/notes/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        fetchNotes();
    } else {
        alert('Failed to delete note.');
    }
}

function renderProfile(profile) {
    let html = `<p><b>Username:</b> ${profile.username}</p>
                <p><b>Email:</b> ${profile.email}</p>`;
    if (profile.profile_image_url) {
        html += `<img src="${profile.profile_image_url}" alt="Profile Image" />`;
    }
    document.getElementById('profile').innerHTML = html;
}

if (localStorage.getItem('token')) {
    showDashboard();
}