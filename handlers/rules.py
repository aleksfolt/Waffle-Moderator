from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from BaseModeration.BaseModerationHelpers import format_keyboard
from database.rules import get_rules_settings, save_rules_settings
from database.utils import get_chat_admins
from keyboards.moderationKeyboards import edit_message_kb, edit_message_text_kb
from keyboards.rulesKeyboards import permissions_kb, rules_kb
from utils.states import EditForm, RulesStates, ModStates
from utils.texts import BUTTONS_MESSAGE

rules_router = Router()


TEXTS = {
    "main": (
        "<b>📜 Правила группы</b>\n"
        "В этом меню вы можете управлять правилами группы, которые будут отображаться с командой /rules.\n\n"
        "Чтобы изменить, кто может использовать команду /rules, перейдите в раздел 'Права на Команды'.\n\n"
        "Статус: {}"
    ),
    "settings": (
        "📄 Текст: {} {}\n\n" "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": (
        "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён)."
    ),
    "permissions": (
        "🕹 <b>Права на Команды</b>\n"
        "В этом меню вы можете настроить права следующих команд.\n\n"
        "✖️ = Никто  |   👥 = Все\n"
        "🤖 = Все, в приватном чате\n"
        "👮🏻 = Администраторы и модераторы\n\n"
        "• /rules » {}"
    ),
}

permissions = {
    "noone": "✖️ Никто",
    "members": "👥 Все",
    "private": "🤖 Приват",
    "admins": "👮🏻 Админ",
}


@rules_router.message(Command("rules", ignore_case=True))
async def rules(msg: Message):
    settings = await get_rules_settings(msg.chat.id)

    if not settings["enable"]:
        return

    match settings["permissions"]:
        case "noone":
            return

        case "admins":
            admin_ids = await get_chat_admins(msg.chat.id)
            if msg.from_user.id not in admin_ids:
                return

        case "private":
            try:
                await msg.bot.send_message(
                    chat_id=msg.from_user.id,
                    text=settings["text"],
                    reply_markup=await format_keyboard(settings["buttons"]),
                    parse_mode="HTML",
                )
                if msg.chat.type != "private":
                    await msg.reply("✅ Правила отправлены вам в личные сообщения.")
            except Exception:
                await msg.reply(
                    "❌ Не удалось отправить правила.\n"
                    "Возможно, вы не начали диалог с ботом. "
                    "Начните диалог и повторите попытку."
                )
            return

        case "members":
            pass

    await msg.reply(
        text=settings["text"],
        reply_markup=await format_keyboard(settings["buttons"]),
        parse_mode="HTML",
    )


@rules_router.callback_query(F.data.startswith("rules:"))
async def rules_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.data.split(":")[-1]
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    settings = await get_rules_settings(chat_id)
    status = "✅" if settings["enable"] else "❌"
    await callback.message.edit_text(
        text=TEXTS["main"].format(status),
        reply_markup=await rules_kb(chat_id),
        parse_mode="HTML",
    )


@rules_router.callback_query(F.data.startswith("srules:"))
async def rules_settings(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))
    action = callback.data.split(":")[1]

    match action:
        case "switch":
            settings = await get_rules_settings(chat_id)
            enable = not settings["enable"]
            await save_rules_settings(chat_id=chat_id, enable=enable)

            text = settings["text"] or "Не установлен"
            status = "✅" if enable else "❌"
            await callback.message.edit_text(
                text=TEXTS["main"].format(status),
                reply_markup=await rules_kb(chat_id),
                parse_mode="HTML",
            )

        case "settings":
            settings = await get_rules_settings(chat_id)
            text = settings["text"] or "Не установлен"
            status = "✅" if settings["enable"] else "❌"
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    text[:50] + "..." if len(text) > 50 else text, status
                ),
                reply_markup=await edit_message_kb(chat_id, "rules"),
                parse_mode="HTML",
            )
        case "permissions":
            settings = await get_rules_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["permissions"].format(permissions[settings["permissions"]]),
                parse_mode="HTML",
                reply_markup=await permissions_kb(chat_id),
            )
        case "epermissions":
            permission = callback.data.split(":")[-1]
            await save_rules_settings(chat_id=chat_id, permissions=permission)
            await callback.message.edit_text(
                text=TEXTS["permissions"].format(permissions[permission]),
                parse_mode="HTML",
                reply_markup=await permissions_kb(chat_id),
            )


async def handle_rules_callback(
    callback: CallbackQuery, target: str, state: FSMContext
):
    chat_id = int(callback.data.split(":")[-1])
    match target:
        case "back":
            settings = await get_rules_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            await callback.message.edit_text(
                text=TEXTS["main"].format(status),
                reply_markup=await rules_kb(chat_id),
                parse_mode="HTML",
            )

        case "text":
            await state.set_state(EditForm.TEXT)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["edit_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "rules", to_delete="text"
                ),
            )
        case "buttons":
            await state.set_state(EditForm.BUTTONS)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=BUTTONS_MESSAGE,
                reply_markup=await edit_message_text_kb(
                    chat_id, "rules", to_delete="button"
                ),
                disable_web_page_preview=True,
            )
        case "back_to_edit":
            settings = await get_rules_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            text = settings["text"] or "Не установлен"
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    settings["text"][:50] + "..." if len(text) > 50 else text, status
                ),
                reply_markup=await edit_message_kb(chat_id, "rules"),
                parse_mode="HTML",
            )
            await state.clear()
            await state.set_state(ModStates.managing_chat)
            await state.update_data(chat_id=chat_id)
        case "deltext" | "delbutton":
            to_del = target.split("del")[1]

            match to_del:
                case "text":
                    await save_rules_settings(chat_id=chat_id, text="Правила")
                case "button":
                    await save_rules_settings(chat_id=chat_id, buttons=[])
            settings = await get_rules_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            text = settings["text"] or "Не установлен"
            await state.clear()
            await state.set_state(ModStates.managing_chat)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    settings["text"][:50] + "..." if len(text) > 50 else text, status
                ),
                reply_markup=await edit_message_kb(chat_id, "rules"),
                parse_mode="HTML",
            )
        case "preview":
            settings = await get_rules_settings(chat_id)
            status = "✅" if settings["enable"] else "❌"
            text = settings["text"] or "Не установлен"
            await callback.message.edit_text(
                text=settings["text"][:50] + "..." if len(text) > 50 else text,
                reply_markup=await format_keyboard(settings["buttons"]),
                parse_mode="HTML",
            )
            await callback.message.answer(
                text=TEXTS["settings"].format(
                    text[:50] + "..." if len(text) > 50 else text, status
                ),
                reply_markup=await edit_message_kb(chat_id, "rules"),
                parse_mode="HTML",
            )
