const API_URL = 'http://localhost:8000';

async function request(method, endpoint, body = null) {
    const token = sessionStorage.getItem('token');

    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        },
        ...(body && { body: JSON.stringify(body) })
    };

    const response = await fetch(`${API_URL}${endpoint}`, options);

    if (response.status === 401) {
        sessionStorage.clear();
        window.location.href = '/pages/login.html';
        return;
    }

    if (response.status === 403) {
        window.location.href = '/pages/login.html';
        return;
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
        throw new Error(error.detail || 'Ошибка сервера');
    }

    if (response.status === 204) return null;
    return response.json();
}

const api = {
    get:    (endpoint)       => request('GET',    endpoint),
    post:   (endpoint, body) => request('POST',   endpoint, body),
    patch:  (endpoint, body) => request('PATCH',  endpoint, body),
    delete: (endpoint)       => request('DELETE', endpoint),
};
