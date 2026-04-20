async function loadParentComponents(activePath) {
    const [navHtml, sideHtml] = await Promise.all([
        fetch('/components/navbar.html').then(r => r.text()),
        fetch('/components/sidebar-parent.html').then(r => r.text()),
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

const GRADE_COLORS = { 5: 'success', 4: 'info', 3: 'warning', 2: 'danger', 1: 'danger' };
const ATTENDANCE_LABELS = {
    present: { label: 'Присутствовал', color: 'success' },
    absent:  { label: 'Отсутствовал',  color: 'danger' },
    late:    { label: 'Опоздал',        color: 'warning' },
    excused: { label: 'Уважительная',   color: 'info' },
};
