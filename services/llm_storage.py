"""LLM-инфраструктура: модели, API-ключи, выбор модели пользователем.
Отдельно от ботовой БД — бот хранит только диалоги и промпты."""
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "llm.db"


async def init_llm_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS llm_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                api_name TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'openai',
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at TEXT,
                fails INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_model (
                user_id INTEGER PRIMARY KEY,
                model_id INTEGER NOT NULL REFERENCES llm_models(id)
            )
        """)
        cur = await db.execute("SELECT COUNT(*) FROM llm_models")
        if (await cur.fetchone())[0] == 0:
            await db.executemany(
                "INSERT INTO llm_models (name, api_name, provider) VALUES (?, ?, ?)",
                [
                    ("GPT-4o mini", "gpt-4o-mini", "openai"),
                    ("Claude Sonnet", "claude-sonnet-4-5", "anthropic"),
                ],
            )
        await db.commit()


# ---------- Модели ----------

async def get_models() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM llm_models WHERE is_active = 1 ORDER BY id")
        return await cur.fetchall()

async def get_models_all() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM llm_models ORDER BY id")
        return await cur.fetchall()

async def add_model(name: str, api_name: str, provider: str = "openai") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO llm_models (name, api_name, provider) VALUES (?, ?, ?)",
            (name, api_name, provider),
        )
        await db.commit()
        return cur.lastrowid

async def set_model_active(model_id: int, active: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE llm_models SET is_active = ? WHERE id = ?", (int(active), model_id))
        await db.commit()


# ---------- Выбор модели пользователем ----------

async def set_user_model(user_id: int, model_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_model (user_id, model_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET model_id = excluded.model_id",
            (user_id, model_id),
        )
        await db.commit()

async def get_user_model(user_id: int):
    """Выбранная модель или первая активная по умолчанию."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT m.* FROM user_model u "
            "JOIN llm_models m ON m.id = u.model_id "
            "WHERE u.user_id = ? AND m.is_active = 1",
            (user_id,),
        )
        row = await cur.fetchone()
        if row:
            return row
        cur = await db.execute("SELECT * FROM llm_models WHERE is_active = 1 ORDER BY id LIMIT 1")
        return await cur.fetchone()


# ---------- API-ключи ----------

async def add_api_key(provider: str, key: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("INSERT INTO api_keys (provider, key) VALUES (?, ?)", (provider, key))
        await db.commit()
        return cur.lastrowid

async def get_api_keys(provider: str) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM api_keys WHERE provider = ? AND is_active = 1 ORDER BY id",
            (provider,),
        )
        return await cur.fetchall()

async def get_api_keys_all() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM api_keys ORDER BY provider, id")
        return await cur.fetchall()

async def set_api_key_active(key_id: int, active: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE api_keys SET is_active = ? WHERE id = ?", (int(active), key_id))
        await db.commit()