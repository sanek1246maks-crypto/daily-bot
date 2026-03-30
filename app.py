import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database import init_db
from handlers import router
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(router)

    scheduler = start_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    logger.info("Bot is starting...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
