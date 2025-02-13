from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from BaseModeration.BaseModerationHelpers import format_keyboard
from database.blockChannels import (
    get_block_channels_settings,
    save_block_channels_settings,
)
from keyboards.moderationKeyboards import (
    channels_kb,
    edit_message_kb,
    edit_message_text_kb,
)
from utils.states import EditForm
from utils.texts import BUTTONS_MESSAGE, CHANNELS_MESSAGE

channels_router = Router()


default_settings = {
    "enable": False,
    "text": "**⛔️В группе запрещены сообщения от каналов!**",
}

TEXTS = {
    "main": (
        "😶‍🌫️ Пользователи в масках\n"
        "Этот параметр блокирует сообщения от пользователей, пишущих через каналы.\n\n"
        "ℹ️ Telegram позволяет скрывать личность, отправляя сообщения от имени канала.\n\n"
        "👮🏻‍♂️ Блокировка применяется ко всем сообщениям, отправленным через каналы.\n\n"
        "🏃🏻 Если включено, писать в группу можно только от своего имени, а не через каналы."
    ),
    "status": "\n\n<b>{} {}</b>",
    "settings": (
        "😶‍🌫️ Пользователи в масках\n\n"
        "📄 Текст: {} {}\n\n"
        "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён).",
}


@channels_router.callback_query(F.data.startswith("channels:"))
async def channels(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state
    await callback.message.edit_text(
        text=TEXTS["main"], reply_markup=await channels_kb(chat_id), parse_mode="HTML"
    )


@channels_router.callback_query(F.data.startswith("channel:"))
async def channel_callback(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[2])
    action = callback.data.split(":")[1]

    match action:
        case "switch":
            settings = await get_block_channels_settings(chat_id)
            enable = not settings["enable"]
            await save_block_channels_settings(chat_id, enable=enable)

            status = TEXTS["status"].format(
                "✅" if enable else "❌", "Включено" if enable else "Выключено"
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status,
                reply_markup=await channels_kb(chat_id),
                parse_mode="HTML",
            )

        case "settings":
            settings = await get_block_channels_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "channels"),
                parse_mode="HTML",
            )


async def handle_channels_callback(
    callback: CallbackQuery, target: str, state: FSMContext
):
    data = await state.get_data()
    chat_id = data.get("chat_id")

    match target:
        case "text":
            await callback.message.edit_text(
                text=TEXTS["edit_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "channels", to_delete="text"
                ),
                parse_mode="HTML",
            )
            await state.set_state(EditForm.TEXT)

        case "buttons":
            await callback.message.edit_text(
                text=BUTTONS_MESSAGE,
                reply_markup=await edit_message_text_kb(
                    chat_id, "channels", to_delete="buttons"
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            await state.set_state(EditForm.BUTTONS)

        case "preview":
            settings = await get_block_channels_settings(chat_id)
            await callback.message.edit_text(
                text=settings["text"],
                reply_markup=await format_keyboard(settings["buttons"]),
                parse_mode="HTML",
            )
            await callback.message.answer(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "channels"),
                parse_mode="HTML",
            )

        case target if target.startswith("del"):
            to_del = target.split("del")[1]
            match to_del:
                case "text":
                    await save_block_channels_settings(
                        chat_id, text="Обнаружен канал! Удаляю."
                    )
                case _:
                    await save_block_channels_settings(chat_id, buttons=[])

            settings = await get_block_channels_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "channels"),
                parse_mode="HTML",
            )

        case "back":
            await callback.message.edit_text(
                text=CHANNELS_MESSAGE,
                reply_markup=await channels_kb(chat_id),
                parse_mode="HTML",
            )

        case "back_to_edit":
            settings = await get_block_channels_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "channels"),
                parse_mode="HTML",
            )
            await state.clear()


@channels_router.message(F.sender_chat)
async def ban_channels(msg: Message):
    if msg.sender_chat.type == "channel":
        chat_id = msg.chat.id
        channel_id = msg.sender_chat.id

        settings = await get_block_channels_settings(chat_id)
        if settings is None:
            enable = default_settings["enable"]
            text = default_settings["text"]
        else:
            enable = settings.enable
            text = settings.text

        if enable:
            try:
                await msg.delete()
                await msg.bot.ban_chat_sender_chat(
                    chat_id=chat_id, sender_chat_id=channel_id
                )
                await msg.answer(text)
            except Exception as e:
                print(f"Error: {e}")
