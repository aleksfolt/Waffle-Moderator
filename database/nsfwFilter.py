from typing import Optional

from sqlalchemy.future import select

from config import get_session
from database.models import NsfwFilter


async def get_nsfwFilter_settings(chat_id: int):
    async with get_session() as session:
        settings = await session.scalar(
            select(NsfwFilter).filter_by(chat_id=int(chat_id))
        )
        if settings:
            return {
                "enable": settings.enable,
                "percent": settings.percent,
                "journal": settings.journal,
                "action": settings.action,
                "duration_action": settings.duration_action,
                "delete_message": settings.delete_message,
                "text": settings.text,
                "buttons": settings.buttons if settings.buttons else [],
            }
        return {
            "enable": False,
            "percent": 80,
            "journal": True,
            "action": "mute",
            "duration_action": "3600",
            "delete_message": True,
            "text": "Обнаружен небезопасный контент!",
            "buttons": [],
        }


async def save_nsfwFilter_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    percent: Optional[int] = None,
    journal: Optional[bool] = None,
    action: Optional[str] = None,
    duration_action: Optional[int] = None,
    delete_message: Optional[bool] = None,
    text: Optional[str] = None,
    buttons: Optional[list] = None,
):
    async with get_session() as session:
        settings = await session.scalar(select(NsfwFilter).filter_by(chat_id=chat_id))

        if settings:
            if enable is not None:
                settings.enable = enable
            if percent is not None:
                settings.percent = percent
            if journal is not None:
                settings.journal = journal
            if action is not None:
                settings.action = action
            if duration_action is not None:
                settings.duration_action = duration_action
            if delete_message is not None:
                settings.delete_message = delete_message
            if text is not None:
                settings.text = text
            if buttons is not None:
                settings.buttons = buttons
        else:
            settings = NsfwFilter(
                chat_id=chat_id,
                enable=enable if enable is not None else False,
                percent=percent if percent is not None else 80,
                journal=journal if journal is not None else True,
                action=action if action is not None else "mute",
                duration_action=(
                    duration_action if duration_action is not None else "3600"
                ),
                delete_message=delete_message if delete_message is not None else True,
                text=text if text is not None else "Обнаружен небезопасный контент!",
                buttons=buttons if buttons is not None else [],
            )
            session.add(settings)

        await session.commit()
