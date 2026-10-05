import aiosqlite
import math

DB_PATH = "userprompts.db"
PER_PAGE = 5

PRESET_PROMPTS = {
    1: ("Переводчик", "Ты переводчик. Переводи любой текст на английский."),
    2: ("Кодер", "Ты опытный Python-разработчик. Отвечай кратко, с кодом."),
    3: ("Редактор", "Ты редактор. Исправляй ошибки и улучшай стиль текста."),
}


async def init_db() -> None:
    """Вызывается один раз при старте бота: создаёт таблицы, если их нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                system_prompt TEXT NOT NULL DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                role TEXT NOT NULL,      -- 'user' или 'assistant'
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_chat (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_prompts_user ON custom_prompts(user_id)")
        await db.commit()

def total_pages(total: int, per_page: int=PER_PAGE) -> int:
    return max(1, math.ceil(total / per_page))
def clamp_page(page: int, total: int) -> int:
    return min(max(page, 0), total_pages(total) - 1)

# ---------- Чаты ----------

async def count_chats(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM chats WHERE user_id = ?", (user_id,))
        return (await cur.fetchone())[0]

async def get_chats_page(user_id: int, page: int, per_page: int = PER_PAGE):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
                "SELECT * FROM chats WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (user_id, per_page, page * per_page),
            )
        return await cur.fetchall()

async def get_chats(user_id: int) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM chats WHERE user_id = ? ORDER BY id", (user_id,)
        )
        return await cursor.fetchall()


async def create_chat(user_id: int, title: str | None = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO chats (user_id, title) VALUES (?, ?)",
            (user_id, title or "Новый чат"),
        )
        chat_id = cursor.lastrowid
        # если название не задали, подставим "Чат #id"
        if title is None:
            await db.execute(
                "UPDATE chats SET title = ? WHERE id = ?", (f"Чат #{chat_id}", chat_id)
            )
        await db.execute(
            "INSERT INTO active_chat (user_id, chat_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET chat_id = excluded.chat_id",
            (user_id, chat_id),
        )
        await db.commit()
        return chat_id


async def delete_chat(user_id: int, chat_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)
        )
        await db.commit()


async def get_chat(user_id: int, chat_id: int) -> aiosqlite.Row | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)
        )
        return await cursor.fetchone()


async def set_system_prompt(chat_id: int, prompt: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE chats SET system_prompt = ? WHERE id = ?", (prompt, chat_id)
        )
        await db.commit()

async def rename_chat(user_id: int, chat_id: int, title: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE chats SET title = ? WHERE id = ? AND user_id = ?",
            (title, chat_id, user_id),
        )
        await db.commit()

# КАСТОМНЫЕ ПРОМПТЫ

async def add_custom_prompt(user_id: int, title: str, text: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO custom_prompts (user_id, title, text) VALUES (?, ?, ?)",
            (user_id, title, text),
        )
        await db.commit()
        return cur.lastrowid

async def get_custom_prompts_page(user_id: int, page: int, per_page: int = PER_PAGE):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM custom_prompts WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, per_page, page * per_page),
        )
        return await cur.fetchall()

async def get_custom_prompt(user_id: int, prompt_id : int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM custom_prompts WHERE id = ? AND user_id = ?",
            (prompt_id, user_id),
        )
        return await cur.fetchone()

async def update_custom_prompt_text(user_id: int, prompt_id: int, text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE custom_prompts SET text = ? WHERE id = ? AND user_id = ?",
            (text, prompt_id, user_id),
        )
        await db.commit()

async def count_custom_prompts(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM custom_prompts WHERE user_id = ?", (user_id,))
        return (await cur.fetchone())[0]
    
async def delete_custom_prompt(user_id: int, prompt_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM custom_prompts WHERE id = ? AND user_id = ?", (prompt_id, user_id))
        await db.commit()

async def rename_custom_prompt(user_id: int, prompt_id: int, title: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE custom_prompts SET title = ? WHERE id = ? AND user_id = ?",
            (title, prompt_id, user_id),
        )
        await db.commit()

# ---------- Активный чат ----------

async def get_active_id(user_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT chat_id FROM active_chat WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_active(user_id: int, chat_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO active_chat (user_id, chat_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET chat_id = excluded.chat_id",
            (user_id, chat_id),
        )
        await db.commit()


# ---------- История сообщений ----------

async def add_message(chat_id: int, role: str, content: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        await db.commit()


async def get_history(chat_id: int, limit: int = 50) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE chat_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return list(reversed(rows))  # вернуть в хронологическом порядке