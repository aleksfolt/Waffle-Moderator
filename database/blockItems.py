from sqlalchemy import select

from config import get_session
from database.models import Block


async def add_item_to_block(chat_id: int, to_block: str, item: str):
    async with get_session() as session:
        result = await session.execute(select(Block).where(Block.chat_id == chat_id))
        block = result.scalar_one_or_none()

        if block:
            current_list = getattr(block, to_block, [])
            if isinstance(current_list, list) and item not in current_list:
                new_list = current_list + [item]
                setattr(block, to_block, new_list)
        else:
            block = Block(chat_id=chat_id, **{to_block: [item]})
            session.add(block)


async def get_items_from_block(chat_id: int, from_block: str) -> list:
    async with get_session() as session:
        result = await session.execute(select(Block).where(Block.chat_id == chat_id))
        block = result.scalar_one_or_none()

        if block:
            return getattr(block, from_block, [])
        else:
            return []


async def remove_item_from_block(chat_id: int, from_block: str, item: str):
    async with get_session() as session:
        result = await session.execute(select(Block).where(Block.chat_id == chat_id))
        block = result.scalar_one_or_none()

        if block:
            current_list = getattr(block, from_block, [])
            if isinstance(current_list, list) and item in current_list:
                new_list = current_list.copy()
                new_list.remove(item)
                setattr(block, from_block, new_list)
                await session.commit()
