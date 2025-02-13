from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.captcha import get_captcha_settings


async def captcha_kb(chat_id: int):
    builder = InlineKeyboardBuilder()
    settings = await get_captcha_settings(chat_id)
    enable_text = "✅ Вкл." if settings["enable"] else "❌ Выкл."

    builder.row(InlineKeyboardButton(text=enable_text, callback_data="scaptcha:switch"))
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )

    return builder.as_markup()
