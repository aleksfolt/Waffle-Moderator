from typing import Any, Awaitable, Callable, Dict

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class ChatRestrictionMiddleware(BaseMiddleware):
    def __init__(self, allowed_chat_id: int):
        super().__init__()
        self.allowed_chat_id = allowed_chat_id

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.chat.type in ["group", "supergroup"]:
            if event.chat.id != self.allowed_chat_id:
                return
        return await handler(event, data)
        return await handler(event, data)
