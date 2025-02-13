import json
from typing import List, Optional

from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_session, redis_client
from database.models import Chat, User


async def add_or_update_user(
    user_id: int, username: str, first_name: str, last_name: str, session: AsyncSession
) -> None:
    async with session.begin():
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


async def get_user_by_id_or_username(
    user_id: Optional[int] = None, username: Optional[str] = None
) -> Optional[User]:
    async with get_session() as session:
        if user_id:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()
        elif username:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
    return None


async def add_or_update_chat(
    chat_id: int,
    title: str = None,
    members_count: int = None,
    work: bool = None,
    admins: list = None,
    all_admins: list = None,
):
    async with get_session() as session:
        chat = await session.get(Chat, chat_id)

        if chat:
            if title is not None:
                chat.title = title
            if members_count is not None:
                chat.members_count = members_count
            if work is not None:
                chat.work = work
            if admins is not None:
                chat.admins = admins
            if all_admins is not None:
                chat.all_admins = all_admins
        else:
            chat = Chat(
                chat_id=chat_id,
                title=title or "Untitled Chat",
                members_count=members_count or 0,
                work=work if work is not None else False,
                admins=admins or [],
                all_admins=all_admins or [],
            )
            session.add(chat)

        await session.commit()

        if admins is not None:
            try:
                serialized_admins = json.dumps(admins)
                await redis_client.set(f"chat:{chat_id}:admins", serialized_admins)
            except (TypeError, ValueError) as e:
                print(f"Error serializing admins list: {e}")


async def get_user_chats(user_id):
    async with get_session() as session:
        result = await session.execute(
            select(Chat).where(
                cast(Chat.admins, JSONB).op("@>")(cast([user_id], JSONB))
            )
        )
        return result.scalars().all()


async def get_chat(chat_id: int):
    async with get_session() as session:
        query = select(Chat).where(Chat.chat_id == chat_id)
        result = await session.execute(query)
        chat = result.scalar_one_or_none()
        return chat


async def get_chat_admins(chat_id: int) -> List[int]:
    cache_key = f"chat:{chat_id}:all_admins"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    async with get_session() as session:
        result = await session.execute(select(Chat).filter_by(chat_id=chat_id))
        chat = result.scalars().first()

        if chat and chat.all_admins:
            admin_ids = (
                json.loads(chat.all_admins)
                if isinstance(chat.all_admins, str)
                else chat.all_admins
            )
        else:
            admin_ids = []

    await redis_client.setex(cache_key, 600, json.dumps(admin_ids))
    return admin_ids


async def preload_admins():
    async with get_session() as session:
        result = await session.execute(select(Chat.chat_id).distinct())
        chat_ids = [row[0] for row in result.fetchall()]

        if not chat_ids:
            return

        count = 0
        async with redis_client.pipeline() as pipe:
            for chat_id in chat_ids:
                admin_ids = await get_chat_admins(chat_id)
                cache_key = f"chat:{chat_id}:admins"
                pipe.setex(cache_key, 600, json.dumps(admin_ids))
                count += 1

            await pipe.execute()
