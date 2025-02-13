from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from BaseModeration.BaseModerationHelpers import parse_seconds_time
from database.antispam import (
    get_all_settings,
    get_forward_settings,
    get_quotes_settings,
    get_tlink_settings,
    save_all_settings,
    save_forward_settings,
    save_quotes_settings,
    save_tlink_settings,
)
from keyboards.antispamKeyboards import (
    all_kb,
    antispam_kb,
    back_action_kb,
    cancel_action_kb,
    forward_kb,
    quotes_kb,
    telegram_links_kb,
)
from utils.states import AntispamStates

antispam_router = Router()

TEXTS = {
    "main": (
        "📨 <b>Антиспам</b>\n\n"
        "В этом меню вы можете настроить автоматическое наказание для пользователей, "
        "которые отправляют спам в группу. Бот будет автоматически блокировать "
        "нежелательный контент на основе выбранных параметров. 🚫"
    ),
    "telegram_links": (
        "📘 <b>Telegram ссылки</b>\n\n"
        "В этом меню вы можете установить наказание для пользователей, отправляющих "
        "сообщения, содержащие ссылки Telegram.\n\n"
        "🎯 <b>Имя Пользователя Анти-Спам:</b>\n"
        "└ Этот параметр запускает антиспам при отправке имени пользователя, считающегося спамом.\n\n"
        "🤖 <b>Бот Анти-Спам:</b>\n"
        "└ Эта опция запускает антиспам при отправке ссылки на Бота."
    ),
    "filter_status": (
        "\n\n"
        "{} <b>Статус фильтра:</b>\n"
        "└ Фильтр Telegram ссылок {}\n"
        "└ Все сообщения проходят проверку"
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
    "settings": (
        "⚙️ Настройки сообщений\n\n"
        "📄 Текст: {} {}\n\n"
        "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": (
        "✏️ <b>Редактирование текста</b>\n\n"
        "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён)."
    ),
    "success_duration": "⏳ Время {} установлено на {}",
    "error_duration": (
        "⚠️ <b>Ошибка ввода</b>\n\n" "└ Введите корректное значение времени"
    ),
    "forward_settings": (
        "📨 <b>Настройки пересылки - {}</b>\n\n"
        "Выберите действие, которое будет применяться к сообщениям, "
        "пересылаемым из выбранного типа источника."
    ),
    "forward_exceptions": (
        "🌟 <b>Исключения для категории: {}</b>\n\n"
        "Текущие исключения:\n"
        "└ {}\n\n"
        "Чтобы добавить новые исключения, отправьте их через запятую.\n"
        "Если исключение уже существует, оно будет удалено.\n\n"
        "<b>Пример:</b>\n"
        "└ @channel1, @user1, t.me/channel2"
    ),
    "success_exceptions": "✅ <b>Изменения сохранены</b>\n\n{}",
    "quotes_settings": (
        "💬 <b>Настройки цитат - {}</b>\n\n"
        "Выберите действие, которое будет применяться к сообщениям "
        "с цитатами из выбранного типа источника."
    ),
    "quotes_exceptions": (
        "🌟 <b>Исключения для цитат: {}</b>\n\n"
        "Текущие исключения:\n"
        "└ {}\n\n"
        "Чтобы добавить новые исключения, отправьте их через запятую.\n"
        "Если исключение уже существует, оно будет удалено.\n\n"
        "<b>Пример:</b>\n"
        "└ @channel1, @user1, t.me/channel2"
    ),
    "general_settings": (
        "🔗 <b>Общий блок ссылок</b>\n\n"
        "В этом меню вы можете установить наказание для пользователей, отправляющих "
        "сообщения, содержащие любые ссылки."
    ),
    "all_exceptions": (
        "🌟 <b>Исключения для общего блока ссылок</b>\n\n"
        "Текущие исключения:\n"
        "└ {}\n\n"
        "Чтобы добавить новые исключения, отправьте их через запятую.\n"
        "Если исключение уже существует, оно будет удалено.\n\n"
        "<b>Пример:</b>\n"
        "└ site.com, example.org, t.me"
    ),
}


class AntispamManager:
    def __init__(self, chat_id: str):
        self.chat_id = chat_id

    async def get_settings(self, category: str = None, settings_type: str = "tlinks"):
        settings_map = {
            "tlinks": lambda: get_tlink_settings(self.chat_id),
            "forward": lambda: get_forward_settings(self.chat_id, category),
            "quotes": lambda: get_quotes_settings(self.chat_id, category),
            "all": lambda: get_all_settings(self.chat_id),
        }
        return await settings_map[settings_type]()

    async def save_settings(
        self, settings_data: dict, category: str = None, settings_type: str = "tlinks"
    ):
        settings_map = {
            "tlinks": lambda: save_tlink_settings(self.chat_id, **settings_data),
            "forward": lambda: save_forward_settings(
                self.chat_id, category, **settings_data
            ),
            "quotes": lambda: save_quotes_settings(
                self.chat_id, category, **settings_data
            ),
            "all": lambda: save_all_settings(self.chat_id, **settings_data),
        }
        await settings_map[settings_type]()

    async def handle_exceptions(
        self,
        new_exceptions: list,
        current_exceptions: list,
        settings_type: str = "tlinks",
    ) -> tuple:
        current_set = set(current_exceptions)
        new_set = set(new_exceptions)

        def is_valid_format(exc: str) -> bool:
            if settings_type == "all":
                valid = any(
                    [
                        exc.startswith("http://"),
                        exc.startswith("https://"),
                        exc.startswith("www."),
                        not exc.startswith(("@", "t.me/")) and "." in exc,
                    ]
                )
            else:
                valid = any(
                    [
                        exc.startswith("@"),
                        exc.startswith("t.me/"),
                        exc.startswith("https://t.me/"),
                    ]
                )
            return valid

        valid_new = {exc for exc in new_set if is_valid_format(exc)}
        added = valid_new - current_set
        removed = current_set & valid_new
        updated = (current_set - removed) | added
        return list(updated), list(added), list(removed)

    async def handle_duration(self, duration: str) -> tuple:
        duration_value = await parse_seconds_time(duration)
        if duration_value is None:
            return None, None
        settings = await self.get_settings()
        action_word = "обеззвучивания" if settings["action"] == "mute" else "блокировки"
        return str(duration_value), action_word

    async def get_status_text(
        self, settings_type: str = "tlinks", category: str = None
    ) -> str:
        settings = await self.get_settings(category, settings_type)
        return TEXTS["filter_status"].format(
            "✅" if settings["enable"] else "❌",
            "включен" if settings["enable"] else "выключен",
        )


@antispam_router.callback_query(F.data.startswith("antispam:"))
async def antispam_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.data.split(":")[1]
    await state.set_state(AntispamStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    await callback.message.edit_text(
        text=TEXTS["main"], reply_markup=await antispam_kb(chat_id), parse_mode="HTML"
    )


@antispam_router.callback_query(F.data.startswith("as:"))
async def as_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await callback.answer("Ошибка: ID чата не найден")
        return
    manager = AntispamManager(chat_id)
    action = callback.data.split(":")[1]

    async def get_action_config(action_type: str):
        configs = {
            "telegram_links": (
                TEXTS["telegram_links"] + await manager.get_status_text(),
                telegram_links_kb,
            ),
            "forwarding": (TEXTS["forward_settings"].format(""), forward_kb),
            "quotes": (TEXTS["quotes_settings"].format(""), quotes_kb),
            "all": (TEXTS["general_settings"], all_kb),
            "back": (TEXTS["main"], antispam_kb),
        }
        return configs.get(action_type)

    if action in ["telegram_links", "forwarding", "quotes", "all", "back"]:
        text, markup = await get_action_config(action)
        await callback.message.edit_text(
            text=text, reply_markup=await markup(chat_id), parse_mode="HTML"
        )
        if action == "back":
            await state.clear()


@antispam_router.callback_query(F.data.startswith("tlinks:"))
async def tlinks_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await callback.answer("Ошибка: ID чата не найден")
        return
    manager = AntispamManager(chat_id)
    parts = callback.data.split(":")
    action = parts[1]

    async def update_view():
        status = await manager.get_status_text()
        await callback.message.edit_text(
            text=TEXTS["telegram_links"] + status,
            reply_markup=await telegram_links_kb(chat_id),
            parse_mode="HTML",
        )

    if action == "back":
        current_state = await state.get_state()
        if current_state in [AntispamStates.TLINK_EXCEPTIONS, AntispamStates.DURATION]:
            await update_view()
            await state.set_state(None)
        else:
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await antispam_kb(chat_id),
                parse_mode="HTML",
            )
            await state.set_state(None)
    elif action == "cancel":
        await update_view()
        await state.set_state(None)
    elif action in ["switch", "username", "bot", "delete_messages"]:
        settings = await manager.get_settings()
        settings_updates = {
            "switch": {"enable": not settings["enable"]},
            "username": {"username": not settings["username"]},
            "bot": {"bot": not settings["bot"]},
            "delete_messages": {"delete_message": not settings["delete_message"]},
        }
        await manager.save_settings(settings_updates[action])
        await update_view()
    elif action == "action" and len(parts) > 2:
        await manager.save_settings({"action": parts[2]})
        await update_view()
    elif action == "duration":
        settings = await manager.get_settings()
        action_word = "обеззвучивания" if settings["action"] == "mute" else "блокировки"
        await callback.message.edit_text(
            text=TEXTS["time_input"].format(action_word),
            reply_markup=await cancel_action_kb("tlinks", None),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.DURATION)
    elif action == "exceptions":
        settings = await manager.get_settings()
        current_exceptions = (
            ", ".join(settings["exceptions"])
            if settings["exceptions"]
            else "Нет исключений"
        )
        await callback.message.edit_text(
            text=TEXTS["forward_exceptions"].format(
                "telegram_links", current_exceptions
            ),
            reply_markup=await cancel_action_kb("tlinks", None),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.TLINK_EXCEPTIONS)


@antispam_router.callback_query(F.data.startswith("forward:"))
async def forward_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await callback.answer("Ошибка: ID чата не найден")
        return
    manager = AntispamManager(chat_id)
    parts = callback.data.split(":")
    action = parts[1]
    category = parts[2] if len(parts) > 2 else None

    async def update_view():
        await callback.message.edit_text(
            text=TEXTS["forward_settings"].format(category or ""),
            reply_markup=await forward_kb(chat_id, category),
            parse_mode="HTML",
        )

    if action == "settings" and category:
        await state.update_data(selected_category=category)
        await update_view()
    elif action == "action" and len(parts) >= 4:
        category = parts[2]
        action_type = parts[3]
        settings = await manager.get_settings(category, "forward")
        if action_type == "off":
            await manager.save_settings(
                {"enable": not settings["enable"]}, category, "forward"
            )
        elif action_type in ["warn", "kick", "mute", "ban"]:
            await manager.save_settings({"action": action_type}, category, "forward")
        elif action_type == "delete_messages":
            await manager.save_settings(
                {"delete_message": not settings["delete_message"]}, category, "forward"
            )
        await update_view()
    elif action == "duration" and category:
        settings = await manager.get_settings(category, "forward")
        action_word = "обеззвучивания" if settings["action"] == "mute" else "блокировки"
        await state.update_data(forward_category=category, section="forward")
        await callback.message.edit_text(
            text=TEXTS["time_input"].format(action_word),
            reply_markup=await cancel_action_kb("forward", category),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.DURATION)
    elif action == "exceptions" and category and category != "none":
        settings = await manager.get_settings(category, "forward")
        current_exceptions = (
            ", ".join(settings["exceptions"])
            if settings["exceptions"]
            else "Нет исключений"
        )
        await callback.message.edit_text(
            text=TEXTS["forward_exceptions"].format(category, current_exceptions),
            reply_markup=await cancel_action_kb("forward", category),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.FORWARD_EXCEPTIONS)
        await state.update_data(forward_category=category)
    elif action in ["cancel", "back"]:
        if category:
            await update_view()
        else:
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await antispam_kb(chat_id),
                parse_mode="HTML",
            )
        await state.set_state(None)


@antispam_router.callback_query(F.data.startswith("quotes:"))
async def quotes_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await callback.answer("Ошибка: ID чата не найден")
        return
    manager = AntispamManager(chat_id)
    parts = callback.data.split(":")
    action = parts[1]
    category = parts[2] if len(parts) > 2 else None

    async def update_view():
        await callback.message.edit_text(
            text=TEXTS["quotes_settings"].format(category or ""),
            reply_markup=await quotes_kb(chat_id, category),
            parse_mode="HTML",
        )

    if action == "settings" and category:
        await state.update_data(selected_category=category)
        await update_view()
    elif action == "action" and len(parts) >= 4:
        category = parts[2]
        action_type = parts[3]
        settings = await manager.get_settings(category, "quotes")
        if action_type == "off":
            await manager.save_settings(
                {"enable": not settings["enable"]}, category, "quotes"
            )
        elif action_type in ["warn", "kick", "mute", "ban"]:
            await manager.save_settings({"action": action_type}, category, "quotes")
        elif action_type == "delete_messages":
            await manager.save_settings(
                {"delete_message": not settings["delete_message"]}, category, "quotes"
            )
        await update_view()
    elif action == "duration" and category:
        settings = await manager.get_settings(category, "quotes")
        action_word = "обеззвучивания" if settings["action"] == "mute" else "блокировки"
        await state.update_data(quotes_category=category)
        await callback.message.edit_text(
            text=TEXTS["time_input"].format(action_word),
            reply_markup=await cancel_action_kb("quotes", category),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.QUOTES_DURATION)
    elif action == "exceptions" and category and category != "none":
        settings = await manager.get_settings(category, "quotes")
        current_exceptions = (
            ", ".join(settings["exceptions"])
            if settings["exceptions"]
            else "Нет исключений"
        )
        await callback.message.edit_text(
            text=TEXTS["quotes_exceptions"].format(category, current_exceptions),
            reply_markup=await cancel_action_kb("quotes", category),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.QUOTES_EXCEPTIONS)
        await state.update_data(quotes_category=category)
    elif action in ["cancel", "back"]:
        if category:
            await update_view()
        else:
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await antispam_kb(chat_id),
                parse_mode="HTML",
            )
        await state.set_state(None)


@antispam_router.callback_query(F.data.startswith("all:"))
async def all_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await callback.answer("Ошибка: ID чата не найден")
        return
    manager = AntispamManager(chat_id)
    parts = callback.data.split(":")
    action = parts[1]

    async def update_view():
        await callback.message.edit_text(
            text=TEXTS["general_settings"],
            reply_markup=await all_kb(chat_id),
            parse_mode="HTML",
        )

    if action == "switch":
        settings = await manager.get_settings(settings_type="all")
        await manager.save_settings(
            {"enable": not settings["enable"]}, settings_type="all"
        )
        await update_view()
    elif action == "action" and len(parts) > 2:
        await manager.save_settings({"action": parts[2]}, settings_type="all")
        await update_view()
    elif action == "delete_messages":
        settings = await manager.get_settings(settings_type="all")
        await manager.save_settings(
            {"delete_message": not settings["delete_message"]}, settings_type="all"
        )
        await update_view()
    elif action == "duration":
        settings = await manager.get_settings(settings_type="all")
        action_word = "обеззвучивания" if settings["action"] == "mute" else "блокировки"
        await state.update_data(section="all")
        await callback.message.edit_text(
            text=TEXTS["time_input"].format(action_word),
            reply_markup=await cancel_action_kb("all", None),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.DURATION)
    elif action == "exceptions":
        settings = await manager.get_settings(settings_type="all")
        current_exceptions = (
            ", ".join(settings["exceptions"])
            if settings["exceptions"]
            else "Нет исключений"
        )
        await callback.message.edit_text(
            text=TEXTS["all_exceptions"].format(current_exceptions),
            reply_markup=await cancel_action_kb("all", None),
            parse_mode="HTML",
        )
        await state.set_state(AntispamStates.ALL_EXCEPTIONS)
    elif action in ["cancel", "back"]:
        current_state = await state.get_state()
        if current_state in [AntispamStates.DURATION, AntispamStates.ALL_EXCEPTIONS]:
            await update_view()
        else:
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await antispam_kb(chat_id),
                parse_mode="HTML",
            )
        await state.set_state(None)


@antispam_router.message(AntispamStates.DURATION)
async def handle_duration_message(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    section = data.get("section", "tlinks")
    category = data.get("forward_category")

    if not chat_id:
        await message.answer("Ошибка: Необходимые данные не найдены")
        return

    manager = AntispamManager(chat_id)
    if section == "all":
        settings = await manager.get_settings(settings_type="all")
        action_word = "обеззвучивания" if settings["action"] == "mute" else "блокировки"
    else:
        duration_value, action_word = await manager.handle_duration(
            message.text.strip()
        )

    duration_value = await parse_seconds_time(message.text.strip())
    if not duration_value:
        await message.answer(
            "⚠️ Неверный формат. Используйте: 30s, 5m, 2h, 1d, 1w или 1y",
            reply_markup=await back_action_kb(section, category),
            parse_mode="HTML",
        )
        return

    if section == "all":
        settings_data = {"duration_actions": str(duration_value)}
    elif section == "forward":
        settings_data = {"duration_actions": str(duration_value)}
    else:
        settings_data = {"duration_action": str(duration_value)}

    await manager.save_settings(settings_data, category, section)
    await message.answer(
        text=TEXTS["success_duration"].format(action_word, message.text.strip()),
        reply_markup=await back_action_kb(section, category),
        parse_mode="HTML",
    )


@antispam_router.message(AntispamStates.TLINK_EXCEPTIONS)
@antispam_router.message(AntispamStates.FORWARD_EXCEPTIONS)
@antispam_router.message(AntispamStates.QUOTES_EXCEPTIONS)
@antispam_router.message(AntispamStates.ALL_EXCEPTIONS)
async def handle_exceptions_message(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    current_state = await state.get_state()
    settings_type_map = {
        "AntispamStates:TLINK_EXCEPTIONS": "tlinks",
        "AntispamStates:FORWARD_EXCEPTIONS": "forward",
        "AntispamStates:QUOTES_EXCEPTIONS": "quotes",
        "AntispamStates:ALL_EXCEPTIONS": "all",
    }
    settings_type = settings_type_map.get(current_state)
    category = (
        data.get(f"{settings_type}_category")
        if settings_type not in ["tlinks", "all"]
        else None
    )
    if not chat_id or (not category and settings_type not in ["tlinks", "all"]):
        await message.answer("Ошибка: Необходимые данные не найдены")
        return
    manager = AntispamManager(chat_id)
    new_exceptions = [exc.strip() for exc in message.text.split(",") if exc.strip()]
    if not new_exceptions:
        error_msg = (
            "⚠️ Ошибка: Пожалуйста, укажите хотя бы одно исключение в правильном формате"
            + (
                " (@username или t.me/...)"
                if settings_type != "all"
                else " (например: example.com)"
            )
        )
        await message.answer(
            text=error_msg,
            reply_markup=await back_action_kb(settings_type, category),
            parse_mode="HTML",
        )
        return
    try:
        settings = await manager.get_settings(category, settings_type)
        current_exceptions = settings.get("exceptions", [])
        updated_exceptions, added, removed = await manager.handle_exceptions(
            new_exceptions, current_exceptions, settings_type
        )
        if not added and not removed:
            error_msg = (
                "⚠️ Ни одно из указанных исключений не соответствует правильному формату"
                + (
                    " (@username или t.me/...)"
                    if settings_type != "all"
                    else " (например: example.com)"
                )
            )
            await message.answer(
                text=error_msg,
                reply_markup=await back_action_kb(settings_type, category),
                parse_mode="HTML",
            )
            return
        await manager.save_settings(
            {"exceptions": updated_exceptions}, category, settings_type
        )
        result_msg = []
        if added:
            result_msg.append(f"✅ Добавлены: {', '.join(added)}")
        if removed:
            result_msg.append(f"❌ Удалены: {', '.join(removed)}")
        keyboard = await back_action_kb(settings_type, category)
        await message.answer(
            text=f"Изменения сохранены:\n{chr(10).join(result_msg)}",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(
            text=f"⚠️ Произошла ошибка при обработке исключений: {str(e)}",
            reply_markup=await back_action_kb(settings_type, category),
            parse_mode="HTML",
        )
