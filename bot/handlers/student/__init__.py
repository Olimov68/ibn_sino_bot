from aiogram import Router
from bot.handlers.student.registration import student_reg_router
from bot.handlers.student.book_exam import student_booking_router
from bot.handlers.student.my_exams import my_exams_router
from bot.handlers.student.profile import profile_router
from bot.handlers.student.about import about_router

student_router = Router(name="student_main_router")

student_router.include_router(student_reg_router)
student_router.include_router(student_booking_router)
student_router.include_router(my_exams_router)
student_router.include_router(profile_router)
student_router.include_router(about_router)

__all__ = ["student_router"]
