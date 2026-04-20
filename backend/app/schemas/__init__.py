from app.schemas.user import (
    UserShort,
    UserCreate,
    UserUpdate,
    UserResponse,
    TeacherProfileCreate,
    TeacherProfileUpdate,
    TeacherProfileResponse,
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
)
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.schemas.class_ import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassStudentCreate,
    ClassStudentResponse,
    TeacherClassCreate,
    TeacherClassResponse,
    ParentStudentCreate,
    ParentStudentResponse,
)
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse
from app.schemas.grade import GradeCreate, GradeUpdate, GradeResponse
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse
from app.schemas.notification import NotificationCreate, NotificationResponse

__all__ = [
    "UserShort", "UserCreate", "UserUpdate", "UserResponse",
    "TeacherProfileCreate", "TeacherProfileUpdate", "TeacherProfileResponse",
    "StudentProfileCreate", "StudentProfileUpdate", "StudentProfileResponse",
    "SubjectCreate", "SubjectUpdate", "SubjectResponse",
    "ClassCreate", "ClassUpdate", "ClassResponse",
    "ClassStudentCreate", "ClassStudentResponse",
    "TeacherClassCreate", "TeacherClassResponse",
    "ParentStudentCreate", "ParentStudentResponse",
    "LessonCreate", "LessonUpdate", "LessonResponse",
    "GradeCreate", "GradeUpdate", "GradeResponse",
    "AttendanceCreate", "AttendanceUpdate", "AttendanceResponse",
    "NotificationCreate", "NotificationResponse",
]
