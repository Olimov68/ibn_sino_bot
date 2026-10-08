from aiogram import Router
from bot.handlers.admin.menu import admin_menu_router
from bot.handlers.admin.locations import admin_locations_router
from bot.handlers.admin.rooms import admin_rooms_router
from bot.handlers.admin.subjects import admin_subjects_router
from bot.handlers.admin.sessions import admin_sessions_router
from bot.handlers.admin.reports import admin_reports_router
from bot.handlers.admin.broadcast import admin_broadcast_router
from bot.handlers.admin.admins import admin_management_router
from bot.handlers.admin.channels import admin_channels_router

admin_router = Router(name="admin_main_router")

admin_router.include_router(admin_menu_router)
admin_router.include_router(admin_locations_router)
admin_router.include_router(admin_rooms_router)
admin_router.include_router(admin_subjects_router)
admin_router.include_router(admin_sessions_router)
admin_router.include_router(admin_reports_router)
admin_router.include_router(admin_broadcast_router)
admin_router.include_router(admin_management_router)
admin_router.include_router(admin_channels_router)

__all__ = ["admin_router"]
