#!/usr/bin/env bash
# =============================================================
#  Зурнал — Backend API Test Suite
#  Тестирует каждый эндпоинт. Созданные данные удаляются.
#
#  Использование:
#    ./test/test_api.sh [BASE_URL] [ADMIN_EMAIL] [ADMIN_PASSWORD]
#
#  Пример:
#    ./test/test_api.sh http://localhost:8000 admin@admin.com 12345678
# =============================================================

BASE_URL="${1:-http://localhost:8000}"
ADMIN_EMAIL="${2:-admin@admin.com}"
ADMIN_PASS="${3:-12345678}"

# Цвета
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# Счётчики
PASS=0; FAIL=0
declare -a FAILED_TESTS=()

pass() { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)) || true; }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)) || true; FAILED_TESTS+=("$1"); }
section() { echo -e "\n${CYAN}${BOLD}▶ $1${NC}"; }

# ID для очистки
CLEANUP_NOTIF=""
CLEANUP_ATTEND=""
CLEANUP_GRADE=""
CLEANUP_LESSON=""
CLEANUP_CLASS=""
CLEANUP_PARENT=""
CLEANUP_STUDENT=""
CLEANUP_TEACHER=""
CLEANUP_SUBJECT=""
ADMIN_TOKEN=""
CLEANED=0

# Очистка
do_cleanup() {
    [[ $CLEANED -eq 1 ]] && return
    CLEANED=1
    [[ -z "$ADMIN_TOKEN" ]] && return

    section "ОЧИСТКА"

    _del() {
        local label="$1" id="$2" path="$3"
        [[ -z "$id" ]] && return
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL$path/$id" \
            -H "Authorization: Bearer $ADMIN_TOKEN")
        if [[ "$code" == "204" || "$code" == "404" ]]; then
            pass "cleanup: $label"
        else
            fail "cleanup: $label [HTTP $code]"
        fi
    }

    _del "уведомление"  "$CLEANUP_NOTIF"    "/notifications"
    _del "посещаемость" "$CLEANUP_ATTEND"   "/attendances"
    _del "оценка"       "$CLEANUP_GRADE"    "/grades"
    _del "урок"         "$CLEANUP_LESSON"   "/lessons"
    _del "класс"        "$CLEANUP_CLASS"    "/classes"
    _del "родитель"     "$CLEANUP_PARENT"   "/users"
    _del "ученик"       "$CLEANUP_STUDENT"  "/users"
    _del "учитель"      "$CLEANUP_TEACHER"  "/users"
    _del "предмет"      "$CLEANUP_SUBJECT"  "/subjects"
}
trap do_cleanup EXIT

# HTTP-хелпер
HTTP_BODY=""; HTTP_CODE=""

call() {
    local method="$1" path="$2" data="${3:-}" token="${4:-$ADMIN_TOKEN}"
    local args=(-s -w "\n%{http_code}" -X "$method" "$BASE_URL$path"
        -H "Content-Type: application/json")
    [[ -n "$token" ]] && args+=(-H "Authorization: Bearer $token")
    [[ -n "$data" ]] && args+=(-d "$data")
    local resp
    resp=$(curl "${args[@]}")
    HTTP_BODY=$(echo "$resp" | sed '$d')
    HTTP_CODE=$(echo "$resp" | tail -1)
}

chk() {
    local name="$1" exp="$2"
    if [[ "$HTTP_CODE" == "$exp" ]]; then
        pass "$name"
    else
        fail "$name [ожидался $exp, получен $HTTP_CODE]"
        # Вывести тело ответа если есть полезная информация
        [[ -n "$HTTP_BODY" && "$HTTP_BODY" != "null" ]] && \
            echo -e "      ${YELLOW}$(echo "$HTTP_BODY" | jq -r '.detail // empty' 2>/dev/null)${NC}"
    fi
}

# Проверка зависимостей
if ! command -v jq &>/dev/null; then
    echo -e "${RED}ОШИБКА: jq не установлен.${NC}"
    echo "  macOS:  brew install jq"
    echo "  Ubuntu: apt install jq"
    exit 1
fi
if ! command -v curl &>/dev/null; then
    echo -e "${RED}ОШИБКА: curl не установлен.${NC}"
    exit 1
fi

echo ""
echo -e "${BOLD}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     Зурнал — Backend API Test Suite      ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════╝${NC}"
echo "  URL:   $BASE_URL"
echo "  Admin: $ADMIN_EMAIL"
echo ""

# =============================================================
#  AUTH
# =============================================================
section "AUTH"

resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login" \
    -F "username=$ADMIN_EMAIL" -F "password=$ADMIN_PASS")
HTTP_BODY=$(echo "$resp" | sed '$d')
HTTP_CODE=$(echo "$resp" | tail -1)
chk "POST /auth/login" "200"

if [[ "$HTTP_CODE" != "200" ]]; then
    echo -e "${RED}Авторизация провалилась — тесты остановлены.${NC}"
    echo "Ответ: $HTTP_BODY"
    exit 1
fi
ADMIN_TOKEN=$(echo "$HTTP_BODY" | jq -r '.access_token')

# Неверные данные → 401
resp=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login" \
    -F "username=nobody@no.no" -F "password=wrongpassword123")
HTTP_CODE=$(echo "$resp" | tail -1)
chk "POST /auth/login (неверные данные → 401)" "401"

# =============================================================
#  PRE-CLEANUP — удалить остатки от упавших предыдущих запусков
# =============================================================
section "PRE-CLEANUP (остатки прошлых запусков)"

call GET /users/
if [[ "$HTTP_CODE" == "200" ]]; then
    stale_ids=$(echo "$HTTP_BODY" | jq -r '[.[] | select(.email | test("^t_(teacher|student|parent)_[0-9]+@test\\.ru$")) | .id] | .[]' 2>/dev/null)
    if [[ -n "$stale_ids" ]]; then
        while IFS= read -r sid; do
            curl -s -o /dev/null -X DELETE "$BASE_URL/users/$sid" -H "Authorization: Bearer $ADMIN_TOKEN"
        done <<< "$stale_ids"
        echo "  Удалены устаревшие тест-пользователи"
    fi
fi

call GET /subjects/
if [[ "$HTTP_CODE" == "200" ]]; then
    old_subj=$(echo "$HTTP_BODY" | jq -r '.[] | select(.name=="Тест-АПИ") | .id' 2>/dev/null)
    if [[ -n "$old_subj" ]]; then
        curl -s -o /dev/null -X DELETE "$BASE_URL/subjects/$old_subj" -H "Authorization: Bearer $ADMIN_TOKEN"
        echo "  Удалён устаревший тест-предмет"
    fi
fi

# =============================================================
#  USERS — создание
# =============================================================
section "USERS — создание"

call GET /users/me
chk "GET /users/me" "200"
ADMIN_ID=$(echo "$HTTP_BODY" | jq -r '.id')

call GET /users/
chk "GET /users/" "200"

TS=$(date +%s)

# Создать учителя
call POST /users/ \
    "{\"email\":\"t_teacher_${TS}@test.ru\",\"password\":\"TestPass123\",\"role\":\"teacher\",\"first_name\":\"Иван\",\"last_name\":\"Тестов\"}"
chk "POST /users/ (teacher)" "201"
[[ "$HTTP_CODE" == "201" ]] && CLEANUP_TEACHER=$(echo "$HTTP_BODY" | jq -r '.id')

# Создать ученика
call POST /users/ \
    "{\"email\":\"t_student_${TS}@test.ru\",\"password\":\"TestPass123\",\"role\":\"student\",\"first_name\":\"Петр\",\"last_name\":\"Ученикин\"}"
chk "POST /users/ (student)" "201"
[[ "$HTTP_CODE" == "201" ]] && CLEANUP_STUDENT=$(echo "$HTTP_BODY" | jq -r '.id')

# Создать родителя
call POST /users/ \
    "{\"email\":\"t_parent_${TS}@test.ru\",\"password\":\"TestPass123\",\"role\":\"parent\",\"first_name\":\"Ольга\",\"last_name\":\"Родителева\"}"
chk "POST /users/ (parent)" "201"
[[ "$HTTP_CODE" == "201" ]] && CLEANUP_PARENT=$(echo "$HTTP_BODY" | jq -r '.id')

# Дублирующий email → 409
call POST /users/ \
    "{\"email\":\"t_teacher_${TS}@test.ru\",\"password\":\"TestPass123\",\"role\":\"teacher\",\"first_name\":\"Иван\",\"last_name\":\"Тестов\"}"
chk "POST /users/ (дубль email → 409)" "409"

# =============================================================
#  USERS — чтение и обновление
# =============================================================
section "USERS — чтение и обновление"

[[ -n "$CLEANUP_TEACHER" ]] && {
    call GET /users/$CLEANUP_TEACHER
    chk "GET /users/{id}" "200"

    call PATCH /users/$CLEANUP_TEACHER '{"first_name":"Иван"}'
    chk "PATCH /users/{id}" "200"
}

# Несуществующий ID → 404
call GET /users/00000000-0000-0000-0000-000000000000
chk "GET /users/{id} (несуществующий → 404)" "404"

# =============================================================
#  USERS — профили
# =============================================================
section "USERS — профили"

[[ -n "$CLEANUP_STUDENT" ]] && {
    call POST /users/$CLEANUP_STUDENT/student-profile '{"date_of_birth":"2005-06-15"}'
    chk "POST /users/{id}/student-profile" "201"

    call PATCH /users/$CLEANUP_STUDENT/student-profile '{"date_of_birth":"2005-01-01"}'
    chk "PATCH /users/{id}/student-profile" "200"

    # Повторное создание → 409
    call POST /users/$CLEANUP_STUDENT/student-profile '{"date_of_birth":"2005-01-01"}'
    chk "POST /users/{id}/student-profile (дубль → 409)" "409"
}

# =============================================================
#  SUBJECTS
# =============================================================
section "SUBJECTS"

call GET /subjects/
chk "GET /subjects/" "200"

# Создать предмет (имя только кириллица+дефис+пробел)
call POST /subjects/ '{"name":"Тест-АПИ"}'
if [[ "$HTTP_CODE" == "409" ]]; then
    # Предмет уже есть — найти его ID
    call GET /subjects/
    CLEANUP_SUBJECT=$(echo "$HTTP_BODY" | jq -r '.[] | select(.name=="Тест-АПИ") | .id')
    [[ -n "$CLEANUP_SUBJECT" ]] && pass "POST /subjects/ (уже существует, ID найден)" \
                                 || fail "POST /subjects/ [409 и не найден]"
else
    chk "POST /subjects/" "201"
    [[ "$HTTP_CODE" == "201" ]] && CLEANUP_SUBJECT=$(echo "$HTTP_BODY" | jq -r '.id')
fi

[[ -n "$CLEANUP_SUBJECT" ]] && {
    call GET /subjects/$CLEANUP_SUBJECT
    chk "GET /subjects/{id}" "200"

    call PATCH /subjects/$CLEANUP_SUBJECT '{"name":"Тест-АПИ-два"}'
    chk "PATCH /subjects/{id}" "200"

    # Вернуть оригинальное имя (для повторных запусков)
    call PATCH /subjects/$CLEANUP_SUBJECT '{"name":"Тест-АПИ"}'
}

# Создать профиль учителя (нужен subject_id)
[[ -n "$CLEANUP_TEACHER" && -n "$CLEANUP_SUBJECT" ]] && {
    call POST /users/$CLEANUP_TEACHER/teacher-profile \
        "{\"subject_id\":\"$CLEANUP_SUBJECT\"}"
    chk "POST /users/{id}/teacher-profile" "201"

    call PATCH /users/$CLEANUP_TEACHER/teacher-profile \
        "{\"subject_id\":\"$CLEANUP_SUBJECT\"}"
    chk "PATCH /users/{id}/teacher-profile" "200"

    # Повторное создание → 409
    call POST /users/$CLEANUP_TEACHER/teacher-profile \
        "{\"subject_id\":\"$CLEANUP_SUBJECT\"}"
    chk "POST /users/{id}/teacher-profile (дубль → 409)" "409"
}

# =============================================================
#  CLASSES
# =============================================================
section "CLASSES"

call GET /classes/
chk "GET /classes/" "200"

# year=2099 — малый риск коллизии
call POST /classes/ '{"name":"9А","academic_year":2099}'
if [[ "$HTTP_CODE" == "409" ]]; then
    call GET /classes/
    CLEANUP_CLASS=$(echo "$HTTP_BODY" | jq -r '.[] | select(.name=="9А" and .academic_year==2099) | .id')
    [[ -n "$CLEANUP_CLASS" ]] && pass "POST /classes/ (уже существует, ID найден)" \
                               || fail "POST /classes/ [409 и не найден]"
else
    chk "POST /classes/" "201"
    [[ "$HTTP_CODE" == "201" ]] && CLEANUP_CLASS=$(echo "$HTTP_BODY" | jq -r '.id')
fi

[[ -n "$CLEANUP_CLASS" ]] && {
    call GET /classes/$CLEANUP_CLASS
    chk "GET /classes/{id}" "200"

    call PATCH /classes/$CLEANUP_CLASS '{"academic_year":2099}'
    chk "PATCH /classes/{id}" "200"
}

# Прикрепить учителя к классу
[[ -n "$CLEANUP_CLASS" && -n "$CLEANUP_TEACHER" ]] && {
    call POST /classes/$CLEANUP_CLASS/teachers \
        "{\"teacher_id\":\"$CLEANUP_TEACHER\",\"class_id\":\"$CLEANUP_CLASS\"}"
    chk "POST /classes/{id}/teachers" "201"

    call GET /classes/$CLEANUP_CLASS/teachers
    chk "GET /classes/{id}/teachers" "200"

    # Дубль → 409
    call POST /classes/$CLEANUP_CLASS/teachers \
        "{\"teacher_id\":\"$CLEANUP_TEACHER\",\"class_id\":\"$CLEANUP_CLASS\"}"
    chk "POST /classes/{id}/teachers (дубль → 409)" "409"
}

# Добавить ученика в класс
[[ -n "$CLEANUP_CLASS" && -n "$CLEANUP_STUDENT" ]] && {
    call POST /classes/$CLEANUP_CLASS/students \
        "{\"class_id\":\"$CLEANUP_CLASS\",\"student_id\":\"$CLEANUP_STUDENT\",\"academic_year\":2099}"
    chk "POST /classes/{id}/students" "201"

    call GET /classes/$CLEANUP_CLASS/students
    chk "GET /classes/{id}/students" "200"

    # Дубль → 409
    call POST /classes/$CLEANUP_CLASS/students \
        "{\"class_id\":\"$CLEANUP_CLASS\",\"student_id\":\"$CLEANUP_STUDENT\",\"academic_year\":2099}"
    chk "POST /classes/{id}/students (дубль → 409)" "409"
}

# Удалить ученика из класса и снова добавить
[[ -n "$CLEANUP_CLASS" && -n "$CLEANUP_STUDENT" ]] && {
    call DELETE /classes/$CLEANUP_CLASS/students/$CLEANUP_STUDENT
    chk "DELETE /classes/{id}/students/{student_id}" "204"

    # Снова добавить — нужен для уроков/оценок/посещаемости
    call POST /classes/$CLEANUP_CLASS/students \
        "{\"class_id\":\"$CLEANUP_CLASS\",\"student_id\":\"$CLEANUP_STUDENT\",\"academic_year\":2099}"
}

# Открепить учителя и снова прикрепить
[[ -n "$CLEANUP_CLASS" && -n "$CLEANUP_TEACHER" ]] && {
    call DELETE /classes/$CLEANUP_CLASS/teachers/$CLEANUP_TEACHER
    chk "DELETE /classes/{id}/teachers/{teacher_id}" "204"

    # Снова прикрепить
    call POST /classes/$CLEANUP_CLASS/teachers \
        "{\"teacher_id\":\"$CLEANUP_TEACHER\",\"class_id\":\"$CLEANUP_CLASS\"}"
}

# Родитель ↔ ученик
[[ -n "$CLEANUP_PARENT" && -n "$CLEANUP_STUDENT" ]] && {
    call POST /users/parents/$CLEANUP_PARENT/children/$CLEANUP_STUDENT '{}'
    chk "POST /users/parents/{pid}/children/{sid}" "201"

    call DELETE /users/parents/$CLEANUP_PARENT/children/$CLEANUP_STUDENT
    chk "DELETE /users/parents/{pid}/children/{sid}" "204"

    # Повторное удаление → 404
    call DELETE /users/parents/$CLEANUP_PARENT/children/$CLEANUP_STUDENT
    chk "DELETE /users/parents/{pid}/children/{sid} (несуществующий → 404)" "404"
}

# =============================================================
#  LESSONS
# =============================================================
section "LESSONS"

call GET /lessons/
chk "GET /lessons/" "200"

TODAY=$(date -v+1d +%Y-%m-%d 2>/dev/null || date -d "tomorrow" +%Y-%m-%d)
[[ -n "$CLEANUP_CLASS" && -n "$CLEANUP_TEACHER" && -n "$CLEANUP_SUBJECT" ]] && {
    call POST /lessons/ \
        "{\"class_id\":\"$CLEANUP_CLASS\",\"teacher_id\":\"$CLEANUP_TEACHER\",\"subject_id\":\"$CLEANUP_SUBJECT\",\"date\":\"$TODAY\",\"topic\":\"Тестовый урок\"}"
    chk "POST /lessons/" "201"
    [[ "$HTTP_CODE" == "201" ]] && CLEANUP_LESSON=$(echo "$HTTP_BODY" | jq -r '.id')
}

[[ -n "$CLEANUP_LESSON" ]] && {
    call GET /lessons/$CLEANUP_LESSON
    chk "GET /lessons/{id}" "200"

    call GET "/lessons/?class_id=$CLEANUP_CLASS"
    chk "GET /lessons/?class_id={id}" "200"

    call PATCH /lessons/$CLEANUP_LESSON '{"topic":"Обновлённая тема"}'
    chk "PATCH /lessons/{id}" "200"
}

# =============================================================
#  GRADES
# =============================================================
section "GRADES"

call GET /grades/
chk "GET /grades/" "200"

[[ -n "$CLEANUP_LESSON" && -n "$CLEANUP_STUDENT" ]] && {
    call POST /grades/ \
        "{\"lesson_id\":\"$CLEANUP_LESSON\",\"student_id\":\"$CLEANUP_STUDENT\",\"value\":5}"
    chk "POST /grades/" "201"
    [[ "$HTTP_CODE" == "201" ]] && CLEANUP_GRADE=$(echo "$HTTP_BODY" | jq -r '.id')

    # Дубль → 409
    call POST /grades/ \
        "{\"lesson_id\":\"$CLEANUP_LESSON\",\"student_id\":\"$CLEANUP_STUDENT\",\"value\":3}"
    chk "POST /grades/ (дубль → 409)" "409"
}

[[ -n "$CLEANUP_GRADE" ]] && {
    call GET /grades/$CLEANUP_GRADE
    chk "GET /grades/{id}" "200"

    call GET "/grades/?lesson_id=$CLEANUP_LESSON"
    chk "GET /grades/?lesson_id={id}" "200"

    call PATCH /grades/$CLEANUP_GRADE '{"value":4}'
    chk "PATCH /grades/{id}" "200"
}

# =============================================================
#  ATTENDANCES
# =============================================================
section "ATTENDANCES"

call GET /attendances/
chk "GET /attendances/" "200"

[[ -n "$CLEANUP_LESSON" && -n "$CLEANUP_STUDENT" ]] && {
    call POST /attendances/ \
        "{\"lesson_id\":\"$CLEANUP_LESSON\",\"student_id\":\"$CLEANUP_STUDENT\",\"status\":\"present\"}"
    chk "POST /attendances/" "201"
    [[ "$HTTP_CODE" == "201" ]] && CLEANUP_ATTEND=$(echo "$HTTP_BODY" | jq -r '.id')

    # Дубль → 409
    call POST /attendances/ \
        "{\"lesson_id\":\"$CLEANUP_LESSON\",\"student_id\":\"$CLEANUP_STUDENT\",\"status\":\"absent\"}"
    chk "POST /attendances/ (дубль → 409)" "409"
}

[[ -n "$CLEANUP_ATTEND" ]] && {
    call GET /attendances/$CLEANUP_ATTEND
    chk "GET /attendances/{id}" "200"

    call GET "/attendances/?lesson_id=$CLEANUP_LESSON"
    chk "GET /attendances/?lesson_id={id}" "200"

    call PATCH /attendances/$CLEANUP_ATTEND '{"status":"late"}'
    chk "PATCH /attendances/{id}" "200"
}

# =============================================================
#  NOTIFICATIONS
# =============================================================
section "NOTIFICATIONS"

call GET /notifications/
chk "GET /notifications/" "200"

call GET '/notifications/?unread_only=true'
chk "GET /notifications/?unread_only=true" "200"

call POST /notifications/ \
    "{\"recipient_id\":\"$ADMIN_ID\",\"title\":\"Тест уведомления\",\"body\":\"Тестовое тело уведомления для проверки\"}"
chk "POST /notifications/" "201"
[[ "$HTTP_CODE" == "201" ]] && CLEANUP_NOTIF=$(echo "$HTTP_BODY" | jq -r '.id')

[[ -n "$CLEANUP_NOTIF" ]] && {
    call GET /notifications/$CLEANUP_NOTIF
    chk "GET /notifications/{id}" "200"

    call PATCH /notifications/$CLEANUP_NOTIF/read
    chk "PATCH /notifications/{id}/read" "200"

    # Повторное прочтение → 200 (идемпотентно)
    call PATCH /notifications/$CLEANUP_NOTIF/read
    chk "PATCH /notifications/{id}/read (повтор → 200)" "200"
}

# =============================================================
#  GUARDS — запросы без токена → 403
# =============================================================
section "AUTH GUARDS (без токена → 403)"

declare -a GUARDED=(
    "GET /users/"
    "GET /users/me"
    "GET /subjects/"
    "GET /classes/"
    "GET /lessons/"
    "GET /grades/"
    "GET /attendances/"
    "GET /notifications/"
)
for ep in "${GUARDED[@]}"; do
    method="${ep%% *}"; path="${ep#* }"
    code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$path")
    HTTP_CODE="$code"
    chk "Нет токена → 403: $method $path" "403"
done

# =============================================================
#  Запуск очистки и итоги
# =============================================================
do_cleanup

TOTAL=$((PASS + FAIL))
echo ""
echo -e "${BOLD}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║              ИТОГИ ТЕСТОВ                ║${NC}"
echo -e "${BOLD}╠═══════════════════════════════════════════╣${NC}"
printf "${BOLD}║${NC}  %-42s${BOLD}║${NC}\n" "Всего:   $TOTAL"
printf "${BOLD}║${NC}  ${GREEN}%-42s${NC}${BOLD}║${NC}\n" "Прошло:  $PASS ✓"
if [[ $FAIL -gt 0 ]]; then
    printf "${BOLD}║${NC}  ${RED}%-42s${NC}${BOLD}║${NC}\n" "Упало:   $FAIL ✗"
else
    printf "${BOLD}║${NC}  %-42s${BOLD}║${NC}\n" "Упало:   $FAIL ✗"
fi
echo -e "${BOLD}╚═══════════════════════════════════════════╝${NC}"

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo -e "${RED}${BOLD}Провалившиеся тесты:${NC}"
    for t in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}✗${NC} $t"
    done
    exit 1
fi

echo -e "\n${GREEN}${BOLD}Все тесты прошли успешно!${NC}"
exit 0
