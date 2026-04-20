async function login(email, password) {
    const body = new URLSearchParams({ username: email, password });
    const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
        throw new Error(err.detail || 'Ошибка сервера');
    }
    const data = await response.json();
    sessionStorage.setItem('token', data.access_token);
    sessionStorage.setItem('role', data.role);
    sessionStorage.setItem('user_id', data.user_id);
    redirectByRole(data.role);
}

function logout() {
    sessionStorage.clear();
    window.location.href = '/pages/login.html';
}

function redirectByRole(role) {
    const routes = {
        admin:          '/pages/admin/dashboard.html',
        vice_principal: '/pages/vice_principal/dashboard.html',
        teacher:        '/pages/teacher/dashboard.html',
        student:        '/pages/student/dashboard.html',
        parent:         '/pages/parent/dashboard.html',
    };
    window.location.href = routes[role] || '/pages/login.html';
}
