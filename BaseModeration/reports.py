from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


from BaseModeration.BaseModerationHelpers import format_keyboard
from database.reports import get_report_settings, save_report_settings
from keyboards.moderationKeyboards import (
    edit_message_kb,
    edit_message_text_kb,
    report_kb,
)
from utils.states import EditForm, ModStates
from utils.texts import BUTTONS_MESSAGE, REPORT_MESSAGE

report_router = Router()

TEXTS = {
    "main": (
        "<b>🆘 /report</b>\n"
        "Это команда, доступная пользователям для привлечения внимания персонала группы.\n"
        "Например, если какой-либо другой пользователь не соблюдает правила группы.\n\n"
        "В этом меню вы можете указать:\n"
        "- Куда вы хотите, чтобы отчеты, сделанные пользователями, отправлялись.\n"
        "- Нужно ли помечать некоторый персонал напрямую.\n\n"
        "⚠️ Команда <b>/report</b> НЕ работает, если используется администратором с "
        'разрешением "Блокировка пользователей".\n'
    ),
    "settings_view": (
        "📜 Репорты\n\n"
        "📄 Текст: {} {}\n\n"
        "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "status": ("\n<b>{} {}</b>"),
    "edit_text": (
        "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён)."
    ),
    "errors": {
        "no_reply": "Ответь на сообщение, на которое хочешь пожаловаться.",
        "private_chat": "Эта команда работает только в группах.",
    },
    "report_template": (
        "Поступила жалоба на сообщение из чата {} (ID чата: {})\n\n"
        "Отправитель: {} (ID пользователя: {})\n"
        "Ссылка на сообщение: https://t.me/c/{}/{}"
    ),
    "default_report_text": "Репорт отправлен.",
    "default_response": "Ваша жалоба была отправлена администраторам.",
    "statuses": {
        "enabled": "Включено",
        "disabled": "Выключено",
        "delete_enabled": "Удалять сообщение",
        "delete_disabled": "Удалять сообщение",
    },
}


async def get_chat_administrators(message, chat_id):
    admins = await message.bot.get_chat_administrators(chat_id)
    return [
        admin.user.id
        for admin in admins
        if (getattr(admin, "can_restrict_members", False) or admin.status == "creator")
    ]


@report_router.callback_query(F.data.startswith("reports:"))
async def reports(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    await callback.message.edit_text(
        text=TEXTS["main"], reply_markup=await report_kb(chat_id), parse_mode="HTML"
    )


@report_router.callback_query(F.data.startswith("report:"))
async def report_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))
    action = callback.data.split(":")[-1]
    settings = await get_report_settings(chat_id)

    match action:
        case "switch":
            enable = not settings["enable_reports"]
            await save_report_settings(chat_id, enable_reports=enable)

            status = TEXTS["status"].format(
                "✅" if enable else "❌",
                (
                    TEXTS["statuses"]["enabled"]
                    if enable
                    else TEXTS["statuses"]["disabled"]
                ),
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status,
                reply_markup=await report_kb(chat_id),
                parse_mode="HTML",
            )

        case "delete_message":
            delete = not settings["delete_reported_messages"]
            await save_report_settings(chat_id, delete_reported_messages=delete)

            status = TEXTS["status"].format(
                "✅" if delete else "❌",
                (
                    TEXTS["statuses"]["delete_enabled"]
                    if delete
                    else TEXTS["statuses"]["delete_disabled"]
                ),
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status,
                reply_markup=await report_kb(chat_id),
                parse_mode="HTML",
            )

        case "settings":
            text_status = "✅" if settings["report_text_template"] else "❌"
            await callback.message.edit_text(
                text=TEXTS["settings_view"].format(
                    text_status, settings["report_text_template"]
                ),
                reply_markup=await edit_message_kb(chat_id, "report"),
                parse_mode="HTML",
            )


async def handle_report_callback(
    callback: CallbackQuery, target: str, state: FSMContext
):
    data = await state.get_data()
    chat_id = data.get("chat_id")

    match target:
        case "text":
            await callback.message.edit_text(
                text=TEXTS["edit_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "report", to_delete="text"
                ),
                parse_mode="HTML",
            )
            await state.set_state(EditForm.TEXT)

        case "buttons":
            await callback.message.edit_text(
                text=BUTTONS_MESSAGE,
                reply_markup=await edit_message_text_kb(
                    chat_id, "report", to_delete="buttons"
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            await state.set_state(EditForm.BUTTONS)

        case "preview":
            settings = await get_report_settings(chat_id)
            await callback.message.edit_text(
                text=settings["report_text_template"],
                reply_markup=await format_keyboard(settings["buttons"]),
                parse_mode="HTML",
            )
            text_status = "✅" if settings["report_text_template"] else "❌"
            await callback.message.answer(
                text=TEXTS["settings_view"].format(
                    text_status, settings["report_text_template"]
                ),
                reply_markup=await edit_message_kb(chat_id, "report"),
                parse_mode="HTML",
            )

        case target if target.startswith("del"):
            to_del = target.split("del")[1]
            match to_del:
                case "text":
                    await save_report_settings(
                        chat_id, report_text_template=TEXTS["default_report_text"]
                    )
                case "buttons":
                    await save_report_settings(chat_id, buttons=[])

            settings = await get_report_settings(chat_id)
            text_status = "✅" if settings["report_text_template"] else "❌"
            await callback.message.edit_text(
                text=TEXTS["settings_view"].format(
                    text_status, settings["report_text_template"]
                ),
                reply_markup=await edit_message_kb(chat_id, "report"),
                parse_mode="HTML",
            )
            await state.clear()

        case "back":
            await callback.message.edit_text(
                text=REPORT_MESSAGE,
                reply_markup=await report_kb(chat_id),
                parse_mode="HTML",
            )

        case "back_to_edit":
            settings = await get_report_settings(chat_id)
            text_status = "✅" if settings["report_text_template"] else "❌"
            await callback.message.edit_text(
                text=TEXTS["settings_view"].format(
                    text_status, settings["report_text_template"]
                ),
                reply_markup=await edit_message_kb(chat_id, "report"),
                parse_mode="HTML",
            )
            await state.clear()


@report_router.message(Command("report", ignore_case=True))
async def handle_report(message: Message):
    if message.chat.type == "private":
        await message.reply(TEXTS["errors"]["private_chat"])
        return

    if not message.reply_to_message:
        await message.reply(TEXTS["errors"]["no_reply"])
        return

    chat_id = message.chat.id
    settings = await get_report_settings(chat_id)

    if not settings["enable_reports"]:
        return

    admins = await get_chat_administrators(message, chat_id)

    if message.from_user.id in admins:
        return

    report_message = TEXTS["report_template"].format(
        message.chat.title,
        message.chat.id,
        message.from_user.full_name,
        message.from_user.id,
        str(message.chat.id)[4:],
        message.reply_to_message.message_id,
    )

    sent_count = 0
    for admin_id in admins:
        try:
            await message.bot.send_message(admin_id, report_message, parse_mode="HTML")
            sent_count += 1
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            continue


    await message.reply(
        settings.get("report_text_template", TEXTS["default_response"]),
        reply_markup=await format_keyboard(settings.get("buttons", [])),
        parse_mode="HTML",
    )

    if settings.get("delete_reported_messages"):
        try:
            await message.reply_to_message.delete()
        except TelegramBadRequest as e:
            print(f"Failed to delete reported message in chat {chat_id}: {e}")
