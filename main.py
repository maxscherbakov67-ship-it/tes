import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from config import load_config

config = load_config()
async def main():
    storage = MemoryStorage()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=storage)

    #dp.include_router
    await dp.start_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="last.log", filemode="a",
                        format="%(name)s%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())