# Документация фронтенда — Зурнал

## Содержание

1. [Обзор архитектуры](#1-обзор-архитектуры)
2. [Технологический стек](#2-технологический-стек)
3. [Структура директорий](#3-структура-директорий)
4. [Сборка и деплой](#4-сборка-и-деплой)
5. [Nginx — конфигурация сервера](#5-nginx--конфигурация-сервера)
6. [Глобальные JS-модули](#6-глобальные-js-модули)
7. [Общие JS-компоненты по ролям](#7-общие-js-компоненты-по-ролям)
8. [HTML-компоненты](#8-html-компоненты)
9. [Стили — css/custom.css](#9-стили--csscustomcss)
10. [Страницы по ролям](#10-страницы-по-ролям)
11. [Шаблон страницы](#11-шаблон-страницы)
12. [Система авторизации на фронтенде](#12-система-авторизации-на-фронтенде)
13. [Жизненный цикл страницы](#13-жизненный-цикл-страницы)
14. [Обработка ошибок API](#14-обработка-ошибок-api)
15. [Добавление новой страницы](#15-добавление-новой-страницы)

---

## 1. Обзор архитектуры

Фронтенд — **статический сайт** (HTML + CSS + Vanilla JS), раздаётся через **Nginx**. Нет сборщика (webpack, vite и т.д.) и фреймворков (React, Vue). Каждая страница — отдельный `.html`-файл со встроенным JS.

```
Браузер
  │
  └── HTTP запрос → Nginx (порт 80)
            │
            ├── /pages/*.html  → статические файлы из /usr/share/nginx/html
            ├── /js/*.js       → статические JS
            ├── /css/*.css     → статические CSS
            └── /api/*         → proxy_pass → http://api:8000/ (бэкенд)
```

**Важно:** фронтенд обращается к API напрямую через `http://localhost:8000` (прямой порт бэкенда), а не через Nginx-прокси `/api/`. Переменная `API_URL = 'http://localhost:8000'` захардкожена в `js/api.js`.

**Сессия** хранится в `sessionStorage` браузера:
- `token` — JWT Bearer-токен
- `role` — роль (`admin/vice_principal/teacher/student/parent`)
- `user_id` — UUID текущего пользователя

---

## 2. Технологический стек

| Технология | Версия | Подключение | Назначение |
|-----------|--------|-------------|-----------|
| Bootstrap | 5.3.0 | CDN | CSS-утилиты, сетка, компоненты |
| AdminLTE | 3.2 | CDN | Шаблон дашборда (сайдбар, навбар, карточки) |
| Font Awesome | 6.4.0 | CDN | Иконки |
| jQuery | 3.7.0 | CDN | Требуется AdminLTE |
| Vanilla JS | ES2020+ | встроен | Логика страниц (async/await, fetch) |

Все CDN-зависимости подключаются в каждом HTML-файле. Интернет-соединение обязательно при первом открытии (до кэширования браузером).

---

## 3. Структура директорий

```
frontend/
├── Dockerfile                          # nginx:alpine, копирует всё в /usr/share/nginx/html
├── nginx.conf                          # конфигурация Nginx
├── css/
│   └── custom.css                      # переопределения AdminLTE и кастомные стили
├── js/
│   ├── api.js                          # HTTP-клиент (обёртка над fetch)
│   ├── auth.js                         # login(), logout(), redirectByRole()
│   ├── guards.js                       # requireAuth() — проверка доступа к странице
│   └── pages/
│       ├── admin/
│       │   └── common.js               # loadAdminComponents(), showAlert(), ROLE_LABELS/COLORS
│       ├── vice_principal/
│       │   └── common.js               # loadVpComponents()
│       ├── teacher/
│       │   └── common.js               # loadTeacherComponents(), GRADE_COLORS, ATTENDANCE_LABELS
│       ├── student/
│       │   └── common.js               # loadStudentComponents(), GRADE_COLORS, ATTENDANCE_LABELS
│       └── parent/
│           └── common.js               # loadParentComponents(), GRADE_COLORS, ATTENDANCE_LABELS
├── components/
│   ├── navbar.html                     # верхняя навигационная панель (общая для всех)
│   ├── sidebar-admin.html              # боковое меню администратора
│   ├── sidebar-vp.html                 # боковое меню завуча
│   ├── sidebar-teacher.html            # боковое меню учителя
│   ├── sidebar-student.html            # боковое меню ученика
│   └── sidebar-parent.html             # боковое меню родителя
└── pages/
    ├── login.html                      # страница входа (единственная без авторизации)
    ├── admin/
    │   ├── dashboard.html              # дашборд с статистикой
    │   ├── users/
    │   │   ├── index.html              # список всех пользователей
    │   │   ├── create.html             # форма создания пользователя
    │   │   └── edit.html               # форма редактирования пользователя + профили
    │   ├── classes/
    │   │   ├── index.html              # список классов
    │   │   ├── create.html             # форма создания класса
    │   │   ├── edit.html               # форма редактирования класса
    │   │   └── detail.html             # управление учениками и учителями класса
    │   ├── subjects/
    │   │   └── index.html              # CRUD предметов
    │   ├── lessons/
    │   │   └── index.html              # список уроков
    │   ├── grades/
    │   │   └── index.html              # список оценок
    │   ├── attendances/
    │   │   └── index.html              # список посещаемости
    │   └── notifications/
    │       └── index.html              # список уведомлений + отправка
    ├── vice_principal/
    │   ├── dashboard.html              # дашборд завуча
    │   └── users/
    │       ├── index.html              # список пользователей (VP)
    │       ├── create.html             # создание пользователя (VP)
    │       ├── edit.html               # редактирование (VP)
    │       ├── profile.html            # собственный профиль завуча
    │       └── view.html               # просмотр карточки пользователя (read-only)
    ├── teacher/
    │   ├── dashboard.html              # дашборд учителя
    │   ├── lessons/
    │   │   ├── index.html              # список уроков учителя
    │   │   └── detail.html             # урок + журнал оценок и посещаемости
    │   ├── grades/
    │   │   └── index.html              # сводная таблица оценок
    │   ├── attendances/
    │   │   └── index.html              # сводная таблица посещаемости
    │   └── notifications.html          # уведомления учителя
    ├── student/
    │   ├── dashboard.html              # дашборд ученика
    │   ├── lessons.html                # расписание/список уроков
    │   ├── grades.html                 # мои оценки
    │   ├── attendances.html            # моя посещаемость
    │   ├── analytics.html              # аналитика успеваемости (средний балл и т.д.)
    │   └── notifications.html          # мои уведомления
    └── parent/
        ├── dashboard.html              # дашборд родителя
        ├── grades.html                 # оценки детей
        ├── attendances.html            # посещаемость детей
        └── notifications.html          # уведомления родителя
```

---

## 4. Сборка и деплой

### Dockerfile

```dockerfile
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html
EXPOSE 80
```

Все файлы фронтенда копируются в `/usr/share/nginx/html` при сборке образа. Nginx раздаёт их как статику.

**Критически важно:** изменение любого HTML/JS/CSS файла требует **пересборки образа**:

```bash
docker compose up -d --build frontend
```

В отличие от бэкенда, фронтенд **не имеет hot-reload** — нет volume mount с локальными файлами. Каждое изменение = пересборка.

### Типичный workflow разработки

```bash
# Внести изменения в frontend/
# Пересобрать и перезапустить фронтенд:
docker compose up -d --build frontend

# Открыть в браузере (hard refresh для сброса кэша):
# Ctrl+Shift+R (Windows/Linux) / Cmd+Shift+R (macOS)
```

---

## 5. Nginx — конфигурация сервера

**Файл:** `frontend/nginx.conf`

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    location = / {
        return 301 /pages/login.html;   # корень → страница входа
    }

    location / {
        try_files $uri $uri/ =404;      # раздача статики
    }

    location /api/ {
        proxy_pass http://api:8000/;    # прокси к бэкенду
    }

    location ~* \.(css|js)$ {
        expires -1;                     # отключить кэш JS/CSS в разработке
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }
}
```

**Маршруты Nginx:**

| Паттерн | Действие | Пример |
|---------|---------|--------|
| `GET /` | Редирект 301 | → `/pages/login.html` |
| `GET /pages/*.html` | Статический файл | `frontend/pages/admin/dashboard.html` |
| `GET /js/*.js` | Статический файл, без кэша | `frontend/js/api.js` |
| `GET /css/*.css` | Статический файл, без кэша | `frontend/css/custom.css` |
| `GET /api/*` | Прокси | → `http://api:8000/*` |

**Замечание по API_URL:** несмотря на наличие `/api/` прокси, фронтенд обращается к API напрямую (`http://localhost:8000`), а не через прокси. Если потребуется скрыть порт 8000, нужно:
1. Изменить `API_URL` в `js/api.js` на `''` (пустая строка = текущий хост)
2. Все запросы будут идти через Nginx-прокси `/api/`

---

## 6. Глобальные JS-модули

Три файла, подключаемые на **каждой** странице (кроме `login.html`, который использует только `api.js` и `auth.js`).

---

### `js/api.js`

**Назначение:** единый HTTP-клиент для всех запросов к бэкенду.

**Константы:**
```javascript
const API_URL = 'http://localhost:8000';
```

**Словарь имён полей** `_FIELD_LABELS` — маппинг технических имён полей на русские названия для отображения ошибок валидации:
```javascript
{ first_name: 'Имя', last_name: 'Фамилия', email: 'Email', value: 'Оценка', ... }
```

**Функция `_formatValidationError(e)`** — форматирует одну ошибку Pydantic (422-ответ) в читаемую строку:
- Определяет поле из `e.loc` (массив из пути к полю)
- Переводит `e.type` в русское сообщение (missing, string_too_short, uuid_parsing и т.д.)
- Возвращает строку `"Поле: Сообщение"` или просто `"Сообщение"` если поле не определено

**Функция `request(method, endpoint, body)`** — основная функция запросов:

```javascript
async function request(method, endpoint, body = null) {
    // 1. Берёт токен из sessionStorage
    const token = sessionStorage.getItem('token');

    // 2. Формирует fetch-опции
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        },
        ...(body && { body: JSON.stringify(body) })
    };

    // 3. Выполняет запрос
    const response = await fetch(`${API_URL}${endpoint}`, options);

    // 4. 401 → очистить сессию + редирект на login
    if (response.status === 401) {
        sessionStorage.clear();
        window.location.href = '/pages/login.html';
        return;
    }

    // 5. 403 → редирект на login (нет прав)
    if (response.status === 403) {
        window.location.href = '/pages/login.html';
        return;
    }

    // 6. Другие ошибки → парсим detail и бросаем Error
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
        const detail = error.detail;
        let message;
        if (typeof detail === 'string') {
            message = detail;
        } else if (Array.isArray(detail)) {
            // Pydantic 422 — массив ошибок
            message = detail.map(_formatValidationError).join('\n');
        }
        throw new Error(message);
    }

    // 7. 204 No Content → null
    if (response.status === 204) return null;

    // 8. Парсим JSON ответ
    return response.json();
}
```

**Объект `api`** — сокращённые методы:
```javascript
const api = {
    get:    (endpoint)       => request('GET',    endpoint),
    post:   (endpoint, body) => request('POST',   endpoint, body),
    patch:  (endpoint, body) => request('PATCH',  endpoint, body),
    delete: (endpoint)       => request('DELETE', endpoint),
};
```

**Типичное использование на страницах:**
```javascript
const users = await api.get('/users/');
const newUser = await api.post('/users/', { email: '...', role: 'student', ... });
await api.delete(`/users/${id}`);
```

---

### `js/auth.js`

**Назначение:** авторизация, выход из системы, редирект по роли.

**Функция `login(email, password)`:**
```javascript
async function login(email, password) {
    // POST /auth/login с form-data (не JSON!)
    const body = new URLSearchParams({ username: email, password });
    const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
    });
    // Сохраняет в sessionStorage: token, role, user_id
    sessionStorage.setItem('token', data.access_token);
    sessionStorage.setItem('role', data.role);
    sessionStorage.setItem('user_id', data.user_id);
    // Редирект по роли
    redirectByRole(data.role);
}
```

**Важно:** `/auth/login` принимает `application/x-www-form-urlencoded` (не JSON). Поле называется `username`, но содержит email. `auth.js` использует `URLSearchParams` вместо JSON.

**Функция `logout()`:**
```javascript
function logout() {
    sessionStorage.clear();                    // удалить token, role, user_id
    window.location.href = '/pages/login.html';
}
```

Вызывается из кнопки "Выйти" в `navbar.html`: `onclick="logout()"`.

**Функция `redirectByRole(role)`:**
```javascript
const routes = {
    admin:          '/pages/admin/dashboard.html',
    vice_principal: '/pages/vice_principal/dashboard.html',
    teacher:        '/pages/teacher/dashboard.html',
    student:        '/pages/student/dashboard.html',
    parent:         '/pages/parent/dashboard.html',
};
window.location.href = routes[role] || '/pages/login.html';
```

---

### `js/guards.js`

**Назначение:** защита страниц от несанкционированного доступа.

**Функция `requireAuth(...allowedRoles)`:**

```javascript
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
```

Вызывается в начале `<script>` каждой защищённой страницы:
```javascript
requireAuth('admin');                          // только admin
requireAuth('admin', 'vice_principal');        // admin или VP
requireAuth('teacher');                        // только teacher
requireAuth('student');                        // только student
requireAuth('parent');                         // только parent
```

**Замечание:** проверка происходит на клиенте. Бэкенд проводит независимую серверную проверку через JWT. Клиентская проверка служит только для UX (немедленный редирект без лишних запросов).

---

## 7. Общие JS-компоненты по ролям

В `js/pages/{role}/common.js` находятся функции, используемые всеми страницами данной роли.

### Функция `load{Role}Components(activePath)`

Одинакова для всех ролей, отличается только названием sidebar-файла.

**Алгоритм:**
1. `Promise.all` — параллельный fetch `navbar.html` и `sidebar-{role}.html`
2. Вставка HTML в `#navbar` и `#sidebar`
3. `api.get('/users/me')` — загрузка имени текущего пользователя
4. Заполнение `#navbar-user-name` и `#sidebar-user-name` форматом `Фамилия Имя`
5. Подсветка активного пункта меню: если `href` содержит `activePath` → добавить класс `active`

**Возвращает** объект пользователя `me` (используется на странице для инициализации).

**Пример вызова:**
```javascript
const me = await loadAdminComponents('users');  // подсветит пункт "Пользователи"
const me = await loadTeacherComponents('lessons');  // подсветит пункт "Уроки"
```

### Функция `showAlert(msg, type = 'danger')`

Показывает Bootstrap-алерт в элементе `#alerts`:
```javascript
function showAlert(msg, type = 'danger') {
    document.getElementById('alerts').innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle mr-2"></i>${msg}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;
}
```

Параметр `type`: `'danger'` (ошибка), `'success'` (успех), `'warning'`, `'info'`.

### Константы (teacher, student, parent)

```javascript
const GRADE_COLORS = {
    5: 'success',  // зелёный
    4: 'info',     // голубой
    3: 'warning',  // жёлтый
    2: 'danger',   // красный
    1: 'danger'    // красный
};

const ATTENDANCE_LABELS = {
    present: { label: 'Присутствовал', color: 'success' },
    absent:  { label: 'Отсутствовал',  color: 'danger' },
    late:    { label: 'Опоздал',        color: 'warning' },
    excused: { label: 'Уважительная',   color: 'info' },
};
```

### Дополнительные константы в `admin/common.js`

```javascript
const ROLE_LABELS = {
    admin: 'Администратор', vice_principal: 'Завуч',
    teacher: 'Учитель', student: 'Ученик', parent: 'Родитель',
};

const ROLE_COLORS = {
    admin: 'danger', vice_principal: 'warning',
    teacher: 'info', student: 'success', parent: 'secondary',
};
```

---

## 8. HTML-компоненты

Компоненты в `components/` — это HTML-фрагменты, подгружаемые через `fetch` и вставляемые в DOM.

### `components/navbar.html`

Верхняя панель, одинакова для всех ролей:
- Кнопка открытия/закрытия сайдбара (`data-widget="pushmenu"`)
- Имя пользователя в `<span id="navbar-user-name">` (заполняется в JS)
- Кнопка "Выйти" (`onclick="logout()"`)

### `components/sidebar-{role}.html`

Пять файлов боковых меню — по одному на роль. Структура одинакова, отличаются ссылки и название роли.

| Файл | Роль | Пункты меню |
|------|------|-------------|
| `sidebar-admin.html` | Администратор | Главная, Пользователи, Классы, Предметы, Уроки, Оценки, Посещаемость, Уведомления |
| `sidebar-vp.html` | Завуч | Главная, Пользователи, Мой профиль, Классы, Предметы, Уроки, Оценки, Посещаемость, Уведомления |
| `sidebar-teacher.html` | Учитель | Главная, Уроки, Оценки, Посещаемость, Уведомления |
| `sidebar-student.html` | Ученик | Главная, Уроки, Оценки, Посещаемость, Аналитика, Уведомления |
| `sidebar-parent.html` | Родитель | Главная, Оценки, Посещаемость, Уведомления |

**Элемент `id="sidebar-user-name"`** — заполняется в JS именем текущего пользователя.

**Брендинг** (верх сайдбара):
```html
<a href="/pages/{role}/dashboard.html" class="brand-link">
    <i class="fas fa-school brand-image ml-3"></i>
    <span class="brand-text font-weight-bold">Зурнал</span>
</a>
```

**Замечание:** завуч (`sidebar-vp.html`) переиспользует страницы администратора для Классов, Предметов, Уроков, Оценок, Посещаемости — ссылки ведут в `/pages/admin/`.

---

## 9. Стили — `css/custom.css`

Файл переопределяет стандартные стили AdminLTE и добавляет кастомные компоненты.

### Брендовая иконка в сайдбаре

```css
.brand-link {
    display: flex !important;
    align-items: center;
}
.brand-link i.brand-image {
    float: none !important;     /* AdminLTE по умолчанию float: left для <img> */
    margin-top: 0 !important;   /* сбрасываем AdminLTE offset */
    font-size: 1.1rem;
    line-height: 1;
}
```
AdminLTE класс `.brand-image` рассчитан на `<img>`, а не на `<i>`. `float: left` из AdminLTE убирается через `flex` на родителе.

### Страница входа

```css
.login-page {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.login-box { width: 380px; }
.login-card-body { border-top: 3px solid #007bff; }
.login-logo a { color: #fff; font-weight: 700; font-size: 1.8rem; }
.login-logo small { display: block; color: rgba(255,255,255,0.6); font-size: 0.9rem; }
```

### Прочие переопределения

| Класс | Что делает |
|-------|-----------|
| `.nav-sidebar .nav-link.active` | Фон активного пункта меню — `rgba(255,255,255,0.15)` |
| `.card-header .card-title` | `font-weight: 600` |
| `.table th` | Верхняя граница убрана, текст в UPPERCASE, `color: #6c757d`, `font-size: 0.85rem` |
| `.badge-role` | `font-size: 0.8rem`, компактный паддинг |
| `.info-box .info-box-icon` | `font-size: 2rem` |
| `.spinner-overlay` | Полноэкранный оверлей со спиннером, показывается добавлением класса `active` |

### Стили уведомлений

```css
.notif-text  { flex: 1 1 0; min-width: 0; overflow: hidden; }
.notif-title { display: block; word-break: break-word; overflow-wrap: anywhere; }
.notif-body  { word-break: break-word; overflow-wrap: anywhere; white-space: pre-line; }
```
`white-space: pre-line` на `.notif-body` — переносы строк из текста уведомления отображаются.

---

## 10. Страницы по ролям

### Страница входа — `pages/login.html`

**Доступ:** без авторизации. При наличии токена — сразу редирект по роли.

**Логика:**
```javascript
// Если уже залогинен — редирект
if (sessionStorage.getItem('token')) {
    redirectByRole(sessionStorage.getItem('role'));
}

// Отправка формы
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await login(email.value.trim(), password.value);
    // login() → сохраняет в sessionStorage → вызывает redirectByRole()
});
```

**Подключаемые скрипты:** `api.js`, `auth.js` (без `guards.js` — страница публичная).

---

### Страницы администратора — `pages/admin/`

#### `dashboard.html`

**Guard:** `requireAuth('admin', 'vice_principal')`

**API-запросы:**
- `GET /users/` — все пользователи
- `GET /classes/` — все классы
- `GET /subjects/` — все предметы

**Отображает:**
- 4 info-box: общее число пользователей, классов, предметов, учеников
- Таблица последних 5 пользователей (реверс массива, slice(0,5))
- Список-группа с количеством пользователей по каждой роли

---

#### `users/index.html`

**Guard:** `requireAuth('admin', 'vice_principal')`

**API:** `GET /users/`

**Функционал:**
- Таблица всех пользователей с ФИО, email, ролью (цветной бейдж), статусом
- Кнопки: просмотр профиля (`edit.html?id=...`)
- Кнопка "Добавить" → `create.html`
- Модальное окно подтверждения удаления → `DELETE /users/{id}`
- Завуч (`role === 'vice_principal'`) не видит кнопку удаления (проверка в JS)

---

#### `users/create.html`

**Guard:** `requireAuth('admin', 'vice_principal')`

**API:** `POST /users/`

**Форма:** Фамилия, Имя, Отчество, Email, Пароль, Роль (select), Аккаунт активен (checkbox).

**Логика:** отправка формы → `api.post('/users/', body)` → редирект на `index.html` при успехе.

---

#### `users/edit.html`

**Guard:** `requireAuth('admin', 'vice_principal')`

**URL-параметр:** `?id=UUID`

**API-запросы:**
- `GET /users/{id}` — загрузка данных пользователя
- `GET /subjects/` — для выбора предмета учителя
- `GET /users/?role=student` — для выбора детей у родителя
- `PATCH /users/{id}` — обновление основных данных
- `POST/PATCH /users/{id}/teacher-profile` — создание/обновление профиля учителя
- `POST/PATCH /users/{id}/student-profile` — создание/обновление профиля ученика
- `POST /users/parents/{pid}/children/{sid}` — привязка ребёнка
- `DELETE /users/parents/{pid}/children/{sid}` — отвязка ребёнка

**Дополнительные карточки** (показываются в зависимости от роли):
- `teacher` → карточка "Профиль учителя" (select предмета)
- `student` → карточка "Профиль ученика" (дата рождения)
- `parent` → карточка "Дети" (таблица детей + добавление/удаление)

**Переменные состояния:**
```javascript
let hasTeacherProfile = false;  // есть ли уже профиль → POST или PATCH
let hasStudentProfile = false;
let currentUser = null;
let allStudents = [];           // для выбора детей родителя
```

---

#### `classes/index.html`

**Guard:** `requireAuth('admin', 'vice_principal')`

**API:** `GET /classes/`

**Таблица:** Название класса, Учебный год, кнопки (управление → `detail.html`, редактировать → `edit.html`, удалить).

---

#### `classes/create.html`

**API:** `POST /classes/`

**Форма:** Название (паттерн `^[1-9][0-9]?[А-ЯЁ]$`), Учебный год (auto-fill текущим годом).

---

#### `classes/edit.html`

**URL:** `?id=UUID`

**API:** `GET /classes/{id}`, `PATCH /classes/{id}`

---

#### `classes/detail.html`

**URL:** `?id=UUID`

**Управление составом класса:**

| Секция | API | Описание |
|--------|-----|----------|
| Ученики класса | `GET /classes/{id}/students` | Таблица учеников, кнопка удалить |
| Добавить ученика | `GET /users/` + `POST /classes/{id}/students` | Select из учеников не в классе |
| Учителя класса | `GET /classes/{id}/teachers` | Таблица учителей |
| Добавить учителя | `GET /users/` + `POST /classes/{id}/teachers` | Select из учителей |

---

#### `subjects/index.html`

**Совмещённый CRUD** на одной странице: список + инлайн-форма создания + редактирование через модалку.

**API:** `GET /subjects/`, `POST /subjects/`, `PATCH /subjects/{id}`, `DELETE /subjects/{id}`

---

#### `lessons/index.html`

**API:** `GET /lessons/`, `GET /classes/`, `GET /users/?role=teacher`, `GET /subjects/`

**Функционал:** фильтр по классу, список уроков с предметом, учителем, датой, темой.

---

#### `grades/index.html`

**API:** `GET /grades/`, `GET /lessons/`, `GET /users/?role=student`

**Фильтрация:** по классу, уроку, ученику. Таблица с оценкой (цветной бейдж) и комментарием.

---

#### `attendances/index.html`

**API:** `GET /attendances/`, `GET /lessons/`

**Фильтрация:** по уроку, ученику. Статус посещаемости с цветным бейджем.

---

#### `notifications/index.html`

**API:** `GET /notifications/`, `POST /notifications/`, `PATCH /notifications/{id}/read`, `DELETE /notifications/{id}`

**Функционал:**
- Список уведомлений с отметкой прочитано/непрочитано
- Форма отправки нового уведомления (выбор получателя из всех пользователей)
- Кнопка "Отметить прочитанным" на каждом уведомлении
- Кнопка удаления

---

### Страницы завуча — `pages/vice_principal/`

Завуч использует большинство admin-страниц напрямую (классы, предметы, уроки, оценки, посещаемость, уведомления). Собственные страницы только для управления пользователями.

#### `dashboard.html`

**Guard:** `requireAuth('vice_principal')`

Аналогичен admin dashboard, но использует `sidebar-vp.html`.

#### `users/index.html`, `create.html`, `edit.html`

Аналогичны admin-версиям, но завуч не может создавать admin-пользователей (бэкенд блокирует), не может редактировать чужие аккаунты.

#### `users/profile.html`

**Guard:** `requireAuth('vice_principal')`

Собственный профиль завуча — `GET /users/me`, `PATCH /users/{id}`. Форма редактирования: ФИО, email, пароль.

#### `users/view.html`

**URL:** `?id=UUID`

Read-only просмотр карточки пользователя (без кнопок редактирования).

---

### Страницы учителя — `pages/teacher/`

#### `dashboard.html`

**Guard:** `requireAuth('teacher')`

**API:** `GET /users/me`, `GET /lessons/` (свои уроки), `GET /grades/` (свои оценки)

**Отображает:** количество своих уроков, оценок, последние уроки.

#### `lessons/index.html`

**API:** `GET /lessons/` (API фильтрует только уроки учителя)

Список уроков с датой, классом, предметом, темой. Кнопка "Подробнее" → `detail.html?id=...`.

#### `lessons/detail.html`

**URL:** `?id=UUID`

**Главная рабочая страница учителя.** Включает три секции на одной странице:

| Секция | API | Описание |
|--------|-----|----------|
| Информация об уроке | `GET /lessons/{id}` | Дата, предмет, класс |
| Редактировать тему | `PATCH /lessons/{id}` | Только поле `topic` |
| Журнал оценок | `GET /grades/?lesson_id={id}`, `GET /classes/{class_id}/students` | Таблица: ученик + его оценка. Выставить/изменить/удалить оценку |
| Журнал посещаемости | `GET /attendances/?lesson_id={id}` | Таблица: ученик + статус. Отметить/изменить/удалить |

**Алгоритм загрузки:**
1. `GET /lessons/{id}` → данные урока + `class_id`
2. `GET /classes/{class_id}/students` → список учеников
3. `GET /grades/?lesson_id={id}` → оценки
4. `GET /attendances/?lesson_id={id}` → посещаемость
5. Слить данные учеников с оценками и посещаемостью по `student_id`

#### `grades/index.html`

Сводная таблица всех оценок учителя. Фильтр по уроку.

#### `attendances/index.html`

Сводная таблица посещаемости. Фильтр по уроку.

#### `notifications.html`

Уведомления, адресованные учителю. `GET /notifications/`, пометить прочитанным, удалить.

---

### Страницы ученика — `pages/student/`

#### `dashboard.html`

**Guard:** `requireAuth('student')`

**API:** `GET /users/me`, `GET /grades/` (свои), `GET /attendances/` (свои), `GET /lessons/`

**Отображает:** последние оценки, количество посещённых/пропущенных уроков, ближайшие уроки.

#### `lessons.html`

**API:** `GET /lessons/` (API возвращает только уроки класса ученика)

Список уроков с датой, предметом, темой.

#### `grades.html`

**API:** `GET /grades/` (только свои), `GET /lessons/`

Таблица оценок с предметом, датой, оценкой (цветной бейдж), комментарием.

#### `attendances.html`

**API:** `GET /attendances/` (только свои), `GET /lessons/`

Таблица посещаемости с датой, предметом, статусом (цветной бейдж).

#### `analytics.html`

**Guard:** `requireAuth('student')`

**API:** `GET /grades/`, `GET /lessons/`

**Вычисляет и отображает:**
- Общий средний балл (среднее по всем оценкам)
- Общее количество оценок
- Процент присутствия
- Таблица среднего балла по каждому предмету (группировка `grades` по `subject_id` через `lessons`)

Все вычисления выполняются в JS на клиенте (не на сервере).

#### `notifications.html`

Уведомления ученика. `GET /notifications/`, пометить прочитанным, удалить.

---

### Страницы родителя — `pages/parent/`

#### `dashboard.html`

**Guard:** `requireAuth('parent')`

**API:** `GET /users/me` (включает `children` — список детей)

Отображает список детей с краткой информацией.

#### `grades.html`

**API:** `GET /grades/` (API возвращает оценки всех детей), `GET /lessons/`

Фильтр по ребёнку. Таблица: ребёнок, предмет, дата, оценка.

#### `attendances.html`

**API:** `GET /attendances/` (все дети), `GET /lessons/`

Аналогично grades — фильтр по ребёнку, таблица посещаемости.

#### `notifications.html`

Уведомления родителя. `GET /notifications/`, пометить прочитанным, удалить.

---

## 11. Шаблон страницы

Каждая страница (кроме login) следует единому шаблону.

### HTML-скелет

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Название страницы — Зурнал</title>
    <!-- CDN зависимости -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="/css/custom.css">
</head>
<body class="hold-transition sidebar-mini layout-fixed">
<div class="wrapper">

    <!-- Компоненты (подгружаются через fetch) -->
    <div id="navbar"></div>
    <div id="sidebar"></div>

    <div class="content-wrapper">
        <!-- Заголовок страницы с хлебными крошками -->
        <div class="content-header">
            <div class="container-fluid">
                <div class="row mb-2">
                    <div class="col-sm-6"><h1 class="m-0">Заголовок</h1></div>
                    <div class="col-sm-6">
                        <ol class="breadcrumb float-sm-right">
                            <li class="breadcrumb-item"><a href="...">Главная</a></li>
                            <li class="breadcrumb-item active">Текущая страница</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>

        <!-- Контент -->
        <section class="content">
            <div class="container-fluid">
                <div id="alerts"></div>  <!-- сюда showAlert() вставляет алерты -->
                <!-- ... основной контент ... -->
            </div>
        </section>
    </div>

    <footer class="main-footer"><strong>Зурнал</strong> &copy; 2024</footer>
</div>

<!-- JS зависимости (в конце body) -->
<script src="https://cdn.jsdelivr.net/npm/jquery@3.7.0/dist/jquery.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>
<script src="/js/api.js"></script>
<script src="/js/auth.js"></script>
<script src="/js/guards.js"></script>
<script>
    // 1. Guard — первым делом, блокирует страницу для нужных ролей
    requireAuth('admin');

    // 2. Инициализация IIFE
    (async () => {
        await loadComponents();     // navbar + sidebar + имя пользователя
        await loadPageData();       // основные данные страницы
    })();
</script>
</body>
</html>
```

### Паттерн загрузки компонентов

На страницах администратора, где нет подключённого `admin/common.js`, компоненты загружаются инлайн:

```javascript
async function loadComponents() {
    const role = sessionStorage.getItem('role');
    // VP и admin могут использовать одни страницы → выбор сайдбара по роли
    const sidebarFile = role === 'vice_principal' ? 'sidebar-vp' : 'sidebar-admin';

    const [navHtml, sideHtml] = await Promise.all([
        fetch('/components/navbar.html').then(r => r.text()),
        fetch(`/components/${sidebarFile}.html`).then(r => r.text()),
    ]);
    document.getElementById('navbar').innerHTML = navHtml;
    document.getElementById('sidebar').innerHTML = sideHtml;

    const me = await api.get('/users/me');
    document.getElementById('navbar-user-name').textContent = `${me.last_name} ${me.first_name}`;
    document.getElementById('sidebar-user-name').textContent = `${me.last_name} ${me.first_name}`;
}
```

**Важный момент:** страницы Классов, Предметов и т.д. доступны и admin, и VP. Обе роли могут попасть туда. Guard `requireAuth('admin', 'vice_principal')` разрешает обоих. Сайдбар выбирается по роли из `sessionStorage`:
```javascript
const sidebarFile = role === 'vice_principal' ? 'sidebar-vp' : 'sidebar-admin';
```

---

## 12. Система авторизации на фронтенде

### Хранение состояния

```
sessionStorage
├── token    = "eyJhbGc..."  (JWT Bearer-токен)
├── role     = "admin"       (роль для guard и выбора сайдбара)
└── user_id  = "uuid-..."    (UUID текущего пользователя)
```

`sessionStorage` — данные живут только в рамках одной вкладки браузера. Закрытие вкладки → выход из системы. Перезагрузка страницы — данные сохраняются (в отличие от памяти JS).

### Поток авторизации

```
1. Пользователь открывает любой URL
        │
        ├─ Нет токена в sessionStorage
        │       └─ requireAuth() → редирект на /pages/login.html
        │
        └─ Есть токен
                ├─ Роль совпадает с requireAuth() → страница загружается
                └─ Роль не совпадает → редирект на /pages/login.html
```

### Поток выхода

```
1. Клик "Выйти" в navbar → logout()
2. sessionStorage.clear()
3. window.location.href = '/pages/login.html'
```

### Автоматический выход при 401/403

В `api.js` функция `request()`:
```javascript
if (response.status === 401) {
    sessionStorage.clear();
    window.location.href = '/pages/login.html';
}
if (response.status === 403) {
    window.location.href = '/pages/login.html';
}
```

При устаревшем/невалидном токене бэкенд вернёт 401 → автоматический выход.

---

## 13. Жизненный цикл страницы

На примере `pages/teacher/lessons/detail.html?id=UUID`:

```
1. Браузер загружает HTML от Nginx

2. Парсинг HTML → подключение CDN (Bootstrap, AdminLTE, Font Awesome)
   → подключение /css/custom.css, /js/api.js, /js/auth.js, /js/guards.js

3. Выполнение inline <script>:

   a. requireAuth('teacher')
      │  sessionStorage не имеет 'teacher' → редирект
      └─ OK → продолжаем

   b. IIFE async () => { ... }:

      i. await loadComponents('lessons')
         ├─ fetch /components/navbar.html (параллельно)
         ├─ fetch /components/sidebar-teacher.html (параллельно)
         ├─ Вставить HTML в DOM
         ├─ api.get('/users/me') → имя пользователя
         └─ Подсветить пункт "Уроки" в меню

      ii. await loadLesson()
          ├─ const id = new URLSearchParams(window.location.search).get('id')
          ├─ api.get('/lessons/' + id) → данные урока
          ├─ api.get('/classes/' + lesson.class_id + '/students') → ученики
          ├─ api.get('/grades/?lesson_id=' + id) → оценки
          ├─ api.get('/attendances/?lesson_id=' + id) → посещаемость
          └─ Заполнить таблицы в DOM

4. Пользователь взаимодействует:
   ├─ Ввод оценки → api.post('/grades/', body) → обновление строки таблицы
   └─ Изменение посещаемости → api.patch('/attendances/' + id, body) → обновление строки
```

---

## 14. Обработка ошибок API

### 422 Validation Error (Pydantic)

Бэкенд возвращает массив ошибок в `detail`:
```json
{
    "detail": [
        {"loc": ["body", "first_name"], "type": "string_pattern_mismatch", "msg": "..."},
        {"loc": ["body", "email"], "type": "value_error", "msg": "..."}
    ]
}
```

`_formatValidationError` обрабатывает каждый элемент:
1. Из `loc` извлекает имя поля (`first_name`)
2. Из `_FIELD_LABELS` берёт название (`Имя`)
3. По `type` формирует сообщение (`Формат не соответствует требованиям`)
4. Возвращает `"Имя: Формат не соответствует требованиям"`

Все ошибки объединяются через `\n` → `showAlert(message)`.

### Типичная конструкция обработки

```javascript
document.getElementById('some-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';

    try {
        await api.post('/endpoint/', bodyData);
        showAlert('Успешно сохранено', 'success');
        setTimeout(() => window.location.href = 'index.html', 1000);
    } catch (err) {
        showAlert(err.message);       // err.message уже сформирован в api.js
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Сохранить';
    }
});
```

---

## 15. Добавление новой страницы

Порядок действий при создании новой страницы для роли (например, страница "Расписание" для учителя):

1. **Создать HTML-файл** `pages/teacher/schedule.html` по шаблону из раздела 11

2. **Подключить нужные скрипты:**
   ```html
   <script src="/js/api.js"></script>
   <script src="/js/auth.js"></script>
   <script src="/js/guards.js"></script>
   <!-- Если используется общий common.js роли -->
   <script src="/js/pages/teacher/common.js"></script>
   ```

3. **Установить guard:**
   ```javascript
   requireAuth('teacher');
   ```

4. **Загрузить компоненты** через `loadTeacherComponents('schedule')` или инлайн-функцией

5. **Добавить ссылку** в `components/sidebar-teacher.html`:
   ```html
   <li class="nav-item">
       <a href="/pages/teacher/schedule.html" class="nav-link">
           <i class="nav-icon fas fa-calendar"></i>
           <p>Расписание</p>
       </a>
   </li>
   ```

6. **Пересобрать** фронтенд-контейнер:
   ```bash
   docker compose up -d --build frontend
   ```

**Важно:** любое изменение компонентов (`sidebar-*.html`, `navbar.html`) или CSS также требует пересборки. Изменения в `.js`-файлах тоже требуют пересборки (нет hot-reload).
