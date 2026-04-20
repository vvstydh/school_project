const ROLE_LABELS = {
    admin:          'Администратор',
    vice_principal: 'Завуч',
    teacher:        'Учитель',
    student:        'Ученик',
    parent:         'Родитель',
};
const ROLE_COLORS = {
    admin:          'danger',
    vice_principal: 'warning',
    teacher:        'info',
    student:        'success',
    parent:         'secondary',
};

async function loadVPComponents(activePath) {
    const [navHtml, sideHtml] = await Promise.all([
        fetch('/components/navbar.html').then(r => r.text()),
        fetch('/components/sidebar-vp.html').then(r => r.text()),
    ]);
    document.getElementById('navbar').innerHTML = navHtml;
    document.getElementById('sidebar').innerHTML = sideHtml;

    const me = await api.get('/users/me');
    const fullName = `${me.last_name} ${me.first_name}`;
    document.getElementById('navbar-user-name').textContent = fullName;
    document.getElementById('sidebar-user-name').textContent = fullName;

    if (activePath) {
        document.querySelectorAll('.nav-sidebar .nav-link').forEach(link => {
            const href = link.getAttribute('href') || '';
            if (href.includes(activePath)) link.classList.add('active');
        });
    }
    return me;
}

function showAlert(msg, type = 'danger') {
    document.getElementById('alerts').innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle mr-2"></i>${msg}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;
}
