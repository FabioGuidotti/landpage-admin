const API_BASE = '/api';
let authToken = localStorage.getItem('token');

// DOM Elements
const loginView = document.getElementById('login-view');
const dashView = document.getElementById('dashboard-view');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const landingsList = document.getElementById('landings-list');
const newLandingBtn = document.getElementById('new-landing-btn');
const modal = document.getElementById('landing-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const landingForm = document.getElementById('landing-form');

// State
let landings = [];

// Init
function init() {
    if (authToken) {
        showDashboard();
    } else {
        showLogin();
    }
}

// Views
function showLogin() {
    loginView.classList.add('active');
    loginView.classList.remove('hidden');
    dashView.classList.remove('active');
    dashView.classList.add('hidden');
}

function showDashboard() {
    loginView.classList.remove('active');
    loginView.classList.add('hidden');
    dashView.classList.add('active');
    dashView.classList.remove('hidden');
    fetchLandings();
}

// Auth
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_BASE}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!res.ok) throw new Error('Invalid credentials');
        const data = await res.json();
        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        loginError.classList.add('hidden');
        showDashboard();
    } catch (err) {
        loginError.classList.remove('hidden');
    }
});

logoutBtn.addEventListener('click', () => {
    authToken = null;
    localStorage.removeItem('token');
    showLogin();
});

// Fetch API helper
async function apiFetch(path, options = {}) {
    const headers = {
        'Authorization': `Bearer ${authToken}`,
        ...(options.headers || {})
    };
    if (options.body && !(options.body instanceof FormData) && typeof options.body !== 'string') {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (response.status === 401) {
        logoutBtn.click();
        throw new Error('Unauthorized');
    }
    return response.json();
}

// CRUD
async function fetchLandings() {
    try {
        landings = await apiFetch('/landings');
        renderTable();
    } catch (err) {
        console.error(err);
    }
}

function renderTable() {
    landingsList.innerHTML = '';
    landings.forEach(l => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${l.subdomain}</strong></td>
            <td>${l.whatsapp_number || '-'}</td>
            <td><span class="status-badge ${l.active ? 'status-active' : 'status-inactive'}">${l.active ? 'Active' : 'Inactive'}</span></td>
            <td>${new Date(l.created_at).toLocaleDateString()}</td>
            <td>
                <button class="btn outline-btn action-btn edit-btn" data-id="${l.id}">Edit</button>
                <button class="btn outline-btn action-btn delete-btn" data-id="${l.id}">Delete</button>
                <a href="https://${l.subdomain}.ai.dashx.com.br" target="_blank" class="btn outline-btn action-btn">View</a>
            </td>
        `;
        landingsList.appendChild(tr);
    });

    // Attach listeners
    document.querySelectorAll('.edit-btn').forEach(btn => btn.addEventListener('click', (e) => openModal(e.target.dataset.id)));
    document.querySelectorAll('.delete-btn').forEach(btn => btn.addEventListener('click', (e) => handleDelete(e.target.dataset.id)));
}

// Modal handling
newLandingBtn.addEventListener('click', () => openModal());
closeModalBtn.addEventListener('click', closeModal);

function openModal(id = null) {
    const title = document.getElementById('modal-title');
    if (id) {
        const landing = landings.find(l => l.id == id);
        title.textContent = 'Edit Landing Page';
        document.getElementById('landing-id').value = landing.id;
        document.getElementById('subdomain').value = landing.subdomain;
        document.getElementById('whatsapp_number').value = landing.whatsapp_number || '';
        document.getElementById('whatsapp_message').value = landing.whatsapp_message || '';
        document.getElementById('html_content').value = landing.html_content || '';
        document.getElementById('active').checked = landing.active;
    } else {
        title.textContent = 'New Landing Page';
        landingForm.reset();
        document.getElementById('landing-id').value = '';
    }
    modal.classList.remove('hidden');
}

function closeModal() {
    modal.classList.add('hidden');
}

landingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('landing-id').value;
    const payload = {
        subdomain: document.getElementById('subdomain').value,
        whatsapp_number: document.getElementById('whatsapp_number').value,
        whatsapp_message: document.getElementById('whatsapp_message').value,
        html_content: document.getElementById('html_content').value,
        active: document.getElementById('active').checked
    };

    try {
        if (id) {
            await apiFetch(`/landings/${id}`, { method: 'PUT', body: payload });
        } else {
            await apiFetch('/landings', { method: 'POST', body: payload });
        }
        closeModal();
        fetchLandings();
    } catch (err) {
        alert('Error saving rendering. Maybe subdomain already exists?');
    }
});

async function handleDelete(id) {
    if (confirm('Are you sure you want to delete this landing page?')) {
        try {
            await apiFetch(`/landings/${id}`, { method: 'DELETE' });
            fetchLandings();
        } catch (err) {
            alert('Error deleting');
        }
    }
}

init();
