import json
from typing import Optional

from sqlalchemy.future import select

from config import get_session, redis_client
from database.models import AntiSpamAll, AntiSpamForward, AntiSpamQuotes, AntiSpamTLink


async def get_tlink_settings(chat_id: int | str):
    chat_id = int(chat_id)
    cache_key = f"antispam:tlink:{chat_id}"

    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamTLink).filter_by(chat_id=chat_id)
        )
        if settings:
            result = {
                "enable": settings.enable,
                "action": settings.action,
                "delete_message": settings.delete_message,
                "duration_action": settings.duration_action,
                "username": settings.username,
                "bot": settings.bot,
                "exceptions": settings.exceptions if settings.exceptions else [],
            }
        else:
            result = {
                "enable": True,
                "action": "mute",
                "delete_message": True,
                "duration_action": "3600",
                "username": True,
                "bot": True,
                "exceptions": [],
            }

        await redis_client.setex(cache_key, 600, json.dumps(result))
        return result


async def save_tlink_settings(
    chat_id: int | str,
    enable: Optional[bool] = None,
    action: Optional[str] = None,
    delete_message: Optional[bool] = None,
    duration_action: Optional[str] = None,
    username: Optional[bool] = None,
    bot: Optional[bool] = None,
    exceptions: Optional[list] = None,
):
    chat_id = int(chat_id)
    cache_key = f"antispam:tlink:{chat_id}"

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamTLink).filter_by(chat_id=chat_id)
        )

        if settings:
            if enable is not None:
                settings.enable = enable
            if action is not None:
                settings.action = action
            if delete_message is not None:
                settings.delete_message = delete_message
            if duration_action is not None:
                settings.duration_action = duration_action
            if username is not None:
                settings.username = username
            if bot is not None:
                settings.bot = bot
            if exceptions is not None:
                settings.exceptions = exceptions
        else:
            settings = AntiSpamTLink(
                chat_id=chat_id,
                enable=enable if enable is not None else True,
                action=action if action is not None else "mute",
                delete_message=delete_message if delete_message is not None else True,
                duration_action=(
                    duration_action if duration_action is not None else "3600"
                ),
                username=username if username is not None else True,
                bot=bot if bot is not None else True,
                exceptions=exceptions if exceptions is not None else [],
            )
            session.add(settings)

        await session.commit()

        new_settings = {
            "enable": settings.enable,
            "action": settings.action,
            "delete_message": settings.delete_message,
            "duration_action": settings.duration_action,
            "username": settings.username,
            "bot": settings.bot,
            "exceptions": settings.exceptions if settings.exceptions else [],
        }
        await redis_client.setex(cache_key, 600, json.dumps(new_settings))


async def get_forward_settings(chat_id: int | str, entity_type: str):
    chat_id = int(chat_id)
    cache_key = f"antispam:forward:{chat_id}:{entity_type}"

    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamForward).where(
                AntiSpamForward.chat_id == chat_id,
                AntiSpamForward.entity_type == entity_type,
            )
        )
        if settings:
            result = {
                "enable": settings.enable,
                "action": settings.action,
                "duration_actions": settings.duration_actions,
                "delete_message": settings.delete_message,
                "exceptions": settings.exceptions if settings.exceptions else [],
            }
        else:
            result = {
                "enable": False,
                "action": "mute",
                "duration_actions": "3600",
                "delete_message": True,
                "exceptions": [],
            }

        await redis_client.setex(cache_key, 600, json.dumps(result))
        return result


async def save_forward_settings(
    chat_id: int | str,
    entity_type: str,
    enable: Optional[bool] = None,
    action: Optional[str] = None,
    duration_actions: Optional[str] = None,
    delete_message: Optional[bool] = None,
    exceptions: Optional[list] = None,
):
    chat_id = int(chat_id)
    cache_key = f"antispam:forward:{chat_id}:{entity_type}"

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamForward).where(
                AntiSpamForward.chat_id == chat_id,
                AntiSpamForward.entity_type == entity_type,
            )
        )

        if settings:
            if enable is not None:
                settings.enable = enable
            if action is not None:
                settings.action = action
            if duration_actions is not None:
                settings.duration_actions = duration_actions
            if delete_message is not None:
                settings.delete_message = delete_message
            if exceptions is not None:
                settings.exceptions = exceptions
        else:
            settings = AntiSpamForward(
                chat_id=chat_id,
                entity_type=entity_type,
                enable=enable if enable is not None else True,
                action=action if action is not None else "mute",
                duration_actions=(
                    duration_actions if duration_actions is not None else "3600"
                ),
                delete_message=delete_message if delete_message is not None else True,
                exceptions=exceptions if exceptions is not None else [],
            )
            session.add(settings)

        await session.commit()

        new_settings = {
            "enable": settings.enable,
            "action": settings.action,
            "duration_actions": settings.duration_actions,
            "delete_message": settings.delete_message,
            "exceptions": settings.exceptions if settings.exceptions else [],
        }
        await redis_client.setex(cache_key, 600, json.dumps(new_settings))


async def get_quotes_settings(chat_id: int | str, entity_type: str):
    chat_id = int(chat_id)
    cache_key = f"antispam:quotes:{chat_id}:{entity_type}"

    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamQuotes).where(
                AntiSpamQuotes.chat_id == chat_id,
                AntiSpamQuotes.entity_type == entity_type,
            )
        )
        if settings:
            result = {
                "enable": settings.enable,
                "action": settings.action,
                "duration_actions": settings.duration_actions,
                "delete_message": settings.delete_message,
                "exceptions": settings.exceptions if settings.exceptions else [],
            }
        else:
            result = {
                "enable": False,
                "action": "mute",
                "duration_actions": "3600",
                "delete_message": True,
                "exceptions": [],
            }

        await redis_client.setex(cache_key, 600, json.dumps(result))
        return result


async def save_quotes_settings(
    chat_id: int | str,
    entity_type: str,
    enable: Optional[bool] = None,
    action: Optional[str] = None,
    duration_actions: Optional[str] = None,
    delete_message: Optional[bool] = None,
    exceptions: Optional[list] = None,
):
    chat_id = int(chat_id)
    cache_key = f"antispam:quotes:{chat_id}:{entity_type}"

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamQuotes).where(
                AntiSpamQuotes.chat_id == chat_id,
                AntiSpamQuotes.entity_type == entity_type,
            )
        )

        if settings:
            if enable is not None:
                settings.enable = enable
            if action is not None:
                settings.action = action
            if duration_actions is not None:
                settings.duration_actions = duration_actions
            if delete_message is not None:
                settings.delete_message = delete_message
            if exceptions is not None:
                settings.exceptions = exceptions
        else:
            settings = AntiSpamQuotes(
                chat_id=chat_id,
                entity_type=entity_type,
                enable=enable if enable is not None else True,
                action=action if action is not None else "mute",
                duration_actions=(
                    duration_actions if duration_actions is not None else "3600"
                ),
                delete_message=delete_message if delete_message is not None else True,
                exceptions=exceptions if exceptions is not None else [],
            )
            session.add(settings)

        await session.commit()

        new_settings = {
            "enable": settings.enable,
            "action": settings.action,
            "duration_actions": settings.duration_actions,
            "delete_message": settings.delete_message,
            "exceptions": settings.exceptions if settings.exceptions else [],
        }
        await redis_client.setex(cache_key, 600, json.dumps(new_settings))


async def get_all_settings(chat_id: int):
    cache_key = f"antispam:all:{chat_id}"

    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamAll).filter_by(chat_id=int(chat_id))
        )
        if settings:
            result = {
                "enable": settings.enable,
                "action": settings.action,
                "duration_actions": settings.duration_actions,
                "delete_message": settings.delete_message,
                "exceptions": settings.exceptions if settings.exceptions else [],
            }
        else:
            result = {
                "enable": False,
                "action": "mute",
                "duration_actions": "3600",
                "delete_message": True,
                "exceptions": [],
            }

        await redis_client.setex(cache_key, 600, json.dumps(result))
        return result


async def save_all_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    action: Optional[str] = None,
    duration_actions: Optional[str] = None,
    delete_message: Optional[bool] = None,
    exceptions: Optional[list] = None,
):
    cache_key = f"antispam:all:{chat_id}"

    async with get_session() as session:
        settings = await session.scalar(
            select(AntiSpamAll).filter_by(chat_id=int(chat_id))
        )

        if settings:
            if enable is not None:
                settings.enable = enable
            if action is not None:
                settings.action = action
            if duration_actions is not None:
                settings.duration_actions = duration_actions
            if delete_message is not None:
                settings.delete_message = delete_message
            if exceptions is not None:
                settings.exceptions = exceptions
        else:
            settings = AntiSpamAll(
                chat_id=int(chat_id),
                enable=enable if enable is not None else True,
                action=action if action is not None else "mute",
                duration_actions=(
                    duration_actions if duration_actions is not None else "3600"
                ),
                delete_message=delete_message if delete_message is not None else True,
                exceptions=exceptions if exceptions is not None else [],
            )
            session.add(settings)

        await session.commit()

        new_settings = {
            "enable": settings.enable,
            "action": settings.action,
            "duration_actions": settings.duration_actions,
            "delete_message": settings.delete_message,
            "exceptions": settings.exceptions if settings.exceptions else [],
        }
        await redis_client.setex(cache_key, 600, json.dumps(new_settings))


async def preload_antispam_settings():
    async with get_session() as session:
        tlink_result = await session.execute(select(AntiSpamTLink))
        tlink_settings = tlink_result.scalars().all()

        forward_result = await session.execute(select(AntiSpamForward))
        forward_settings = forward_result.scalars().all()

        quotes_result = await session.execute(select(AntiSpamQuotes))
        quotes_settings = quotes_result.scalars().all()

        all_result = await session.execute(select(AntiSpamAll))
        all_settings = all_result.scalars().all()

        count = 0
        async with redis_client.pipeline() as pipe:
            for tlink in tlink_settings:
                cache_key = f"antispam:tlink:{tlink.chat_id}"
                settings = {
                    "enable": tlink.enable,
                    "action": tlink.action,
                    "delete_message": tlink.delete_message,
                    "duration_action": tlink.duration_action,
                    "username": tlink.username,
                    "bot": tlink.bot,
                    "exceptions": tlink.exceptions if tlink.exceptions else [],
                }
                pipe.setex(cache_key, 600, json.dumps(settings))
                count += 1

            for forward in forward_settings:
                cache_key = f"antispam:forward:{forward.chat_id}:{forward.entity_type}"
                settings = {
                    "enable": forward.enable,
                    "action": forward.action,
                    "duration_actions": forward.duration_actions,
                    "delete_message": forward.delete_message,
                    "exceptions": forward.exceptions if forward.exceptions else [],
                }
                pipe.setex(cache_key, 600, json.dumps(settings))
                count += 1

            for quotes in quotes_settings:
                cache_key = f"antispam:quotes:{quotes.chat_id}:{quotes.entity_type}"
                settings = {
                    "enable": quotes.enable,
                    "action": quotes.action,
                    "duration_actions": quotes.duration_actions,
                    "delete_message": quotes.delete_message,
                    "exceptions": quotes.exceptions if quotes.exceptions else [],
                }
                pipe.setex(cache_key, 600, json.dumps(settings))
                count += 1

            for all in all_settings:
                cache_key = f"antispam:all:{all.chat_id}"
                settings = {
                    "enable": all.enable,
                    "action": all.action,
                    "duration_actions": all.duration_actions,
                    "delete_message": all.delete_message,
                    "exceptions": all.exceptions if all.exceptions else [],
                }
                pipe.setex(cache_key, 600, json.dumps(settings))
                count += 1

            await pipe.execute()
