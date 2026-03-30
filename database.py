import aiosqlite
from config import settings

DB = settings.DATABASE_URL


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                task_date   TEXT NOT NULL,
                text        TEXT NOT NULL,
                done        INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id     INTEGER PRIMARY KEY,
                report_time TEXT NOT NULL DEFAULT '09:00'
            )
        """)
        await db.commit()


async def add_task(user_id: int, task_date: str, text: str) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "INSERT INTO tasks (user_id, task_date, text) VALUES (?, ?, ?)",
            (user_id, task_date, text),
        )
        await db.commit()
        return cur.lastrowid


async def get_tasks_for_date(user_id: int, task_date: str) -> list:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND task_date = ? ORDER BY id",
            (user_id, task_date),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_month_tasks(user_id: int, year_month: str) -> list:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND task_date LIKE ? ORDER BY task_date, id",
            (user_id, f"{year_month}-%"),
        )
        return [dict(r) for r in await cur.fetchall()]


async def mark_done(task_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def delete_task(task_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def get_all_active_users() -> list:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT DISTINCT user_id FROM tasks")
        return [r[0] for r in await cur.fetchall()]


async def set_report_time(user_id: int, time_str: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO user_settings (user_id, report_time) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET report_time = excluded.report_time",
            (user_id, time_str),
        )
        await db.commit()


async def get_report_time(user_id: int) -> str:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT report_time FROM user_settings WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else "09:00"
