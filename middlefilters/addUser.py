from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.future import select

from config import get_session
from database.models import User


class AddUserToDatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        try:
            user_id = event.from_user.id
            username = event.from_user.username or "unknown"
            first_name = event.from_user.first_name or "unknown"
            last_name = event.from_user.last_name or "unknown"

            async with get_session() as session:

                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                existing_user = result.scalar_one_or_none()

                if not existing_user or (
                    existing_user.username != username
                    or existing_user.first_name != first_name
                    or existing_user.last_name != last_name
                ):
                    stmt = (
                        pg_insert(User)
                        .values(
                            user_id=user_id,
                            username=username,
                            first_name=first_name,
                            last_name=last_name,
                        )
                        .on_conflict_do_update(
                            index_elements=["user_id"],
                            set_={
                                "username": username,
                                "first_name": first_name,
                                "last_name": last_name,
                            },
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()

            return await handler(event, data)
        except Exception:
            return await handler(event, data)
