from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.moderation import get_moderation_settings, save_moderation_settings
from keyboards.moderationKeyboards import (
    edit_message_kb,
    edit_message_text_kb,
    moderation_kb,
    moderations_kb,
)
from utils.states import EditForm, ModStates
from utils.texts import (
    ACTION_INFO,
    BAN_INFO,
    KICK_INFO,
    MUTE_INFO,
    default_moderation_settings,
)

moderation_router = Router()

TEXTS = {
    "main": (
        "🛡 Инструменты модерации\n"
        "Выберите действие:"
    ),
    "status": ("\n\n{} {}"),
    "message_settings": (
        "📜 Модерация\n\n"
        "📄 Текст: {} {}\n\n"
        "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": ("👉🏻 Отправьте сообщение для настройки {} (HTML разрешён)."),
    "buttons_unavailable": ("❌ Кнопки не доступны для команд модерации"),
    "preview_title": ("Настройки сообщения"),
    "default_text": ("Нет текста"),
    "statuses": {
        "enabled": "Включено",
        "disabled": "Отключено",
        "logs_enabled": "Логи в журнал включены",
        "logs_disabled": "Логи в журнал отключены",
        "delete_enabled": "Удаление сообщения включено",
        "delete_disabled": "Удаление сообщения отключено",
    },
}


@moderation_router.callback_query(F.data.startswith("moderations:"))
async def moderation_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    await callback.message.edit_text(
        TEXTS["main"], reply_markup=await moderation_kb(chat_id)
    )


@moderation_router.callback_query(F.data.startswith("moderation:"))
async def moderation_action_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[-1]
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))
    action_texts = {"mute": MUTE_INFO, "ban": BAN_INFO, "kick": KICK_INFO}

    await callback.message.edit_text(
        action_texts[action], reply_markup=await moderations_kb(chat_id, action)
    )


@moderation_router.callback_query(F.data.startswith("s:"))
async def moderation_switch_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[-1]
    moderation_action = callback.data.split(":")[1]
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))
    settings = await get_moderation_settings(chat_id, moderation_action)

    match action:
        case "switch":
            enabled = settings.get(moderation_action, {}).get("enabled", False)
            new_status = not enabled
            await save_moderation_settings(
                chat_id=chat_id, command_type=moderation_action, enabled=new_status
            )

            status = TEXTS["status"].format(
                "✅" if new_status else "❌",
                (
                    TEXTS["statuses"]["enabled"]
                    if new_status
                    else TEXTS["statuses"]["disabled"]
                ),
            )
            await callback.message.edit_text(
                text=ACTION_INFO[moderation_action] + status,
                reply_markup=await moderations_kb(chat_id, moderation_action),
            )

        case "journal":
            enabled = settings.get(moderation_action, {}).get("journal", False)
            new_status = not enabled
            await save_moderation_settings(
                chat_id=chat_id, command_type=moderation_action, journal=new_status
            )

            status = TEXTS["status"].format(
                "✅" if new_status else "❌",
                (
                    TEXTS["statuses"]["logs_enabled"]
                    if new_status
                    else TEXTS["statuses"]["logs_disabled"]
                ),
            )
            await callback.message.edit_text(
                text=ACTION_INFO[moderation_action] + status,
                reply_markup=await moderations_kb(chat_id, moderation_action),
            )

        case "delete_message":
            enabled = settings.get(moderation_action, {}).get("delete_message", False)
            new_status = not enabled
            await save_moderation_settings(
                chat_id=chat_id,
                command_type=moderation_action,
                delete_message=new_status,
            )

            status = TEXTS["status"].format(
                "✅" if new_status else "❌",
                (
                    TEXTS["statuses"]["delete_enabled"]
                    if new_status
                    else TEXTS["statuses"]["delete_disabled"]
                ),
            )
            await callback.message.edit_text(
                text=ACTION_INFO[moderation_action] + status,
                reply_markup=await moderations_kb(chat_id, moderation_action),
            )

        case "settings":
            text_status = (
                "✅" if settings.get(moderation_action, {}).get("text") else "❌"
            )
            text = settings.get(moderation_action, {}).get(
                "text", TEXTS["default_text"]
            )

            await state.update_data(moderation_action=moderation_action)
            await callback.message.edit_text(
                text=TEXTS["message_settings"].format(text_status, text),
                reply_markup=await edit_message_kb(chat_id, "moderation"),
                parse_mode="HTML",
            )


async def handle_moderation_callback(
    callback: CallbackQuery, target: str, state: FSMContext
):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    moderation_action = data.get("moderation_action")
    action_texts = {"mute": MUTE_INFO, "ban": BAN_INFO, "kick": KICK_INFO}

    match target:
        case "text":
            await callback.message.edit_text(
                text=TEXTS["edit_text"].format(moderation_action.upper()),
                reply_markup=await edit_message_text_kb(chat_id, "moderation", "text"),
                parse_mode="HTML",
            )
            await state.set_state(EditForm.TEXT)

        case "buttons":
            await callback.answer(TEXTS["buttons_unavailable"], show_alert=True)

        case "preview":
            settings = await get_moderation_settings(chat_id, moderation_action)
            moderation_text = settings.get(moderation_action, {}).get(
                "text", TEXTS["default_text"]
            )

            await callback.message.edit_text(text=moderation_text, parse_mode="HTML")
            await callback.message.answer(
                text=TEXTS["preview_title"],
                reply_markup=await edit_message_kb(chat_id, "moderation"),
                parse_mode="HTML",
            )

        case target if target.startswith("del"):
            await save_moderation_settings(
                chat_id=chat_id,
                command_type=moderation_action,
                text=default_moderation_settings[moderation_action]["text"],
            )
            settings = await get_moderation_settings(chat_id, moderation_action)
            text_status = (
                "✅" if settings.get(moderation_action, {}).get("text") else "❌"
            )
            text = settings.get(moderation_action, {}).get(
                "text", TEXTS["default_text"]
            )

            await state.update_data(moderation_action=moderation_action)
            await callback.message.edit_text(
                text=TEXTS["message_settings"].format(text_status, text),
                reply_markup=await edit_message_kb(chat_id, "moderation"),
                parse_mode="HTML",
            )

        case "back":
            await callback.message.edit_text(
                text=action_texts[moderation_action],
                reply_markup=await moderations_kb(chat_id, moderation_action),
            )

        case "mback":
            await callback.message.edit_text(
                text=TEXTS["main"], reply_markup=await moderation_kb(chat_id)
            )

        case "back_to_edit":
            settings = await get_moderation_settings(chat_id, moderation_action)
            text_status = (
                "✅" if settings.get(moderation_action, {}).get("text") else "❌"
            )
            text = settings.get(moderation_action, {}).get(
                "text", TEXTS["default_text"]
            )

            await callback.message.edit_text(
                text=TEXTS["message_settings"].format(text_status, text),
                reply_markup=await edit_message_kb(chat_id, "moderation"),
                parse_mode="HTML",
            )
            data = await state.get_data()
            await state.clear()
            await state.update_data(moderation_action=data.get("moderation_action"))
