import logging
from datetime import date, datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import database as db
from config import settings
from handlers import build_daily_report

logger = logging.getLogger(__name__)
TZ = pytz.timezone(settings.TIMEZONE)


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)

    scheduler.add_job(
        check_and_send_reports,
        trigger="cron",
        minute="*",
        args=[bot],
        id="daily_reports",
        replace_existing=True,
    )

    return scheduler


async def check_and_send_reports(bot: Bot):
    now = datetime.now(TZ)
    current_time = now.strftime("%H:%M")
    today_str = date.today().strftime("%Y-%m-%d")

    user_ids = await db.get_all_active_users()

    for user_id in user_ids:
        report_time = await db.get_report_time(user_id)

        if report_time != current_time:
            continue

        tasks = await db.get_tasks_for_date(user_id, today_str)
        text = build_daily_report(today_str, tasks, report_time)

        try:
            await bot.send_message(chat_id=user_id, text=text)
            logger.info(f"Звіт відправлено user_id={user_id} о {current_time}")
        except Exception as e:
            logger.error(f"Помилка відправки user_id={user_id}: {e}")
