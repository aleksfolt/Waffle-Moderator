from typing import Union

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class HasPromoteRights(BaseFilter):

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        if isinstance(event, Message):
            chat_id = event.chat.id
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            if event.message is None or event.message.chat is None:
                return False
            chat_id = event.message.chat.id
            user_id = event.from_user.id
        else:
            return False

        try:
            admins = await event.bot.get_chat_administrators(chat_id=chat_id)
        except TelegramBadRequest as e:
            if "there are no administrators in the private chat" in str(e):
                return False
            else:
                raise

        for admin in admins:
            if admin.user.id == user_id:
                if (
                    isinstance(admin, types.ChatMemberAdministrator)
                    and admin.can_restrict_members
                ):
                    return True
                if isinstance(admin, types.ChatMemberOwner):
                    return True

        return False
