from typing import Optional

from sqlalchemy.future import select

from config import get_session
from database.models import UserWarn, Warns


async def get_warn_settings(chat_id: int):
    async with get_session() as session:
        warn = await session.scalar(select(Warns).filter_by(chat_id=int(chat_id)))
        if warn:
            return {
                "enable": warn.enable,
                "text": warn.text,
                "action": warn.action,
                "duration_action": warn.duration_action,
                "warns_count": warn.warns_count,
            }
        return {
            "enable": True,
            "text": "%%__mention__%% [%%__user_id__%%] предупрежден (%%__warn_count__%%).",
            "action": "mute",
            "duration_action": 1800,
            "warns_count": 3,
        }


async def save_warn_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    text: Optional[str] = None,
    action: Optional[str] = None,
    duration_action: Optional[str] = None,
    warns_count: Optional[int] = None,
):
    async with get_session() as session:
        warn = await session.scalar(select(Warns).filter_by(chat_id=int(chat_id)))

        if warn:
            if enable is not None:
                warn.enable = enable
            if text is not None:
                warn.text = text
            if action is not None:
                warn.action = action
            if duration_action is not None:
                warn.duration_action = duration_action
            if warns_count is not None:
                warn.warns_count = warns_count
        else:
            warn = Warns(
                chat_id=int(chat_id),
                enable=enable if enable is not None else True,
                text=(
                    text
                    if text is not None
                    else "%%__mention__%% [%%__user_id__%%] предупрежден (%%__warn_count__%%)."
                ),
                action=action if action is not None else "mute",
                duration_action=(
                    duration_action if duration_action is not None else 1800
                ),
                warns_count=warns_count if warns_count is not None else 3,
            )
            session.add(warn)

        await session.commit()


async def get_user_warns(chat_id: int, user_id: int) -> Optional[UserWarn]:
    async with get_session() as session:
        warn_entry = await session.scalar(
            select(UserWarn).where(
                UserWarn.chat_id == chat_id, UserWarn.user_id == user_id
            )
        )
        if warn_entry:
            async with get_session() as new_session:
                warn_entry = await new_session.get(UserWarn, warn_entry.id)
        return warn_entry


async def add_warn(chat_id: int, user_id: int) -> int:
    async with get_session() as session:
        warn_entry = await session.scalar(
            select(UserWarn).where(
                UserWarn.chat_id == chat_id, UserWarn.user_id == user_id
            )
        )

        if warn_entry:
            warn_entry.warns += 1
        else:
            warn_entry = UserWarn(user_id=user_id, chat_id=chat_id, warns=1)
            session.add(warn_entry)

        await session.commit()
        return warn_entry.warns


async def reset_warns(chat_id: int, user_id: int) -> bool:
    async with get_session() as session:
        warn_entry = await session.scalar(
            select(UserWarn).where(
                UserWarn.chat_id == chat_id, UserWarn.user_id == user_id
            )
        )

        if warn_entry:
            warn_entry.warns = 0
            await session.commit()
            return True

        return False


async def remove_warn(chat_id: int, user_id: int) -> int:
    async with get_session() as session:
        warn_entry = await session.scalar(
            select(UserWarn).where(
                UserWarn.chat_id == chat_id, UserWarn.user_id == user_id
            )
        )

        if warn_entry and warn_entry.warns > 0:
            warn_entry.warns -= 1
            await session.commit()
            return warn_entry.warns
        return 0


async def get_warns_count(chat_id: int, user_id: int) -> int:
    async with get_session() as session:
        warn_entry = await session.scalar(
            select(UserWarn).where(
                UserWarn.chat_id == chat_id, UserWarn.user_id == user_id
            )
        )
        return warn_entry.warns if warn_entry else 0
