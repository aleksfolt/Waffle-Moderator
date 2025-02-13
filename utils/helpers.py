import validators
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ChatPermissions, Message

from BaseModeration.BaseModerationHelpers import format_buttons
from BaseModeration.moderation import handle_moderation_callback
from BaseModeration.reports import handle_report_callback
from BaseModeration.warns import handle_warn_callback
from database.blockChannels import save_block_channels_settings
from database.meeting import get_meeting_settings, save_meeting_settings
from database.moderation import save_moderation_settings
from database.nsfwFilter import save_nsfwFilter_settings
from database.reports import save_report_settings
from database.rules import save_rules_settings
from database.utils import get_chat
from database.warns import save_warn_settings
from handlers.antiflood import handle_antiflood_callback
from handlers.blockChannels import handle_channels_callback
from handlers.meeting import handle_meeting_callback
from handlers.nsfwFilter import handle_nsfw_callback
from handlers.rules import handle_rules_callback
from keyboards.handlersKeyboards import chat_settings_kb
from keyboards.moderationKeyboards import back_kb
from middlefilters.HasPromoteRights import HasPromoteRights
from utils.states import EditForm

utils_router = Router()


@utils_router.callback_query(
    F.data.startswith(("unmute:", "unban:")), HasPromoteRights()
)
async def moderation_action_callback(callback: CallbackQuery):
    action, user_id = callback.data.split(":")
    user_id = int(user_id)
    chat_id = callback.message.chat.id

    try:
        if action == "unmute":
            await callback.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_voice_notes=True,
                    can_send_video_notes=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                ),
            )
        else:
            await callback.bot.unban_chat_member(chat_id, user_id)

        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Наказание снято.", parse_mode="HTML"
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@utils_router.callback_query(F.data.startswith("edit:"))
async def on_edit_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    action, target, chat_id = parts[1], parts[2], int(parts[-1])

    await state.update_data(action=action, chat_id=chat_id)

    match action:
        case "report":
            await handle_report_callback(callback, target, state)
        case "channels":
            await handle_channels_callback(callback, target, state)
        case "moderation":
            await handle_moderation_callback(callback, target, state)
        case "warn":
            await handle_warn_callback(callback, target, state)
        case "af":
            await handle_antiflood_callback(callback, target, state)
        case "nsfw":
            await handle_nsfw_callback(callback, target, state)
        case "rules":
            await handle_rules_callback(callback, target, state)
        case "meeting":
            await handle_meeting_callback(callback, target, state)
        case "main" if target == "back":
            chat = await get_chat(chat_id)
            await callback.message.edit_text(
                text=f"Настройки группы {chat.title}\n\nВыберите один из параметров:",
                reply_markup=await chat_settings_kb(chat_id),
                parse_mode="HTML",
            )


@utils_router.message(EditForm.TEXT)
async def process_edit_text(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    moderation_action = data.get("moderation_action")
    chat_id = data.get("chat_id")
    print(chat_id, action)
    new_text = message.text

    if action in {"report", "channels", "moderation", "warn", "nsfw"}:
        if len(new_text) > 1024:
            await message.answer("❌ Ошибка: Максимальная длина текста - 1024 символа.")
            return
    elif action in {"rules", "meeting"}:
        if action == "meeting":
            meeting_data = await get_meeting_settings(chat_id)
            if meeting_data and meeting_data.get("media_link"):
                if len(new_text) > 1024:
                    await message.answer(
                        "❌ Ошибка: При наличии медиа максимальная длина текста - 1024 символа."
                    )
                    return
            else:
                if len(new_text) > 4000:
                    await message.answer(
                        "❌ Ошибка: Максимальная длина текста - 4000 символов."
                    )
                    return
        else:  # rules
            if len(new_text) > 4000:
                await message.answer(
                    "❌ Ошибка: Максимальная длина текста - 4000 символов."
                )
                return

    if action == "report":
        await save_report_settings(chat_id=chat_id, report_text_template=new_text)
    elif action == "channels":
        await save_block_channels_settings(chat_id=chat_id, text=new_text)
    elif action == "moderation" and moderation_action in {"mute", "ban", "kick"}:
        await save_moderation_settings(
            chat_id=chat_id, command_type=moderation_action, text=new_text
        )
    elif action == "warn":
        await save_warn_settings(
            chat_id=chat_id,
            text=new_text,
        )
    elif action == "nsfw":
        await save_nsfwFilter_settings(
            chat_id=chat_id,
            text=new_text,
        )
    elif action == "rules":
        await save_rules_settings(chat_id=chat_id, text=new_text)
    elif action == "meeting":
        await save_meeting_settings(chat_id=chat_id, text=new_text)

    data = await state.get_data()
    await state.clear()
    await state.update_data(moderation_action=data.get("moderation_action"))
    await message.answer(
        text="✅ Сообщение сохранено.", reply_markup=await back_kb(chat_id, action)
    )


@utils_router.message(EditForm.BUTTONS)
async def process_edit_buttons(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    chat_id = data.get("chat_id")
    buttons = await format_buttons(message.text)

    if not buttons:
        await message.answer(
            "❌ Ошибка: Неверный формат кнопок.\n"
            "Формат должен быть:\n"
            "текст кнопки - ссылка && текст кнопки - ссылка\n"
            "текст кнопки - ссылка\n\n"
            "Пример:\n"
            "Google - https://google.com && YouTube - https://youtube.com\n"
            "Telegram - https://t.me/username"
        )
        return

    if action == "report":
        await save_report_settings(chat_id=chat_id, buttons=buttons)
    elif action == "channels":
        await save_block_channels_settings(chat_id, buttons=buttons)
    elif action == "rules":
        await save_rules_settings(chat_id=chat_id, buttons=buttons)
    elif action == "meeting":
        await save_meeting_settings(chat_id=chat_id, buttons=buttons)

    await state.clear()
    await message.answer(
        text="✅ Кнопки сохранены.", reply_markup=await back_kb(chat_id, action)
    )


@utils_router.message(EditForm.MEDIA)
async def process_edit_media(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    chat_id = data.get("chat_id")

    if action == "meeting":
        media_link = message.text.strip()

        if not media_link.startswith(("http://", "https://")):
            media_link = "http://" + media_link

        if not validators.url(media_link):
            await message.answer("❌ Ошибка: Введите корректную ссылку.")
            return

        await save_meeting_settings(chat_id=chat_id, media_link=media_link)
        await message.answer(
            "✅ Медиа-ссылка успешно сохранена!",
            reply_markup=await back_kb(chat_id, action),
        )
