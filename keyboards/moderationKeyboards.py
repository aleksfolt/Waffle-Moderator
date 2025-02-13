from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.blockChannels import get_block_channels_settings
from database.moderation import get_moderation_settings
from database.reports import get_report_settings
from database.warns import get_warn_settings


async def get_moderation_action_kb(user_id: int, action: str):
    buttons = []

    if action == "mute":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔊 Размутить", callback_data=f"unmute:{user_id}"
                )
            ]
        )
    elif action == "ban":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Разбанить", callback_data=f"unban:{user_id}"
                )
            ]
        )
    elif action != "kick":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="➖ Убрать предупреждение",
                    callback_data=f"decrease_warn:{user_id}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def edit_message_kb(chat_id: int, action: str, media: Optional[bool] = None):
    builder = InlineKeyboardBuilder()

    buttons = [
        InlineKeyboardButton(
            text="📄 Текст", callback_data=f"edit:{action}:text:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🔡 URL - кнопки", callback_data=f"edit:{action}:buttons:{chat_id}"
        ),
        InlineKeyboardButton(
            text="👀 Предпросмотр", callback_data=f"edit:{action}:preview:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🔙 Назад", callback_data=f"edit:{action}:back:{chat_id}"
        ),
    ]

    if media:
        buttons.insert(
            2,
            InlineKeyboardButton(
                text="📷 Медиа", callback_data=f"edit:{action}:media:{chat_id}"
            ),
        )

    builder.add(*buttons)
    builder.adjust(2, 1, 1)

    return builder.as_markup()


async def report_kb(chat_id):
    settings = await get_report_settings(chat_id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if settings['enable_reports'] else '❌'} Включено",
            callback_data="report:switch",
        ),
        InlineKeyboardButton(
            text=f"{'✅' if settings['delete_reported_messages'] else '❌'} 🗑️ Удалять сообщение",
            callback_data="report:delete_message",
        ),
        InlineKeyboardButton(
            text="📩 Настроить сообщение", callback_data="report:settings"
        ),
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}"),
    )
    builder.adjust(1)
    return builder.as_markup()


async def moderation_kb(chat_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔇 Муты", callback_data="moderation:mute"
        ),
        InlineKeyboardButton(text="🚫 Баны", callback_data="moderation:ban"),
        InlineKeyboardButton(text="🔕 Кик", callback_data="moderation:kick"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}"),
    )
    builder.adjust(1)
    return builder.as_markup()


async def channels_kb(chat_id):
    settings = await get_block_channels_settings(chat_id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if settings['enable'] else '❌'} Включено",
            callback_data=f"channel:switch:{chat_id}",
        ),
        InlineKeyboardButton(
            text="📩 Настроить сообщение", callback_data=f"channel:settings:{chat_id}"
        ),
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}"),
    )
    builder.adjust(1)
    return builder.as_markup()


async def moderations_kb(chat_id, action):
    moderation_settings = await get_moderation_settings(chat_id)
    settings = moderation_settings[str(action)]

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if settings['enabled'] else '❌'} Включено",
            callback_data=f"s:{action}:switch",
        ),
        InlineKeyboardButton(
            text=f"{'✅' if settings['journal'] else '❌'} Журнал",
            callback_data=f"s:{action}:journal",
        ),
        InlineKeyboardButton(
            text=f"{'✅' if settings['delete_message'] else '❌'} 🗑️ Удалять сообщение",
            callback_data=f"s:{action}:delete_message",
        ),
        InlineKeyboardButton(
            text="📩 Настроить сообщение",
            callback_data=f"s:{action}:settings",
        ),
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=f"edit:moderation:mback:{chat_id}"
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


async def edit_message_text_kb(
    chat_id: int, action: str, to_delete: Optional[str] = None
):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"🚫 Удалить {action}",
            callback_data=f"edit:{action}:del{to_delete}:{chat_id}",
        ),
        InlineKeyboardButton(
            text="❌ Отмена", callback_data=f"edit:{action}:back_to_edit:{chat_id}"
        ),
    )
    return builder.as_markup()


async def back_kb(chat_id: int, action: str):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=f"edit:{action}:back_to_edit:{chat_id}"
        )
    )
    return builder.as_markup()


async def warns_kb(chat_id):
    chat_id = int(chat_id)
    settings = await get_warn_settings(chat_id)
    enable_status = "✅ Вкл" if settings["enable"] else "✖️ Выкл"
    current_warns = settings["warns_count"]
    action = settings["action"]
    moderation_texts = {"ban": "бана.", "kick": "", "mute": "обеззвучивания."}
    mute_text = (
        f"⏳ Длительность {moderation_texts.get(action, 'наказания.')}"
        if action != "kick"
        else None
    )
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=enable_status, callback_data="warn:switch")
    )
    builder.row(
        InlineKeyboardButton(
            text="❗ Исключить", callback_data="warn:action:kick"
        ),
        InlineKeyboardButton(
            text="🎧 Обеззвучить", callback_data="warn:action:mute"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🚫 Заблокировать", callback_data="warn:action:ban"
        )
    )
    if mute_text:
        builder.row(
            InlineKeyboardButton(
                text=mute_text, callback_data="warn:duration"
            )
        )

    number_buttons = []
    for button in range(1, 7):
        mark = " ✅" if button == current_warns else ""
        number_buttons.append(
            InlineKeyboardButton(
                text=f"{button}{mark}", callback_data=f"warn:count:{button}"
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="📩 Настроить сообщение", callback_data="warn:settings"
        )
    )

    builder.row(*number_buttons)
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )

    return builder.as_markup()


async def back_to_warns(chat_id):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"warn:back:{chat_id}")
    )
    return builder.as_markup()
