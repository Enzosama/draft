# routers/__init__.py
from . import auth, posts, exams, users, rag
from . import admin_teachers, teacher_classrooms, teacher_notifications, teacher_posts

__all__ = ["auth", "posts", "exams", "users", "rag", "admin_teachers", "teacher_classrooms", "teacher_notifications", "teacher_posts"]
