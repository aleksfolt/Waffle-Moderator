from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.rules import get_rules_settings


async def rules_kb(chat_id):
    builder = InlineKeyboardBuilder()
    settings = await get_rules_settings(chat_id)
    enable_text = "✅ Вкл." if settings["enable"] else "❌ Выкл."
    builder.row(InlineKeyboardButton(text=enable_text, callback_data="srules:switch"))
    builder.row(
        InlineKeyboardButton(
            text="📩 Настроить сообщение", callback_data="srules:settings"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🕹 Права на команду", callback_data="srules:permissions"
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )
    return builder.as_markup()


async def permissions_kb(chat_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="/rules", callback_data="None"),
        InlineKeyboardButton(text="✖", callback_data="srules:epermissions:noone"),
        InlineKeyboardButton(text="👮🏻", callback_data="srules:epermissions:admins"),
        InlineKeyboardButton(text="👥", callback_data="srules:epermissions:members"),
        InlineKeyboardButton(text="🤖", callback_data="srules:epermissions:private"),
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:rules:back:{chat_id}")
    )
    return builder.as_markup()
