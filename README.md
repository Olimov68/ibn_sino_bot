# 🏥 @ibnsinoschoolbot — Haftalik Mock Imtihonlar Taqsimot Boti

**@ibnsinoschoolbot** — o'quv markazlarida haftalik mock imtihonlar (kimyo, biologiya, matematika, fizika, ingliz tili va b.) uchun o'quvchilarni xonalar va stollarga avtomatik joylashtiradigan professional Telegram bot tizimi.

---

## 🛠 Texnologiyalar to'plami (Tech Stack)

- **Til:** Python 3.11+
- **Telegram Bot Framework:** Aiogram 3.x
- **Ma'lumotlar bazasi:** PostgreSQL 16
- **ORM:** SQLAlchemy 2.0 (Async) + `asyncpg`
- **Migratsiyalar:** Alembic (Asinxron rejimda)
- **Fon rejimida rejalashtiruvchi:** APScheduler (1 kun va 2 soat oldingi eslatmalar)
- **Excel hisobotlar:** openpyxl (.xlsx davomat varaqlari)
- **Validatsiya & Sozlamalar:** Pydantic Settings
- **Testlar:** pytest + pytest-asyncio + aiosqlite

---

## 📂 Loyiha tuzilmasi

```text
ibnsinobot/
├── .env.example                  # Muhit sozlamalari namunasi
├── requirements.txt              # Python kutubxonalari
├── alembic.ini                   # Alembic konfiguratsiyasi
├── alembic/                      # Baza migratsiya skriptlari
│   ├── env.py
│   └── versions/001_initial_schema.py
├── bot/
│   ├── config.py                 # Pydantic sozlamalari (.env)
│   ├── main.py                   # Bot kirish nuqtasi (Entrypoint)
│   ├── db/                       # SQLAlchemy 2.0 baza qatlami
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/               # ORM jadvallari (Admins, Rooms, Sessions...)
│   ├── services/                 # BIZNES MANTIQ (FastAPI bilan integratsiyabop)
│   │   ├── allocation_service.py # Avtomatik joylashtirish (Retry & Concurrency)
│   │   ├── session_service.py    # Seanslar boshqaruvi
│   │   ├── student_service.py    # O'quvchi profillari
│   │   ├── location_service.py   # Manzillar
│   │   ├── room_service.py       # Xonalar va sig'imlar
│   │   ├── subject_service.py    # Fanlar
│   │   ├── report_service.py     # Statistik hisobotlar
│   │   ├── excel_service.py      # Davomat varaqalarini Excelga chiqarish
│   │   └── admin_service.py      # Adminlar boshqaruvi
│   ├── handlers/                 # Aiogram 3 handlerlari
│   │   ├── common.py             # /start va rejim almashtirish
│   │   ├── admin/                # Admin paneli (Manzillar, Xonalar, Fanlar, Seanslar...)
│   │   └── student/              # O'quvchi oqimi (Ro'yxatdan o'tish, Imtihonga yozilish...)
│   ├── keyboards/                # Emojili Reply & Inline tugmalar
│   ├── states/                   # FSM holatlari
│   ├── middlewares/              # DbSessionMiddleware va IsAdminFilter
│   ├── schedulers/               # APScheduler eslatmalari
│   └── utils/                    # Formatlash utilitalari
└── tests/                        # Pytest avtotestlari
    ├── conftest.py
    └── test_allocation_service.py
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1-qadam: Telegram Bot Token va Admin ID olish

1. Telegramda [@BotFather](https://t.me/BotFather) ga kiring, `/newbot` buyrug'i orqali yangi bot yarating va `BOT_TOKEN` ni oling.
2. O'z Telegram ID raqamingizni aniqlash uchun [@userinfobot](https://t.me/userinfobot) ga kiring.

### 2-qadam: `.env` konfiguratsiya faylini yaratish

Loyiha ildizida `.env` faylini yarating (`.env.example` dan nusxa olib):

```bash
cp .env.example .env
```

`.env` faylini ochib, parametrlarni kiriting:

```env
# Bot tokeningiz (@BotFather dan olingan)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxyz

# Adminlarning Telegram ID lari (bir nechta bo'lsa vergul bilan ajrating)
ADMIN_IDS=123456789,987654321

# Ma'lumotlar bazasi URL manzili (PostgreSQL yoki SQLite)
# PostgreSQL: postgresql+asyncpg://ibnsino:ibnsino_password@localhost:5432/ibnsino_db
# SQLite: sqlite+aiosqlite:///ibnsino.db
DATABASE_URL=sqlite+aiosqlite:///ibnsino.db
```

---

### 3-qadam: Botni ishga tushirish

Mahalliy muhitda botni ishga tushirish uchun:

1. **Virtual muhit yaratish va faollashtirish:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```

2. **Kutubxonalarni o'rnatish:**
   ```bash
   pip install -r requirements.txt
   ```

3. **PostgreSQL ulanishini `.env` da belgilash:**
   ```env
   DATABASE_URL=postgresql+asyncpg://ibnsino:ibnsino_password@localhost:5432/ibnsino_db
   ```

4. **Alembic migratsiyalarini qo'llash:**
   ```bash
   alembic upgrade head
   ```

5. **Botni ishga tushirish:**
   ```bash
   python -m bot.main
   ```

---

## 🧪 Testlarni ishga tushirish

Joylashtirish algoritmining barcha holatlarini (xona to'lishi, barcha xonalar to'lishi, bekor qilish, parallel so'rovlar) tekshirish uchun:

```bash
pytest -v
```

---

## 📱 Botdan foydalanish qo'llanmasi

### 1. Administrator uchun:
- Botga `/start` yuborganingizda Telegram ID ingiz `ADMIN_IDS` ro'yxatida bo'lsa, to'g'ridan-to'g'ri **Admin paneli** ochiladi.
- **Manzillar:** Yangi bino yoki filial qo'shish (nomi va to'liq manzili).
- **Xonalar:** Manzilni tanlab, xona nomi, stollar soni (sig'imi) va to'ldirish tartibi (`sort_order`) ni kiritish.
- **Fanlar:** Imtihon fanlarini (Kimyo, Biologiya, Matematika...) qo'shish.
- **Imtihon seanslari:** Fanni, manzilni, sana (`DD.MM.YYYY`) va vaqtni (`HH:MM`) tanlab seans yaratish.
- **Hisobot va Excel:** Seansni tanlab statistikani ko'rish hamda bitta bosishda xonalar va stollar bo'yicha davomat varaqasini (`.xlsx`) yuklab olish.
- **Xabar yuborish:** Seansga yozilgan barcha o'quvchilarga bildirishnoma yuborish.
- **Adminlar:** Boshqa xodimlarni Telegram ID orqali admin qilib qo'shish yoki olib tashlash.
- **🔙 O'quvchi rejimiga o'tish:** Botning o'quvchilar ko'ziga qanday ko'rinishini tekshirish.

### 2. O'quvchi uchun:
- Birinchi marta `/start` bosganda: Ism-familiya, telefon raqami (kontakt tugmasi orqali) va sinf (5-11) kiritiladi.
- **📝 Imtihonga yozilish:** Fan -> Sana -> Vaqt tanlanadi. Bot avtomatik bo'sh xona va stolni ajratadi va chiroyli tasdiq chekini taqdim etadi.
- **📋 Mening ro'yxatlarim:** O'quvchi o'zining barcha yozilgan imtihonlarini ko'radi va zarur bo'lsa "❌ Bekor qilish" orqali o'rnini bo'shatishi mumkin.
- **👤 Profilim:** O'z ma'lumotlarini ko'rish va tahrirlash (`✏️`).
- **⏰ Avtomatik eslatmalar:** Imtihonga 1 kun va 2 soat qolganda bot o'quvchiga o'z vaqtida kelish va hujjatlarni olish haqida avtomatik eslatma yuboradi.
