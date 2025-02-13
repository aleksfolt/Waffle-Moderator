# пример
import json
from typing import Optional

from sqlalchemy import select

from config import get_session, redis_client
from database.models import AntiFlood


async def get_antiflood_settings(chat_id: int):
    cache_key = f"antiflood:{chat_id}"

    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    async with get_session() as session:
        antiflood = await session.scalar(
            select(AntiFlood).filter_by(chat_id=int(chat_id))
        )
        if antiflood:
            settings = {
                "enable": antiflood.enable,
                "messages": antiflood.messages,
                "time": antiflood.time,
                "action": antiflood.action,
                "delete_message": antiflood.delete_message,
                "duration_action": antiflood.duration_action,
                "journal": antiflood.journal,
            }
        else:
            settings = {
                "enable": True,
                "messages": 5,
                "time": 10,
                "action": "mute",
                "delete_message": True,
                "duration_action": "60s",
                "journal": True,
            }

    await redis_client.setex(cache_key, 600, json.dumps(settings))

    return settings


async def save_antiflood_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    messages: Optional[int] = None,
    time: Optional[int] = None,
    action: Optional[str] = None,
    delete_message: Optional[bool] = None,
    duration_action: Optional[str] = None,
    journal: Optional[bool] = None,
):
    cache_key = f"antiflood:{chat_id}"

    async with get_session() as session:
        antiflood = await session.scalar(
            select(AntiFlood).filter_by(chat_id=int(chat_id))
        )

        if antiflood:
            if enable is not None:
                antiflood.enable = enable
            if messages is not None:
                antiflood.messages = messages
            if time is not None:
                antiflood.time = time
            if action is not None:
                antiflood.action = action
            if delete_message is not None:
                antiflood.delete_message = delete_message
            if duration_action is not None:
                antiflood.duration_action = duration_action
            if journal is not None:
                antiflood.journal = journal
        else:
            antiflood = AntiFlood(
                chat_id=int(chat_id),
                enable=enable if enable is not None else True,
                messages=messages if messages is not None else 5,
                time=time if time is not None else 10,
                action=action if action is not None else "mute",
                delete_message=delete_message if delete_message is not None else True,
                duration_action=(
                    duration_action if duration_action is not None else "60s"
                ),
                journal=journal if journal is not None else True,
            )
            session.add(antiflood)

        await session.commit()

    new_settings = {
        "enable": antiflood.enable,
        "messages": antiflood.messages,
        "time": antiflood.time,
        "action": antiflood.action,
        "delete_message": antiflood.delete_message,
        "duration_action": antiflood.duration_action,
        "journal": antiflood.journal,
    }

    await redis_client.setex(cache_key, 600, json.dumps(new_settings))


async def preload_antiflood_settings():
    async with get_session() as session:
        result = await session.execute(select(AntiFlood))
        antiflood_settings = result.scalars().all()

        if not antiflood_settings:
            return

        count = 0
        async with redis_client.pipeline() as pipe:
            for antiflood in antiflood_settings:
                chat_id = antiflood.chat_id
                cache_key = f"antiflood:{chat_id}"
                settings = {
                    "enable": antiflood.enable,
                    "messages": antiflood.messages,
                    "time": antiflood.time,
                    "action": antiflood.action,
                    "delete_message": antiflood.delete_message,
                    "duration_action": antiflood.duration_action,
                    "journal": antiflood.journal,
                }
                pipe.setex(cache_key, 600, json.dumps(settings))
                count += 1

            await pipe.execute()
