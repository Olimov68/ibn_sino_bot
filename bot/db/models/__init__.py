from bot.db.base import Base
from bot.db.models.admin import Admin
from bot.db.models.location import Location
from bot.db.models.room import Room
from bot.db.models.subject import Subject
from bot.db.models.session import ExamSession
from bot.db.models.student import Student
from bot.db.models.registration import Registration
from bot.db.models.channel import MandatoryChannel

__all__ = [
    "Base",
    "Admin",
    "Location",
    "Room",
    "Subject",
    "ExamSession",
    "Student",
    "Registration",
    "MandatoryChannel",
]
