import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from BaseModeration.BaseModerationHelpers import (
    apply_punishment,
    format_text,
    parse_seconds_time,
)
from database.utils import get_user_by_id_or_username
from database.warns import (
    add_warn,
    get_warn_settings,
    get_warns_count,
    remove_warn,
    reset_warns,
    save_warn_settings,
)
from keyboards.moderationKeyboards import (
    back_to_warns,
    edit_message_kb,
    edit_message_text_kb,
    get_moderation_action_kb,
    warns_kb,
)
from middlefilters.HasPromoteRights import HasPromoteRights
from utils.states import EditForm, warnForm, ModStates

warns_router = Router()

TEXTS = {
    "main": (
        "❗️Предупреждение пользователей\n"
        "Система предупреждений позволяет выдавать предупреждения пользователям за их "
        "некорректное поведение в группе, прежде чем наказывать их.\n\n"
        "В этом меню вы можете установить:\n"
        "• наказание для пользователей, превысивших допустимое число предупреждений\n"
        "• допустимое число предупреждений"
    ),
    "time_input": (
        "⏱ <b>Установка длительности наказания</b>\n\n"
        "Отправьте сейчас длительность выбранного наказания\n"
        "└ Минимум: 30 секунд\n"
        "└ Максимум: 365 дней\n\n"
        "Пример формата:\n"
        "└ 3 m, 2 d, 12 h, 4 m, 34 s\n\n"
        "Обозначения:\n"
        "└ d - дни\n"
        "└ h - часы\n"
        "└ m - минуты\n"
        "└ s - секунды"
    ),
    "settings_view": (
        "❗️ Предупреждения\n\n"
        "📄 Текст: {} {}\n\n"
        "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": (
        "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён)."
    ),
    "status": ("\n\n<b>{} {}</b>"),
    "errors": {
        "warns_disabled": "⚠️ Варны отключены в этом чате.",
        "user_not_found": "❌ Не удалось определить пользователя для варна.",
        "buttons_unavailable": "❌ Кнопки не доступны для команд модерации",
        "invalid_time": "❌ Неверный формат времени",
        "no_warns": "❌ У пользователя нет предупреждений",
    },
    "success": {
        "saved": "✅ Успешно сохранено!",
        "action_set": "\n\n<b>✅ Установлено {}</b>",
        "warns_set": "\n\n<b>✅ Установлено {} предупреждений</b>",
        "warn_decreased": "✅ Количество предупреждений уменьшено для {}",
        "unwarn": "✅ Предупреждения сброшены для {}",
    },
    "warnings": {
        "max_reached": "🚨 {} Достиг максимального количества предупреждений.\n{}!"
    },
    "moderation_actions": {
        "ban": "бан.",
        "kick": "кик из чата.",
        "mute": "обеззвучивание.",
    },
    "punishments": {
        "mute": "🔇 Мут {}.",
        "ban": "🚫 Бан {}",
        "kick": "👢 Кик из чата.",
        "error": "❌ Ошибка: {}",
    },
    "default_text": "%%__mention__%% [%%__user_id__%%] предупрежден (%%__warn_count__%%/%%__max_warns__%%).",
    "default_reason": "Без причины",
}


@warns_router.callback_query(F.data.startswith("warns"))
async def warns_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.data.split(":")[1]
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    await callback.message.edit_text(
        TEXTS["main"], reply_markup=await warns_kb(chat_id)
    )


@warns_router.callback_query(F.data.startswith("warn:"))
async def warn_callback(callback: CallbackQuery, state: FSMContext) -> None:
    data = callback.data.split(":")
    action = data[1]
    state_data = await state.get_data()
    chat_id = int(state_data.get("chat_id"))

    match action:
        case "switch":
            settings = await get_warn_settings(chat_id)
            enable = not settings["enable"]
            await save_warn_settings(chat_id, enable=enable)

            await callback.message.edit_text(
                text=TEXTS["main"] + TEXTS["status"].format(
                    "✅" if enable else "❌",
                    "Включено" if enable else "Выключено"
                ),
                reply_markup=await warns_kb(chat_id),
                parse_mode="HTML"
            )

        case "action":
            action_type = data[2]
            await save_warn_settings(chat_id, action=action_type)

            await callback.message.edit_text(
                text=TEXTS["main"] + TEXTS["success"]["action_set"].format(
                    TEXTS["moderation_actions"][action_type]
                ),
                reply_markup=await warns_kb(chat_id),
                parse_mode="HTML"
            )

        case "count":
            count = int(data[2])
            await save_warn_settings(chat_id, warns_count=count)

            await callback.message.edit_text(
                text=TEXTS["main"] + TEXTS["success"]["warns_set"].format(count),
                reply_markup=await warns_kb(chat_id),
                parse_mode="HTML"
            )

        case "duration":
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["time_input"],
                reply_markup=await back_to_warns(chat_id)
            )
            await state.set_state(warnForm.DURATION)

        case "back":
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await warns_kb(chat_id),
                parse_mode="HTML"
            )
            await state.clear()

        case "settings":
            settings = await get_warn_settings(chat_id)
            text_status = "✅" if settings["text"] else "❌"

            await callback.message.edit_text(
                text=TEXTS["settings_view"].format(text_status, settings["text"]),
                reply_markup=await edit_message_kb(chat_id, "warn"),
                parse_mode="HTML"
            )


async def handle_warn_callback(callback: CallbackQuery, target: str, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")

    match target:
        case "text":
            await callback.message.edit_text(
                text=TEXTS["edit_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "warn", to_delete="text"
                ),
                parse_mode="HTML",
            )
            await state.set_state(EditForm.TEXT)

        case "buttons":
            await callback.answer(
                TEXTS["errors"]["buttons_unavailable"], show_alert=True
            )

        case "preview":
            settings = await get_warn_settings(chat_id)
            await callback.message.edit_text(text=settings["text"], parse_mode="HTML")
            text_status = "✅" if settings["text"] else "❌"
            await callback.message.answer(
                text=TEXTS["settings_view"].format(text_status, settings["text"]),
                reply_markup=await edit_message_kb(chat_id, "warn"),
                parse_mode="HTML",
            )

        case target if target.startswith("del"):
            await save_warn_settings(chat_id, text=TEXTS["default_text"])
            settings = await get_warn_settings(chat_id)
            text_status = "✅" if settings["text"] else "❌"

            await callback.message.edit_text(
                text=TEXTS["settings_view"].format(text_status, settings["text"]),
                reply_markup=await edit_message_kb(chat_id, "warn"),
                parse_mode="HTML",
            )
            await state.clear()

        case "back":
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await warns_kb(chat_id),
                parse_mode="HTML",
            )
            await state.clear()

        case "back_to_edit":
            settings = await get_warn_settings(chat_id)
            text_status = "✅" if settings["text"] else "❌"

            await callback.message.edit_text(
                text=TEXTS["settings_view"].format(text_status, settings["text"]),
                reply_markup=await edit_message_kb(chat_id, "warn"),
                parse_mode="HTML",
            )
            await state.clear()


@warns_router.message(warnForm.DURATION)
async def warn_duration(msg: Message, state: FSMContext):
    duration = str(msg.text)
    format_duration = str(await parse_seconds_time(duration))
    data = await state.get_data()
    chat_id = data.get("chat_id")

    if format_duration is None:
        await msg.answer(
            "⚠️ Неверный формат. Используйте: 30s, 5m, 2h, 1d, 1w или 1y",
            reply_markup=await back_to_warns(chat_id),
        )
        return

    await save_warn_settings(chat_id, duration_action=format_duration)
    await msg.answer(
        text=TEXTS["success"]["saved"], reply_markup=await back_to_warns(chat_id)
    )
    await state.clear()


async def get_warn_decrease_kb(user_id: int, chat_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➖ Убрать предупреждение",
                    callback_data=f"decrease_warn:{chat_id}:{user_id}",
                )
            ]
        ]
    )


@warns_router.callback_query(F.data.startswith("decrease_warn:"))
async def decrease_warn_callback(callback: CallbackQuery):
    _, chat_id, user_id = callback.data.split(":")
    user_id = int(user_id)
    chat_id = int(chat_id)

    try:
        warns_count = await get_warns_count(chat_id, user_id)
        if warns_count <= 0:
            await callback.answer(TEXTS["errors"]["no_warns"], show_alert=True)
            return

        await remove_warn(chat_id, user_id)
        user = await callback.bot.get_chat_member(chat_id, user_id)
        mention = (
            f"<a href='tg://user?id={user_id}'>{html.escape(user.user.first_name)}</a>"
        )

        await callback.message.edit_text(
            callback.message.text
            + f"\n\n{TEXTS['success']['warn_decreased'].format(mention)}",
            parse_mode="HTML",
        )
    except Exception as e:
        await callback.answer(f"Произошла ошибка: {str(e)}", show_alert=True)


@warns_router.message(Command("warn", ignore_case=True), HasPromoteRights())
async def warn(msg: Message):
    settings = await get_warn_settings(msg.chat.id)
    if not settings["enable"]:
        await msg.answer(TEXTS["errors"]["warns_disabled"])
        return

    target_user = None
    reason = TEXTS["default_reason"]

    if msg.reply_to_message:
        target_user = msg.reply_to_message.from_user
    else:
        args = msg.text.split()[1:]
        if args:
            if args[0].startswith("@"):
                target_user = await get_user_by_id_or_username(username=args[0][1:])
            elif args[0].isdigit():
                target_user = await get_user_by_id_or_username(user_id=int(args[0]))

            if len(args) > 1:
                reason = " ".join(args[1:])

    if not target_user:
        await msg.answer(TEXTS["errors"]["user_not_found"])
        return

    target_user_id = (
        target_user.user_id if hasattr(target_user, "user_id") else target_user.id
    )
    target_first_name = (
        target_user.full_name
        if hasattr(target_user, "full_name")
        else target_user.first_name
    )
    warns_count = await add_warn(msg.chat.id, target_user_id)

    if warns_count >= settings["warns_count"]:
        punishment = await apply_punishment(
            bot=msg.bot,
            chat_id=msg.chat.id,
            user_id=target_user_id,
            action=settings["action"],
            duration=settings["duration_action"],
        )

        warn_text = await format_text(
            template=settings["text"],
            message=msg,
            target_user_id=target_user_id,
            target_first_name=target_first_name,
            duration=str(settings["duration_action"]),
            reason=reason,
        )
        mention = f"<a href='tg://user?id={target_user_id}'>{html.escape(target_first_name)}</a>"
        await msg.answer(
            TEXTS["warnings"]["max_reached"].format(mention, punishment),
            parse_mode="HTML",
            reply_markup=await get_moderation_action_kb(
                target_user_id, settings["action"]
            ),
        )
        await reset_warns(msg.chat.id, target_user_id)
    else:
        warn_text = await format_text(
            template=settings["text"],
            message=msg,
            target_user_id=target_user_id,
            target_first_name=target_first_name,
            reason=reason,
            warns_count=warns_count,
            max_warns=settings["warns_count"],
        )
        await msg.answer(
            warn_text,
            parse_mode="HTML",
            reply_markup=await get_warn_decrease_kb(target_user_id, msg.chat.id),
        )


@warns_router.message(Command("unwarn", ignore_case=True), HasPromoteRights())
async def unwarn(msg: Message):
    settings = await get_warn_settings(msg.chat.id)
    if not settings["enable"]:
        await msg.answer(TEXTS["errors"]["warns_disabled"])
        return

    target_user = None
    if msg.reply_to_message:
        target_user = msg.reply_to_message.from_user
    else:
        args = msg.text.split()[1:]
        if args:
            if args[0].startswith("@"):
                target_user = await get_user_by_id_or_username(username=args[0][1:])
            elif args[0].isdigit():
                target_user = await get_user_by_id_or_username(user_id=int(args[0]))

    if not target_user:
        await msg.answer(TEXTS["errors"]["user_not_found"])
        return

    target_user_id = (
        target_user.user_id if hasattr(target_user, "user_id") else target_user.id
    )
    target_first_name = (
        target_user.full_name
        if hasattr(target_user, "full_name")
        else target_user.first_name
    )

    await reset_warns(msg.chat.id, target_user_id)
    mention = (
        f"<a href='tg://user?id={target_user_id}'>{html.escape(target_first_name)}</a>"
    )
    await msg.answer(TEXTS["success"]["unwarn"].format(mention), parse_mode="HTML")
