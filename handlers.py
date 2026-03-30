from datetime import date, datetime, timedelta
from collections import defaultdict

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import database as db

router = Router()

WELCOME = (
    "👋 <b>Привіт! Я твій щоденний планувальник.</b>\n\n"
    "Як це працює:\n"
    "1️⃣ Ти додаєш задачі на місяць\n"
    "2️⃣ Щоранку я сам пишу тобі що треба зробити сьогодні\n\n"
    "<b>Команди:</b>\n"
    "/add — додати задачу на конкретний день\n"
    "/today — що робити сьогодні\n"
    "/month — план на поточний місяць\n"
    "/done ID — позначити виконаною\n"
    "/delete ID — видалити задачу\n"
    "/settime HH:MM — змінити час щоденного звіту\n"
    "/help — інструкція"
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(WELCOME)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Як додавати задачі:</b>\n\n"
        "<code>/add 2026-04-01 Зустріч з клієнтом</code>\n"
        "<code>/add 2026-04-05 Відправити звіт</code>\n"
        "<code>/add 2026-04-10 Оплатити рахунок</code>\n\n"
        "Можна додати кілька задач на один день.\n\n"
        "⏰ <b>Змінити час щоденного звіту:</b>\n"
        "<code>/settime 08:30</code>\n\n"
        "За замовчуванням звіт приходить о <b>09:00</b>."
    )


@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    if not command.args:
        await message.answer(
            "❌ Вкажи дату і текст:\n"
            "<code>/add YYYY-MM-DD Текст задачі</code>\n\n"
            "Приклад:\n"
            "<code>/add 2026-04-03 Зателефонувати партнеру</code>"
        )
        return

    parts = command.args.split(" ", 1)
    if len(parts) < 2:
        await message.answer(
            "❌ Потрібен текст після дати.\n"
            "Приклад: <code>/add 2026-04-03 Текст</code>"
        )
        return

    date_str = parts[0].strip()
    text = parts[1].strip()

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await message.answer(
            "❌ Неправильна дата. Формат: <code>YYYY-MM-DD</code>\n"
            "Приклад: <code>2026-04-03</code>"
        )
        return

    task_id = await db.add_task(message.from_user.id, date_str, text)
    await message.answer(
        f"✅ Додано!\n\n"
        f"🆔 <b>#{task_id}</b>\n"
        f"📅 {date_str}\n"
        f"📝 {text}"
    )


@router.message(Command("today"))
async def cmd_today(message: Message):
    today = date.today().strftime("%Y-%m-%d")
    tasks = await db.get_tasks_for_date(message.from_user.id, today)
    report_time = await db.get_report_time(message.from_user.id)
    text = build_daily_report(today, tasks, report_time)
    await message.answer(text)


@router.message(Command("month"))
async def cmd_month(message: Message, command: CommandObject):
    if command.args:
        try:
            datetime.strptime(command.args.strip(), "%Y-%m")
            year_month = command.args.strip()
        except ValueError:
            await message.answer("❌ Формат: <code>/month 2026-05</code>")
            return
    else:
        year_month = date.today().strftime("%Y-%m")

    tasks = await db.get_month_tasks(message.from_user.id, year_month)

    if not tasks:
        await message.answer(
            f"📭 На {year_month} задач немає.\n\n"
            f"Додай: <code>/add {year_month}-01 Текст</code>"
        )
        return

    grouped = defaultdict(list)
    for t in tasks:
        grouped[t["task_date"]].append(t)

    lines = [f"📅 <b>План на {year_month}:</b>\n"]
    for day_date in sorted(grouped.keys()):
        day_tasks = grouped[day_date]
        dt = datetime.strptime(day_date, "%Y-%m-%d")
        weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"][dt.weekday()]
        day_num = dt.strftime("%d")
        lines.append(f"\n<b>{day_num} ({weekday}):</b>")
        for t in day_tasks:
            icon = "✅" if t["done"] else "🔲"
            lines.append(f"  {icon} #{t['id']} {t['text']}")

    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    lines.append(f"\n📊 Виконано: {done}/{total}")

    await message.answer("\n".join(lines))


@router.message(Command("done"))
async def cmd_done(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.answer("❌ Вкажи ID: <code>/done 5</code>")
        return

    success = await db.mark_done(int(command.args.strip()), message.from_user.id)
    if success:
        await message.answer(f"✅ Задача #{command.args.strip()} виконана! Молодець 💪")
    else:
        await message.answer(f"❌ Задача #{command.args.strip()} не знайдена.")


@router.message(Command("delete"))
async def cmd_delete(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.answer("❌ Вкажи ID: <code>/delete 5</code>")
        return

    success = await db.delete_task(int(command.args.strip()), message.from_user.id)
    if success:
        await message.answer(f"🗑 Задача #{command.args.strip()} видалена.")
    else:
        await message.answer(f"❌ Задача #{command.args.strip()} не знайдена.")


@router.message(Command("settime"))
async def cmd_settime(message: Message, command: CommandObject):
    if not command.args:
        current = await db.get_report_time(message.from_user.id)
        await message.answer(
            f"⏰ Зараз звіт приходить о <b>{current}</b>\n\n"
            "Щоб змінити: <code>/settime 08:30</code>"
        )
        return

    try:
        datetime.strptime(command.args.strip(), "%H:%M")
    except ValueError:
        await message.answer(
            "❌ Формат: <code>HH:MM</code>\n"
            "Приклад: <code>/settime 08:30</code>"
        )
        return

    await db.set_report_time(message.from_user.id, command.args.strip())
    await message.answer(f"✅ Щоденний звіт тепер о <b>{command.args.strip()}</b>")


def build_daily_report(today_str: str, tasks: list, report_time: str = "09:00") -> str:
    dt = datetime.strptime(today_str, "%Y-%m-%d")
    weekdays = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
    weekday_name = weekdays[dt.weekday()]
    day_formatted = dt.strftime("%d.%m.%Y")

    if not tasks:
        return (
            f"☀️ <b>{weekday_name}, {day_formatted}</b>\n\n"
            "📭 На сьогодні задач немає.\n\n"
            "Додай нові: /add"
        )

    pending = [t for t in tasks if not t["done"]]
    done = [t for t in tasks if t["done"]]

    lines = [f"☀️ <b>{weekday_name}, {day_formatted}</b>\n"]
    lines.append(f"📋 <b>Твій план на сьогодні ({len(tasks)} задач):</b>\n")

    for t in pending:
        lines.append(f"🔲 #{t['id']} {t['text']}")

    if done:
        lines.append("\n<i>Вже виконано:</i>")
        for t in done:
            lines.append(f"✅ #{t['id']} {t['text']}")

    if pending:
        lines.append(f"\n💪 Вперед! Позначай виконані: <code>/done ID</code>")
    else:
        lines.append(f"\n🎉 Всі задачі виконані! Відмінний день!")

    return "\n".join(lines)
