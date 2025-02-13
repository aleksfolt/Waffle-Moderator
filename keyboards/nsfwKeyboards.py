from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.nsfwFilter import get_nsfwFilter_settings


async def nsfw_kb(chat_id):
    settings = await get_nsfwFilter_settings(chat_id)
    enable = settings["enable"]
    journal = settings["journal"]
    action = settings.get("action", "mute")
    moderation_texts = {
        "ban": "бана.",
        "kick": "",
        "mute": "обеззвучивания.",
        "warn": "",
    }

    mute_text = (
        f"⏳ Длительность {moderation_texts.get(action, 'наказание')}"
        if action not in ["kick", "warn"]
        else None
    )

    toggle_text = "✅ Вкл" if enable else "❌ Выкл"
    journal_text = "📄 Журнал ✅" if journal else "📄 Журнал ❌"

    warn_text = "❗ Предупреждение ✅" if action == "warn" else "❗ Предупреждение"
    kick_text = "❗ Исключить ✅" if action == "kick" else "❗ Исключить"
    mute_text_action = "🎧 Обеззвучить ✅" if action == "mute" else "🎧 Обеззвучить"
    ban_text = "🚫 Заблокировать ✅" if action == "ban" else "🚫 Заблокировать"

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=toggle_text, callback_data="nsfw:switch:")
    )
    builder.row(
        InlineKeyboardButton(
            text="🔞 Процент NSFW", callback_data="nsfw:percentage"
        ),
        InlineKeyboardButton(
            text=journal_text, callback_data="nsfw:journal"
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=warn_text, callback_data="nsfw:action:warn"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=kick_text, callback_data="nsfw:action:kick"
        ),
        InlineKeyboardButton(
            text=mute_text_action, callback_data="nsfw:action:mute"
        ),
    )
    builder.row(
        InlineKeyboardButton(text=ban_text, callback_data="nsfw:action:ban")
    )

    if mute_text:
        builder.row(
            InlineKeyboardButton(
                text=f"{mute_text}", callback_data="nsfw:duration"
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="📩 Настроить сообщение", callback_data="nsfw:settings"
        )
    )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )

    return builder.as_markup()


async def nsfw_back(chat_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"nsfw:back:{chat_id}")
    )
    return builder.as_markup()
