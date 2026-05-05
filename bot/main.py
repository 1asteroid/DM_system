import asyncio
import logging
import sys
import os
from pathlib import Path

# Allow running both as: python main.py  (from bot/ dir)
#                     and: python -m bot.main  (from project root)
_here = Path(__file__).parent
_root = _here.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers.handlers import router
from bot.handlers.deadline_handler import router as deadline_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! .env faylini tekshiring.")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.include_router(deadline_router)

    logger.info("Bot ishga tushmoqda...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Bot xatolik bilan to'xtadi: %s", e)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
