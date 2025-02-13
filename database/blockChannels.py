from typing import Dict, Optional

from sqlalchemy import select

from config import get_session
from database.models import ChatSettings


async def get_block_channels_settings(chat_id: int):
    async with get_session() as session:
        result = await session.execute(
            select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()

        if settings is None:
            return {
                "chat_id": chat_id,
                "enable": False,
                "text": "Обнаружен канал! Блокирую..",
                "buttons": {},
            }

        return {
            "chat_id": settings.chat_id,
            "enable": settings.enable,
            "text": settings.text,
            "buttons": settings.buttons if settings.buttons else {},
        }


async def save_block_channels_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    text: Optional[str] = None,
    buttons: Optional[Dict] = None,
):
    async with get_session() as session:
        block = await session.get(ChatSettings, chat_id)

        if block:
            if enable is not None:
                block.enable = enable
            if text is not None:
                block.text = text
            if buttons is not None:
                block.buttons = buttons
        else:
            block = ChatSettings(
                chat_id=chat_id,
                enable=enable if enable is not None else False,
                text=text if text is not None else None,
                buttons=buttons if buttons is not None else {},
            )
            session.add(block)

        await session.commit()
