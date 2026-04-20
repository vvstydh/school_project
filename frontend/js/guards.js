function requireAuth(...allowedRoles) {
    const token = sessionStorage.getItem('token');
    const role  = sessionStorage.getItem('role');

    if (!token) {
        window.location.href = '/pages/login.html';
        return false;
    }

    if (allowedRoles.length && !allowedRoles.includes(role)) {
        window.location.href = '/pages/login.html';
        return false;
    }

    return true;
}
