from typing import Optional

from sqlalchemy.future import select

from config import get_session
from database.models import Captcha


async def get_captcha_settings(chat_id: int):
    async with get_session() as session:
        settings = await session.scalar(select(Captcha).filter_by(chat_id=int(chat_id)))
        if settings:
            return {"enable": settings.enable}
        return {"enable": False}


async def save_captcha_settings(chat_id: int, enable: Optional[bool] = None):
    async with get_session() as session:
        settings = await session.scalar(select(Captcha).filter_by(chat_id=chat_id))

        if settings:
            if enable is not None:
                settings.enable = enable
        else:
            settings = Captcha(
                chat_id=chat_id, enable=enable if enable is not None else False
            )
            session.add(settings)

        await session.commit()
