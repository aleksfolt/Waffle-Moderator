from typing import Optional

from sqlalchemy.future import select

from config import get_session
from database.models import Rules


async def get_rules_settings(chat_id: int):
    async with get_session() as session:
        settings = await session.scalar(select(Rules).filter_by(chat_id=int(chat_id)))
        if settings:
            return {
                "enable": settings.enable,
                "text": settings.text,
                "buttons": settings.buttons if settings.buttons else {},
                "permissions": settings.permissions,
            }
        return {
            "enable": False,
            "text": "Правила:",
            "buttons": {},
            "permissions": "members",
        }


async def save_rules_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    text: Optional[str] = None,
    buttons: Optional[dict] = None,
    permissions: Optional[str] = None,
):
    async with get_session() as session:
        settings = await session.scalar(select(Rules).filter_by(chat_id=chat_id))

        if settings:
            if enable is not None:
                settings.enable = enable
            if text is not None:
                settings.text = text
            if buttons is not None:
                settings.buttons = buttons
            if permissions is not None:
                settings.permissions = permissions
        else:
            settings = Rules(
                chat_id=chat_id,
                enable=enable if enable is not None else False,
                text=text if text is not None else "Правила:",
                buttons=buttons if buttons is not None else {},
                permissions=permissions if permissions is not None else "members",
            )
            session.add(settings)

        await session.commit()
