from datetime import datetime
from typing import Optional

from sqlalchemy import select, update

from config import get_session
from database.models import Meeting, MeetingHistory


async def get_meeting_settings(chat_id: int) -> dict:
    async with get_session() as session:
        settings = await session.scalar(select(Meeting).filter_by(chat_id=int(chat_id)))
        if settings:
            return {
                "enable": settings.enable,
                "text": settings.text,
                "buttons": settings.buttons if settings.buttons else {},
                "media_link": settings.media_link,
                "always_send": settings.always_send,
                "delete_last_message": settings.delete_last_message,
            }
        return {
            "enable": True,
            "text": "Приветствуем в нашем чате!",
            "buttons": {},
            "media_link": None,
            "always_send": False,
            "delete_last_message": True,
        }


async def save_meeting_settings(
    chat_id: int,
    enable: Optional[bool] = None,
    text: Optional[str] = None,
    buttons: Optional[dict] = None,
    media_link: Optional[str] = None,
    always_send: Optional[bool] = None,
    delete_last_message: Optional[bool] = None,
) -> None:
    async with get_session() as session:
        settings = await session.scalar(select(Meeting).filter_by(chat_id=chat_id))

        if settings:
            if enable is not None:
                settings.enable = enable
            if text is not None:
                settings.text = text
            if buttons is not None:
                settings.buttons = buttons
            if media_link is not None:
                settings.media_link = media_link
            if always_send is not None:
                settings.always_send = always_send
            if delete_last_message is not None:
                settings.delete_last_message = delete_last_message
        else:
            settings = Meeting(
                chat_id=chat_id,
                enable=enable if enable is not None else False,
                text=text if text is not None else "Приветствуем в нашем чате!",
                buttons=buttons if buttons is not None else {},
                media_link=media_link,
                always_send=always_send if always_send is not None else False,
                delete_last_message=(
                    delete_last_message if delete_last_message is not None else True
                ),
            )
            session.add(settings)

        await session.commit()


async def get_user_meeting_history(chat_id: int, user_id: int) -> MeetingHistory | None:
    async with get_session() as session:
        query = select(MeetingHistory).where(
            MeetingHistory.chat_id == chat_id, MeetingHistory.user_id == user_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def update_meeting_message(chat_id: int, user_id: int, message_id: int) -> None:
    async with get_session() as session:
        await session.execute(
            update(MeetingHistory)
            .where(MeetingHistory.chat_id == chat_id, MeetingHistory.user_id == user_id)
            .values(message_id=message_id, last_welcomed_at=datetime.utcnow())
        )
        await session.commit()


async def create_meeting_history(
    chat_id: int, user_id: int, message_id: int
) -> MeetingHistory:
    async with get_session() as session:
        now = datetime.utcnow()
        history = MeetingHistory(
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            first_joined_at=now,
            last_welcomed_at=now,
        )
        session.add(history)
        await session.commit()
        return history
