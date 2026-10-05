import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from config import load_config
from bot.handlers import commands
from database.storage import init_db
from services import llm_storage

async def main():
    await init_db()
    await llm_storage.init_llm_db()
    storage = MemoryStorage()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=storage)

    dp.include_router(commands.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    config = load_config()
    logging.basicConfig(level=logging.INFO, filename="last.log", filemode="a",
                        format="%(name)s%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())