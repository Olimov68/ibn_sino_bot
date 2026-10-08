import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.db.session import async_session_maker, engine
from bot.handlers import main_router
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.schedulers.reminder_service import setup_scheduler
from bot.services.admin_service import AdminService
from bot.services.channel_service import ChannelService

# Log konfiguratsiyasi
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ibnsinobot")


async def main() -> None:
    """Botni ishga tushiruvchi asosiy asinxron funksiya"""
    if not settings.BOT_TOKEN:
        logger.error("XATOLIK: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, tekshiring.")
        sys.exit(1)

    logger.info("Bot ishga tushirilmoqda...")

    # Bot va Dispatcher obyektlari
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Baza jadvallarini yaratish (agar mavjud bo'lmasa)
    async with engine.begin() as conn:
        from bot.db.models import Base
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Ma'lumotlar bazasi jadvallari tayyor.")

    # Boshlang'ich majburiy kanal va adminlarni tekshirish hamda qo'shish
    async with async_session_maker() as session:
        await ChannelService.init_default_channel(session)
        await AdminService.init_default_admins(session)

    # Middleware: barcha so'rovlarga avtomatik DB sessiya ulash
    dp.update.outer_middleware(DbSessionMiddleware())

    # Majburiy kanal obunasini tekshiruvchi middleware
    sub_middleware = SubscriptionMiddleware()
    dp.message.outer_middleware(sub_middleware)
    dp.callback_query.outer_middleware(sub_middleware)

    # Routerlarni ulash
    dp.include_router(main_router)

    # APScheduler (Eslatmalar xizmati)
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("APScheduler eslatmalar xizmati muvaffaqiyatli ishga tushirildi.")

    try:
        # Eski to'planib qolgan xabarlarni tozalash va pollingni boshlash
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Telegram Polling faollashtirildi. Bot muvaffaqiyatli ishlamoqda!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Bot to'xtatilmoqda...")
        scheduler.shutdown(wait=False)
        await engine.dispose()
        await bot.session.close()
        logger.info("Barcha resurslar xavfsiz yopildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
