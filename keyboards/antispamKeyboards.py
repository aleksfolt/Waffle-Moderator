from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.antispam import (
    get_all_settings,
    get_forward_settings,
    get_quotes_settings,
    get_tlink_settings,
)


async def antispam_kb(chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📘 Telegram ссылки", callback_data="as:telegram_links"
        )
    )
    builder.row(
        InlineKeyboardButton(text="✉️ Пересылка", callback_data="as:forwarding"),
        InlineKeyboardButton(text="💬 Цитаты", callback_data="as:quotes"),
    )
    builder.row(
        InlineKeyboardButton(text="🔗 Общий блок ссылок", callback_data="as:all")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"edit:main:back:{chat_id}")
    )
    return builder.as_markup()


async def telegram_links_kb(chat_id: int) -> InlineKeyboardMarkup:
    settings = await get_tlink_settings(chat_id)
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Вкл." if settings["enable"] else "❌ Выкл.",
            callback_data="tlinks:switch",
        ),
        InlineKeyboardButton(
            text="❗ Предупреждение" + (" ✓" if settings["action"] == "warn" else ""),
            callback_data="tlinks:action:warn",
        ),
        InlineKeyboardButton(
            text="❕ Исключить" + (" ✓" if settings["action"] == "kick" else ""),
            callback_data="tlinks:action:kick",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔇 Обеззвучить" + (" ✓" if settings["action"] == "mute" else ""),
            callback_data="tlinks:action:mute",
        ),
        InlineKeyboardButton(
            text="🚷 Заблокировать" + (" ✓" if settings["action"] == "ban" else ""),
            callback_data="tlinks:action:ban",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалять сообщения"
            + (" ✅" if settings["delete_message"] else " ❌"),
            callback_data="tlinks:delete_messages",
        )
    )
    if settings["action"] in ["mute", "ban"]:
        builder.row(
            InlineKeyboardButton(
                text="❗⏳ Длительность "
                + ("обеззвучивания" if settings["action"] == "mute" else "блокировки"),
                callback_data="tlinks:duration",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🔑 Имя пользователя Анти-Спам"
            + (" ✅" if settings["username"] else " ❌"),
            callback_data="tlinks:username",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🤖 Бот Анти-Спам" + (" ✅" if settings["bot"] else " ❌"),
            callback_data="tlinks:bot",
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="tlinks:back"),
        InlineKeyboardButton(text="🌟 Исключения", callback_data="tlinks:exceptions"),
    )
    return builder.as_markup()


async def forward_kb(
    chat_id: int, selected_category: Optional[str] = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    settings = None
    if selected_category:
        settings = await get_forward_settings(chat_id, selected_category)

    builder.row(
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'channels' else ' '} 📢 Каналы {'•' if selected_category == 'channels' else ' '}",
            callback_data="forward:settings:channels",
        ),
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'chats' else ' '} 👥 Группы {'•' if selected_category == 'chats' else ' '}",
            callback_data="forward:settings:chats",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'users' else ' '} 👤 Пользователи {'•' if selected_category == 'users' else ' '}",
            callback_data="forward:settings:users",
        ),
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'bots' else ' '} 🤖 Боты {'•' if selected_category == 'bots' else ' '}",
            callback_data="forward:settings:bots",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="➖➖➖➖➖➖➖➖➖➖", callback_data="nothing")
    )

    if selected_category and settings:
        enable_text = "✅ Вкл." if settings["enable"] else "❌ Выкл."
        builder.row(
            InlineKeyboardButton(
                text=enable_text,
                callback_data=f"forward:action:{selected_category}:off",
            ),
            InlineKeyboardButton(
                text="❗ Предупреждение"
                + (" ✓" if settings["action"] == "warn" else ""),
                callback_data=f"forward:action:{selected_category}:warn",
            ),
            InlineKeyboardButton(
                text="❕ Исключить" + (" ✓" if settings["action"] == "kick" else ""),
                callback_data=f"forward:action:{selected_category}:kick",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🔇 Обеззвучить" + (" ✓" if settings["action"] == "mute" else ""),
                callback_data=f"forward:action:{selected_category}:mute",
            ),
            InlineKeyboardButton(
                text="🚫 Заблокировать" + (" ✓" if settings["action"] == "ban" else ""),
                callback_data=f"forward:action:{selected_category}:ban",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑 Удалять сообщения"
                + (" ✅" if settings["delete_message"] else " ❌"),
                callback_data=f"forward:action:{selected_category}:delete_messages",
            )
        )
        if settings["action"] in ["mute", "ban"]:
            builder.row(
                InlineKeyboardButton(
                    text="❗⏳ Длительность "
                    + (
                        "обеззвучивания"
                        if settings["action"] == "mute"
                        else "блокировки"
                    ),
                    callback_data=f"forward:duration:{selected_category}",
                )
            )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="forward:back"),
        InlineKeyboardButton(
            text="🌟 Исключения",
            callback_data=f"forward:exceptions:{selected_category if selected_category else 'none'}",
        ),
    )
    return builder.as_markup()


async def quotes_kb(
    chat_id: int, selected_category: Optional[str] = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    settings = None
    if selected_category:
        settings = await get_quotes_settings(chat_id, selected_category)

    builder.row(
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'channels' else ' '} 📢 Каналы {'•' if selected_category == 'channels' else ' '}",
            callback_data="quotes:settings:channels",
        ),
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'chats' else ' '} 👥 Группы {'•' if selected_category == 'chats' else ' '}",
            callback_data="quotes:settings:chats",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'users' else ' '} 👤 Пользователи {'•' if selected_category == 'users' else ' '}",
            callback_data="quotes:settings:users",
        ),
        InlineKeyboardButton(
            text=f"{'•' if selected_category == 'bots' else ' '} 🤖 Боты {'•' if selected_category == 'bots' else ' '}",
            callback_data="quotes:settings:bots",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="➖➖➖➖➖➖➖➖➖➖", callback_data="nothing")
    )

    if selected_category and settings:
        enable_text = "✅ Вкл." if settings["enable"] else "❌ Выкл."
        builder.row(
            InlineKeyboardButton(
                text=enable_text, callback_data=f"quotes:action:{selected_category}:off"
            ),
            InlineKeyboardButton(
                text="❗ Предупреждение"
                + (" ✓" if settings["action"] == "warn" else ""),
                callback_data=f"quotes:action:{selected_category}:warn",
            ),
            InlineKeyboardButton(
                text="❕ Исключить" + (" ✓" if settings["action"] == "kick" else ""),
                callback_data=f"quotes:action:{selected_category}:kick",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🔇 Обеззвучить" + (" ✓" if settings["action"] == "mute" else ""),
                callback_data=f"quotes:action:{selected_category}:mute",
            ),
            InlineKeyboardButton(
                text="🚫 Заблокировать" + (" ✓" if settings["action"] == "ban" else ""),
                callback_data=f"quotes:action:{selected_category}:ban",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑 Удалять сообщения"
                + (" ✅" if settings["delete_message"] else " ❌"),
                callback_data=f"quotes:action:{selected_category}:delete_messages",
            )
        )
        if settings["action"] in ["mute", "ban"]:
            builder.row(
                InlineKeyboardButton(
                    text="❗⏳ Длительность "
                    + (
                        "обеззвучивания"
                        if settings["action"] == "mute"
                        else "блокировки"
                    ),
                    callback_data=f"quotes:duration:{selected_category}",
                )
            )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="quotes:back"),
        InlineKeyboardButton(
            text="🌟 Исключения",
            callback_data=f"quotes:exceptions:{selected_category if selected_category else 'none'}",
        ),
    )
    return builder.as_markup()


async def cancel_action_kb(
    prefix: str, category: Optional[str] = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"{prefix}:cancel:{category if category else ''}",
        )
    )
    return builder.as_markup()


async def back_action_kb(
    prefix: str, category: Optional[str] = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if prefix == "all":
        callback_data = "all:cancel"
    elif prefix == "tlinks":
        callback_data = "tlinks:cancel"
    else:
        callback_data = f"{prefix}:back:{category if category else ''}"

    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data))
    return builder.as_markup()


async def all_kb(chat_id: int):
    settings = await get_all_settings(chat_id)
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Вкл." if settings["enable"] else "❌ Выкл.",
            callback_data="all:switch",
        ),
        InlineKeyboardButton(
            text="❗ Предупреждение" + (" ✓" if settings["action"] == "warn" else ""),
            callback_data="all:action:warn",
        ),
        InlineKeyboardButton(
            text="❕ Исключить" + (" ✓" if settings["action"] == "kick" else ""),
            callback_data="all:action:kick",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔇 Обеззвучить" + (" ✓" if settings["action"] == "mute" else ""),
            callback_data="all:action:mute",
        ),
        InlineKeyboardButton(
            text="🚫 Заблокировать" + (" ✓" if settings["action"] == "ban" else ""),
            callback_data="all:action:ban",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалять сообщения"
            + (" ✅" if settings["delete_message"] else " ❌"),
            callback_data="all:delete_messages",
        )
    )

    if settings["action"] in ["mute", "ban"]:
        builder.row(
            InlineKeyboardButton(
                text="❗⏳ Длительность "
                + ("обеззвучивания" if settings["action"] == "mute" else "блокировки"),
                callback_data="all:duration",
            )
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="all:back"),
        InlineKeyboardButton(text="🌟 Исключения", callback_data="all:exceptions"),
    )
    return builder.as_markup()
