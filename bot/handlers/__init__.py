from aiogram import Router
from bot.handlers.admin import admin_router
from bot.handlers.common import common_router
from bot.handlers.student import student_router

main_router = Router(name="main_router")

# Routerlarni tartib bo'yicha ulash:
# 1. common_router (/start va rejim o'zgartirish)
# 2. admin_router (Admin paneli amallari)
# 3. student_router (O'quvchi amallari)
main_router.include_router(common_router)
main_router.include_router(admin_router)
main_router.include_router(student_router)

__all__ = ["main_router", "admin_router", "student_router", "common_router"]
