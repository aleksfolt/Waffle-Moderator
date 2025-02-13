from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def chat_settings_kb(chat_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Репорты", callback_data=f"reports:{chat_id}"),
        InlineKeyboardButton(text="🔉 Каналы", callback_data=f"channels:{chat_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text="🛠 Модерация", callback_data=f"moderations:{chat_id}"
        ),
        InlineKeyboardButton(text="🗣 Антифлуд", callback_data=f"antiflood:{chat_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="❗️ Варны", callback_data=f"warns:{chat_id}"),
        InlineKeyboardButton(text="🔞 Фильтр NSFW", callback_data=f"fnsfw:{chat_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="📨 Антиспам", callback_data=f"antispam:{chat_id}"),
        InlineKeyboardButton(text="🗒 Правила", callback_data=f"rules:{chat_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text="👋 Приветствия", callback_data=f"meetings:{chat_id}"
        ),
        InlineKeyboardButton(text="♻️ Капча", callback_data=f"captcha:{chat_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 Запретные слова", callback_data=f"forbidden_words:{chat_id}"
        )
    )
    return builder.as_markup()


async def pm_link():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Настроить", url="https://t.me/WaffleModeratorBot?start=login"
        )
    )
    return builder.as_markup()


async def stickers_kb(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🖼 Стикер", callback_data=f"block:sticker:{user_id}"),
        InlineKeyboardButton(
            text="🃏 Набор стикеров", callback_data=f"block:set:{user_id}"
        ),
    )

    builder.adjust(1)
    return builder.as_markup()
