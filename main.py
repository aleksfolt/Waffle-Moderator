# main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

import config
from BaseModeration.ban import ban_router
from BaseModeration.kick import kick_router
from BaseModeration.moderation import moderation_router
from BaseModeration.muting import muting_router
from BaseModeration.reports import report_router
from BaseModeration.warns import warns_router
from config import redis_client
from database.antiflood import preload_antiflood_settings
from database.antispam import preload_antispam_settings
from database.models import init_db
from database.utils import preload_admins
from handlers.antiflood import antiflood_router
from handlers.antispam import antispam_router
from handlers.blockChannels import channels_router
from handlers.blockStickers import stick_router
from handlers.captcha import captcha_router
from handlers.handlers import handlers_router
from handlers.meeting import meeting_router
from handlers.nsfwFilter import nsfw_router
from handlers.rules import rules_router
from middlefilters.addUser import AddUserToDatabaseMiddleware
from utils.helpers import utils_router


async def main():
    await init_db()
    await preload_admins()
    await preload_antispam_settings()
    await preload_antiflood_settings()
    bot = Bot(token=config.BOT_TOKEN)
    storage = RedisStorage(redis_client)
    dp = Dispatcher(storage=storage)
    dp.include_routers(
        stick_router,
        muting_router,
        ban_router,
        report_router,
        channels_router,
        kick_router,
        utils_router,
        moderation_router,
        antiflood_router,
        warns_router,
        nsfw_router,
        antispam_router,
        rules_router,
        meeting_router,
        captcha_router,
        handlers_router,
    )
    dp.message.middleware(AddUserToDatabaseMiddleware())
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await storage.close()
        await redis_client.aclose()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    print("\033[91m[!] Bot started.\033[0m")
    asyncio.run(main())
