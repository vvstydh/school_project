Отлично, всё понятно. Вот готовый `CLAUDE.md` для фронтенда:

```markdown
# CLAUDE.md — Фронтенд (Электронный школьный журнал)

## Контекст проекта

Фронтенд для электронного школьного журнала.
Чистый HTML + CSS + JS, без фреймворков.
Административная панель на базе AdminLTE 3 + Bootstrap 5.

## Стек

- **HTML5** — отдельные .html файлы для каждой страницы
- **Bootstrap 5** — UI компоненты и сетка
- **AdminLTE 3** — шаблон административной панели
- **Vanilla JS** — логика, fetch запросы к API, DOM манипуляции
- **sessionStorage** — хранение JWT токена

## CDN подключения (в каждом HTML файле)

```html
<!-- Bootstrap 5 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

<!-- AdminLTE 3 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">

<!-- Font Awesome (иконки) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<!-- jQuery (нужен для AdminLTE) -->
<script src="https://cdn.jsdelivr.net/npm/jquery@3.7.0/dist/jquery.min.js"></script>

<!-- Bootstrap 5 JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- AdminLTE 3 JS -->
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>
```

## Структура проекта

```
frontend/
├── Dockerfile
├── nginx.conf
├── pages/
│   ├── login.html                  # Страница входа (без сайдбара)
│   ├── admin/
│   │   ├── dashboard.html          # Главная админа
│   │   ├── users/
│   │   │   ├── index.html          # Список пользователей
│   │   │   ├── create.html         # Создать пользователя
│   │   │   └── edit.html           # Редактировать пользователя
│   │   ├── classes/
│   │   │   ├── index.html          # Список классов
│   │   │   ├── create.html         # Создать класс
│   │   │   └── edit.html           # Редактировать класс
│   │   ├── subjects/
│   │   │   ├── index.html          # Список предметов
│   │   │   └── create.html         # Создать предмет
│   │   └── notifications/
│   │       └── index.html          # Уведомления
│   ├── teacher/
│   │   ├── dashboard.html
│   │   ├── lessons/
│   │   │   ├── index.html
│   │   │   └── detail.html
│   │   ├── grades/
│   │   │   └── index.html
│   │   └── attendances/
│   │       └── index.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── grades.html
│   │   ├── attendances.html
│   │   └── notifications.html
│   └── parent/
│       ├── dashboard.html
│       ├── grades.html
│       ├── attendances.html
│       └── notifications.html
├── components/
│   ├── sidebar-admin.html          # Сайдбар для админа
│   ├── sidebar-teacher.html        # Сайдбар для учителя
│   ├── sidebar-student.html        # Сайдбар для ученика
│   ├── sidebar-parent.html         # Сайдбар для родителя
│   └── navbar.html                 # Верхняя панель
├── js/
│   ├── api.js                      # Базовые fetch функции
│   ├── auth.js                     # Логика авторизации
│   ├── guards.js                   # Проверка роли и редиректы
│   └── pages/
│       ├── login.js
│       ├── admin/
│       │   ├── users.js
│       │   ├── classes.js
│       │   └── subjects.js
│       ├── teacher/
│       │   ├── lessons.js
│       │   ├── grades.js
│       │   └── attendances.js
│       └── student/
│           └── grades.js
└── css/
    └── custom.css                  # Только точечные переопределения
```

## API

### Базовый URL

```javascript
const API_URL = 'http://localhost:8000';
```

### Эндпоинты

```
POST   /auth/login                      — логин
GET    /users/                          — список пользователей
POST   /users/                          — создать пользователя
GET    /users/{id}                      — получить пользователя
PATCH  /users/{id}                      — обновить пользователя
DELETE /users/{id}                      — удалить пользователя
GET    /subjects/                       — список предметов
POST   /subjects/                       — создать предмет
GET    /classes/                        — список классов
POST   /classes/                        — создать класс
GET    /classes/{id}/students           — ученики класса
GET    /lessons/                        — список уроков
POST   /lessons/                        — создать урок
GET    /grades/                         — оценки
POST   /grades/                         — выставить оценку
PATCH  /grades/{id}                     — изменить оценку
GET    /attendances/                    — посещаемость
POST   /attendances/                    — отметить посещаемость
GET    /notifications/                  — уведомления
PATCH  /notifications/{id}/read        — отметить как прочитанное
```

## Аутентификация

### Хранение токена

```javascript
// Сохранить после логина
sessionStorage.setItem('token', response.access_token);
sessionStorage.setItem('role', response.role);
sessionStorage.setItem('user_id', response.user_id);

// Получить
const token = sessionStorage.getItem('token');

// Удалить при выходе
sessionStorage.clear();
```

### Заголовок для всех запросов

```javascript
headers: {
    'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
    'Content-Type': 'application/json'
}
```

## js/api.js — базовый модуль запросов

```javascript
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
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка сервера');
    }

    if (response.status === 204) return null;
    return response.json();
}

const api = {
    get:    (endpoint)        => request('GET',    endpoint),
    post:   (endpoint, body)  => request('POST',   endpoint, body),
    patch:  (endpoint, body)  => request('PATCH',  endpoint, body),
    delete: (endpoint)        => request('DELETE',  endpoint),
};
```

## js/auth.js — авторизация

```javascript
async function login(email, password) {
    const data = await api.post('/auth/login', { email, password });
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
        admin:           '/pages/admin/dashboard.html',
        vice_principal:  '/pages/admin/dashboard.html',
        teacher:         '/pages/teacher/dashboard.html',
        student:         '/pages/student/dashboard.html',
        parent:          '/pages/parent/dashboard.html',
    };
    window.location.href = routes[role] || '/pages/login.html';
}
```

## js/guards.js — защита страниц

```javascript
// Вставлять в начало каждой защищённой страницы
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

// Использование в начале каждой страницы
requireAuth('admin');                           // только админ
requireAuth('admin', 'vice_principal');         // админ и завуч
requireAuth('teacher');                         // только учитель
```

## Правила вёрстки

### Структура каждой HTML страницы (AdminLTE)

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Название страницы — Школьный журнал</title>
    <!-- CDN: Bootstrap, AdminLTE, FontAwesome -->
</head>
<body class="hold-transition sidebar-mini layout-fixed">
<div class="wrapper">

    <!-- Navbar -->
    <nav class="main-header navbar navbar-expand navbar-white navbar-light">
        ...
    </nav>

    <!-- Sidebar -->
    <aside class="main-sidebar sidebar-dark-primary elevation-4">
        ...
    </aside>

    <!-- Content -->
    <div class="content-wrapper">
        <div class="content-header">...</div>
        <section class="content">
            <div class="container-fluid">
                <!-- Контент страницы -->
            </div>
        </section>
    </div>

    <!-- Footer -->
    <footer class="main-footer">
        <strong>Школьный журнал</strong>
    </footer>

</div>
<!-- CDN: jQuery, Bootstrap JS, AdminLTE JS -->
<!-- Подключение JS страницы -->
</body>
</html>
```

### Компоненты AdminLTE которые используем

```
.card                        — блок с контентом
.card-header / .card-body    — части карточки
.table                       — таблицы данных
.btn .btn-primary / danger   — кнопки
.badge                       — статусы (роль, оценка)
.alert .alert-danger         — ошибки
.modal                       — модальные окна для форм
.breadcrumb                  — навигационная цепочка
.info-box                    — виджеты на дашборде
```

### Отключаемые элементы по роли

```javascript
// Скрывать элементы если роль не позволяет
function hideForRole(...roles) {
    const role = sessionStorage.getItem('role');
    if (!roles.includes(role)) {
        document.querySelectorAll('[data-role-required]').forEach(el => {
            const required = el.dataset.roleRequired.split(',');
            if (!required.includes(role)) {
                el.style.display = 'none';
            }
        });
    }
}

// В HTML разметке
<button data-role-required="admin,vice_principal"
        class="btn btn-danger">
    Удалить
</button>
```

### Уведомления об ошибках

```javascript
// Показать ошибку пользователю
function showError(message) {
    const alert = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;
    document.getElementById('alerts').innerHTML = alert;
}

function showSuccess(message) {
    const alert = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;
    document.getElementById('alerts').innerHTML = alert;
}
```

## Запрещено

- Хранить токен в `localStorage` — только `sessionStorage`
- Хардкодить данные — всё через fetch к API
- Показывать элементы управления если роль не позволяет
- Отправлять запросы без токена на защищённые эндпоинты
- Писать CSS вручную если есть готовый класс Bootstrap или AdminLTE
- Дублировать HTML сайдбара и навбара в каждом файле вручную — выносить в компоненты и подгружать через fetch

## Загрузка компонентов (сайдбар, navbar)

```javascript
// Подгружаем общие компоненты чтобы не дублировать HTML
async function loadComponent(selector, url) {
    const response = await fetch(url);
    const html = await response.text();
    document.querySelector(selector).innerHTML = html;
}

// В начале каждой страницы
await loadComponent('#navbar',  '/components/navbar.html');
await loadComponent('#sidebar', '/components/sidebar-admin.html');
```

## Порядок разработки

- [ ] login.html — страница входа
- [ ] js/api.js — базовый модуль
- [ ] js/auth.js — логин / логаут / редирект
- [ ] js/guards.js — защита страниц
- [ ] components/navbar.html
- [ ] components/sidebar-admin.html
- [ ] admin/dashboard.html — дашборд с виджетами
- [ ] admin/users/index.html — таблица пользователей
- [ ] admin/users/create.html — форма создания
- [ ] admin/users/edit.html — форма редактирования
- [ ] admin/classes/index.html
- [ ] admin/classes/create.html
- [ ] admin/subjects/index.html
- [ ] admin/notifications/index.html
- [ ] teacher/* — страницы учителя
- [ ] student/* — страницы ученика
- [ ] parent/* — страницы родителя
```

Создай файл в корне фронтенд папки:

```bash
touch frontend/CLAUDE.md
```