from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.antiflood import get_antiflood_settings


async def antiflood_kb(chat_id):
    chat_id = int(chat_id)
    settings = await get_antiflood_settings(chat_id)

    enable_status = "✅ Вкл" if settings["enable"] else "❌ Выкл"
    delete_status = (
        "🗑 Удалять сообщения ✅"
        if settings["delete_message"]
        else "🗑 Удалять сообщения ❌"
    )
    journal = "📄 Журнал ✅" if settings["journal"] else "📄 Журнал ❌"
    action = settings["action"]

    moderation_texts = {
        "ban": "бана.",
        "kick": "",
        "mute": "обеззвучивания.",
        "warn": "",
    }
    mute_text = (
        f"⏳ Длительность {moderation_texts.get(action, 'наказания.')}"
        if action not in ["kick", "warn"]
        else None
    )

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=enable_status, callback_data="af:switch")
    )
    builder.row(
        InlineKeyboardButton(text="📄 Сообщения", callback_data="af:msgs"),
        InlineKeyboardButton(text="🕓 Время", callback_data="af:time"),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"❗ Предупреждение {'✅' if action == 'warn' else ''}",
            callback_data="af:action:warn",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"❗ Исключить {'✅' if action == 'kick' else ''}",
            callback_data="af:action:kick",
        ),
        InlineKeyboardButton(
            text=f"🎧 Обеззвучить {'✅' if action == 'mute' else ''}",
            callback_data="af:action:mute",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🚫 Заблокировать {'✅' if action == 'ban' else ''}",
            callback_data="af:action:ban",
        )
    )

    if mute_text:
        builder.row(
            InlineKeyboardButton(text=mute_text, callback_data="af:duration")
        )

    builder.row(
        InlineKeyboardButton(
            text=delete_status, callback_data="af:delete_messages"
        )
    )
    builder.row(
        InlineKeyboardButton(text=journal, callback_data="af:journal:")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )

    return builder.as_markup()


async def numbers_keyboard(chat_id, action):
    builder = InlineKeyboardBuilder()
    settings = await get_antiflood_settings(chat_id)
    selected_value = str(settings[action])

    buttons = [["2", "3", "4", "5"], ["6", "7", "8", "9"], ["10", "12", "15", "20"]]

    for row in buttons:
        builder.row(
            *[
                InlineKeyboardButton(
                    text=f"{btn} ✅" if btn == selected_value else btn,
                    callback_data=f"edit:af:{action}:{btn}:{chat_id}",
                )
                for btn in row
            ]
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"af:back:{chat_id}")
    )

    return builder.as_markup()


async def back_to_antiflood(chat_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"af:back:{chat_id}")
    )
    return builder.as_markup()
