const API_URL = 'http://localhost:8000';

const _FIELD_LABELS = {
    first_name:    'Имя',
    last_name:     'Фамилия',
    middle_name:   'Отчество',
    email:         'Email',
    password:      'Пароль',
    role:          'Роль',
    name:          'Название',
    academic_year: 'Учебный год',
    value:         'Оценка',
    comment:       'Комментарий',
    date:          'Дата',
    topic:         'Тема',
    title:         'Заголовок',
    body:          'Текст',
    date_of_birth: 'Дата рождения',
    record_number: 'Номер личного дела',
    status:        'Статус',
    subject_id:    'Предмет',
    class_id:      'Класс',
    teacher_id:    'Учитель',
    student_id:    'Ученик',
    recipient_id:  'Получатель',
};

function _formatValidationError(e) {
    const field = Array.isArray(e.loc)
        ? e.loc.find(l => typeof l === 'string' && l !== 'body')
        : null;
    const label = field ? (_FIELD_LABELS[field] || field) : null;

    const ctx = e.ctx || {};
    let msg;

    switch (e.type) {
        case 'missing':                  msg = 'Обязательное поле'; break;
        case 'string_too_short':         msg = `Минимум ${ctx.min_length} символов`; break;
        case 'string_too_long':          msg = `Максимум ${ctx.max_length} символов`; break;
        case 'greater_than_equal':       msg = `Не менее ${ctx.ge}`; break;
        case 'less_than_equal':          msg = `Не более ${ctx.le}`; break;
        case 'greater_than':             msg = `Должно быть больше ${ctx.gt}`; break;
        case 'less_than':                msg = `Должно быть меньше ${ctx.lt}`; break;
        case 'int_parsing':              msg = 'Введите целое число'; break;
        case 'int_type':                 msg = 'Должно быть числом'; break;
        case 'string_type':              msg = 'Должно быть строкой'; break;
        case 'bool_type':                msg = 'Должно быть булевым значением'; break;
        case 'uuid_parsing':             msg = 'Неверный формат ID'; break;
        case 'value_error':
        case 'string_pattern_mismatch':
        default:
            msg = (e.msg || 'Неверное значение').replace(/^Value error,\s*/i, '');
    }

    return label ? `${label}: ${msg}` : msg;
}

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
        const detail = error.detail;
        let message;
        if (!detail) {
            message = 'Ошибка сервера';
        } else if (typeof detail === 'string') {
            message = detail;
        } else if (Array.isArray(detail)) {
            message = detail.map(_formatValidationError).join('\n');
        } else {
            message = JSON.stringify(detail);
        }
        throw new Error(message);
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
