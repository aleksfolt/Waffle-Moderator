from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.meeting import get_meeting_settings


async def meeting_kb(chat_id):
    builder = InlineKeyboardBuilder()
    settings = await get_meeting_settings(chat_id)
    builder.row(
        InlineKeyboardButton(
            text="✅ Вкл." if settings["enable"] else "❌ Выкл.",
            callback_data="meeting:switch",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📩 Настроить сообщение", callback_data="meeting:settings"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔔 Всегда отправлять", callback_data="meeting:send:always"
        ),
        InlineKeyboardButton(
            text="1️⃣ Отправить 1 раз", callback_data="meeting:send:once"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="♻️ Удалять последнее сообщение"
            + (" ✅" if settings["delete_last_message"] else " ❌"),
            callback_data="meeting:delete_last_message",
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )
    return builder.as_markup()
