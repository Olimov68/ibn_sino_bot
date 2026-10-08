import datetime


def format_date(d: datetime.date) -> str:
    """Sanani DD.MM.YYYY formatida ko'rsatish"""
    return d.strftime("%d.%m.%Y")


def format_time(t: datetime.time) -> str:
    """Vaqtni HH:MM formatida ko'rsatish"""
    return t.strftime("%H:%M")


def format_phone(phone: str) -> str:
    """Telefon raqamini chiroyli ko'rsatish"""
    if len(phone) == 13 and phone.startswith("+998"):
        return f"+998 ({phone[4:6]}) {phone[6:9]}-{phone[9:11]}-{phone[11:13]}"
    return phone
