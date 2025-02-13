from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from BaseModeration.BaseModerationHelpers import (
    format_keyboard,
    format_text,
    get_captcha_keyboard,
    handle_welcome_message,
    is_user_restricted,
    restrict_user,
    unrestrict_user,
)
from database.captcha import get_captcha_settings
from database.meeting import (
    get_meeting_settings,
    get_user_meeting_history,
    save_meeting_settings,
)
from keyboards.meetingKeyboards import meeting_kb
from keyboards.moderationKeyboards import edit_message_kb, edit_message_text_kb
from utils.states import EditForm, ModStates
from utils.texts import BUTTONS_MESSAGE

meeting_router = Router()


TEXTS = {
    "main": (
        "💬 Приветственное сообщение\n\n"
        "В этом меню вы можете установить приветственное сообщение, которое будет отправлено, когда пользователь присоединяется к группе.\n\n"
        "<b>Статус:</b> {}\n"
        "<b>Режим:</b> {}"
    ),
    "settings": (
        "📄 Текст: {} {}\n\n" "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": (
        "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён)."
    ),
    "media_text": (
        "👉🏻 Отправьте ссылку на медиа в формате (example.com/video<b>.mp4</b>):"
    ),
}


@meeting_router.message(F.new_chat_members)
async def new_chat_member(message: Message):
    captcha_settings = await get_captcha_settings(message.chat.id)
    meeting_settings = await get_meeting_settings(message.chat.id)

    if not captcha_settings["enable"]:
        return await handle_welcome_message(message)

    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue

        if await is_user_restricted(message.bot, message.chat.id, new_member.id):
            continue

        history = await get_user_meeting_history(message.chat.id, new_member.id)
        if not meeting_settings["always_send"] and history is not None:
            continue

        if not await restrict_user(message.bot, message.chat.id, new_member.id):
            continue

        try:
            welcome_text = (
                f"👋 Привет, {new_member.mention_html()}!\n"
                f"Для доступа к чату, пожалуйста, подтвердите, что вы не робот."
            )

            captcha_text = await format_text(
                template=welcome_text,
                message=message,
                target_user_id=new_member.id,
                target_first_name=new_member.first_name,
            )

            await message.answer(
                text=captcha_text,
                reply_markup=await get_captcha_keyboard(new_member.id),
                parse_mode="HTML",
            )

        except Exception as e:
            print(f"Error sending captcha message: {e}")
            await unrestrict_user(message.bot, message.chat.id, new_member.id)


@meeting_router.callback_query(F.data.startswith("cunmute:"))
async def handle_captcha_callback(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    if callback.from_user.id != user_id:
        await callback.answer("Это не ваша капча!", show_alert=True)
        return

    try:
        if await unrestrict_user(callback.bot, callback.message.chat.id, user_id):
            await callback.message.delete()

            class CustomMessage:
                def __init__(self, chat_id, from_user, bot):
                    class Chat:
                        def __init__(self, chat_id, title=None):
                            self.id = chat_id
                            self.title = title

                    self.chat = Chat(chat_id, title=None)
                    self.from_user = from_user
                    self.bot = bot
                    self.new_chat_members = [from_user]
                    self.message_id = 0

                async def answer(self, **kwargs):
                    msg = await self.bot.send_message(chat_id=self.chat.id, **kwargs)
                    self.message_id = msg.message_id
                    return msg

                async def reply(self, **kwargs):
                    msg = await self.bot.send_message(chat_id=self.chat.id, **kwargs)
                    self.message_id = msg.message_id
                    return msg

            chat_title = None
            chat_title = callback.message.chat.title

            custom_message = CustomMessage(
                chat_id=callback.message.chat.id,
                from_user=callback.from_user,
                bot=callback.bot,
            )
            custom_message.chat.title = chat_title

            await handle_welcome_message(custom_message)

    except Exception as e:
        print(f"Error handling captcha callback: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)


@meeting_router.callback_query(F.data.startswith("meetings:"))
async def meetings_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.data.split(":")[-1]
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    settings = await get_meeting_settings(chat_id)
    await callback.message.edit_text(
        text=TEXTS["main"].format(
            "✅ Включено" if settings["enable"] else "❌ Выключено",
            (
                "отправка приветствия при каждом присоединении пользователей в группе"
                if settings["always_send"]
                else "отправка приветствия только при первом вступлении пользователя в группу"
            ),
        ),
        reply_markup=await meeting_kb(chat_id),
        parse_mode="HTML",
    )


@meeting_router.callback_query(F.data.startswith("meeting:"))
async def meeting_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))

    match action:
        case "switch":
            settings = await get_meeting_settings(chat_id)
            enable = not settings["enable"]
            await save_meeting_settings(chat_id=chat_id, enable=enable)

            status = "✅ Включено" if enable else "❌ Выключено"
            await callback.message.edit_text(
                text=TEXTS["main"].format(
                    status,
                    (
                        "отправка приветствия при каждом присоединении пользователей в группе"
                        if settings["always_send"]
                        else "отправка приветствия только при первом вступлении пользователя в группу"
                    ),
                ),
                reply_markup=await meeting_kb(chat_id),
                parse_mode="HTML",
            )
        case "delete_last_message":
            settings = await get_meeting_settings(chat_id)
            delete = not settings["delete_last_message"]
            await save_meeting_settings(chat_id=chat_id, delete_last_message=delete)

            status = "✅ Включено" if settings["enable"] else "❌ Выключено"
            await callback.message.edit_text(
                text=TEXTS["main"].format(
                    status,
                    (
                        "отправка приветствия при каждом присоединении пользователей в группе"
                        if settings["always_send"]
                        else "отправка приветствия только при первом вступлении пользователя в группу"
                    ),
                ),
                reply_markup=await meeting_kb(chat_id),
                parse_mode="HTML",
            )
        case "send":
            send_mode = callback.data.split(":")[2]
            await save_meeting_settings(
                chat_id=chat_id, always_send=(send_mode == "always")
            )
            updated_settings = await get_meeting_settings(chat_id)
            status = "✅ Включено" if updated_settings["enable"] else "❌ Выключено"

            await callback.message.edit_text(
                text=TEXTS["main"].format(
                    status,
                    (
                        "отправка приветствия при каждом присоединении пользователей в группе"
                        if updated_settings["always_send"]
                        else "отправка приветствия только при первом вступлении пользователя в группу"
                    ),
                ),
                reply_markup=await meeting_kb(chat_id),
                parse_mode="HTML",
            )
        case "settings":
            settings = await get_meeting_settings(chat_id)
            text = settings["text"] or "Не установлен"
            status = "✅" if settings["enable"] else "❌"
            await callback.message.edit_text(
                text=TEXTS["settings"].format(status, text),
                reply_markup=await edit_message_kb(chat_id, "meeting", True),
                parse_mode="HTML",
            )


async def handle_meeting_callback(
    callback: CallbackQuery, target: str, state: FSMContext
):
    chat_id = int(callback.data.split(":")[-1])
    match target:
        case "back":
            settings = await get_meeting_settings(chat_id)
            status = "✅ Включено" if settings["enable"] else "❌ Выключено"
            await callback.message.edit_text(
                text=TEXTS["main"].format(
                    status,
                    (
                        "отправка приветствия при каждом присоединении пользователей в группе"
                        if settings["always_send"]
                        else "отправка приветствия только при первом вступлении пользователя в группу"
                    ),
                ),
                reply_markup=await meeting_kb(chat_id),
                parse_mode="HTML",
            )

        case "text":
            await state.set_state(EditForm.TEXT)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["edit_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "meeting", to_delete="text"
                ),
            )
        case "buttons":
            await state.set_state(EditForm.BUTTONS)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=BUTTONS_MESSAGE,
                reply_markup=await edit_message_text_kb(
                    chat_id, "meeting", to_delete="button"
                ),
                disable_web_page_preview=True,
            )
        case "media":
            await state.set_state(EditForm.MEDIA)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["media_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "meeting", to_delete="media"
                ),
                parse_mode="HTML",
            )
        case "back_to_edit":
            settings = await get_meeting_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            text = settings["text"] or "Не установлен"
            await callback.message.edit_text(
                text=TEXTS["settings"].format(status, text),
                reply_markup=await edit_message_kb(chat_id, "meeting", True),
                parse_mode="HTML",
            )
            await state.clear()
            await state.set_state(ModStates.managing_chat)
            await state.update_data(chat_id=chat_id)
        case "deltext" | "delbutton":
            to_del = target.split("del")[1]

            match to_del:
                case "text":
                    await save_meeting_settings(
                        chat_id=chat_id, text="Приветственное сообщение"
                    )
                case "button":
                    await save_meeting_settings(chat_id=chat_id, buttons=[])
            settings = await get_meeting_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            text = settings["text"] or "Не установлен"
            await state.clear()
            await state.set_state(ModStates.managing_chat)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(status, text),
                reply_markup=await edit_message_kb(chat_id, "meeting", True),
                parse_mode="HTML",
            )
        case "preview":
            settings = await get_meeting_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            text = settings["text"] or "Не установлен"
            await callback.message.edit_text(
                text=settings["text"][:50] + "..." if len(text) > 50 else text,
                reply_markup=await format_keyboard(settings["buttons"]),
                parse_mode="HTML",
            )
            await callback.message.answer(
                text=TEXTS["settings"].format(status, text),
                reply_markup=await edit_message_kb(chat_id, "meeting", True),
                parse_mode="HTML",
            )
