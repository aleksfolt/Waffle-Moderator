import os

import opennsfw2 as n2
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from BaseModeration.BaseModerationHelpers import (
    format_keyboard,
    parse_seconds_time,
    punish_user,
)
from database.nsfwFilter import get_nsfwFilter_settings, save_nsfwFilter_settings
from keyboards.moderationKeyboards import edit_message_kb, edit_message_text_kb
from keyboards.nsfwKeyboards import nsfw_back, nsfw_kb
from utils.states import EditForm, Nsfw, ModStates
from utils.texts import BUTTONS_MESSAGE

nsfw_router = Router()

TEXTS = {
    "main": (
        "🔞 <b>Фильтр порно</b>\n\n"
        "В этом меню вы можете настроить автоматическое наказание для пользователей, "
        "которые отправляют порнографию в группу. Бот использует <b>OpenNSFW 2</b> для "
        "анализа изображений и автоматически блокирует нежелательный контент. 🚨📵"
    ),
    "filter_status": (
        "\n\n"
        "{} <b>Статус фильтра:</b>\n"
        "└ Фильтр NSFW {}\n"
        "└ Все изображения проходят проверку"
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
    "journal_status": (
        "\n\n" "{} <b>Статус журнала:</b>\n" "└ Логирование {}\n" "└ {}"
    ),
    "percentage_input": (
        "📊 <b>Настройка порога обнаружения NSFW</b>\n\n"
        "└ Текущее значение: {}%\n"
        "└ При превышении этого значения контент считается NSFW\n"
        "└ Допустимый диапазон: 0-100%\n"
        "└ Введите процент уверенности нейросети:"
    ),
    "error": (
        "⚠️ <b>Ошибка ввода</b>\n\n"
        "└ Допустимые значения: 0-100%\n"
        "└ Введите корректное число"
    ),
    "success": (
        "✅ <b>Настройки обновлены</b>\n\n"
        "└ Новый порог обнаружения NSFW: {}%\n"
        "└ Если нейросеть будет уверена больше чем на {}%, контент будет считаться NSFW\n"
        "└ Изменения вступили в силу"
    ),
    "settings": (
        "📄 Текст: {} {}\n\n" "👉🏻 Используйте команды, чтобы изменить настройки."
    ),
    "edit_text": (
        "👉🏻 Отправьте сообщение, которое хотите установить (HTML разрешён)."
    ),
}


@nsfw_router.callback_query(F.data.startswith("fnsfw:"))
async def fnsfw_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.data.split(":")[1]
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    await callback.message.edit_text(
        text=TEXTS["main"], reply_markup=await nsfw_kb(chat_id), parse_mode="HTML"
    )


@nsfw_router.callback_query(F.data.startswith("nsfw:"))
async def nsfw_callback(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split(":")
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))
    action = data_parts[1]

    match action:
        case "switch":
            settings = await get_nsfwFilter_settings(chat_id)
            enable = not settings["enable"]
            await save_nsfwFilter_settings(chat_id, enable=enable)

            status = TEXTS["filter_status"].format(
                "✅" if enable else "❌", "включен" if enable else "выключен"
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status,
                reply_markup=await nsfw_kb(chat_id),
                parse_mode="HTML",
            )

        case "journal":
            settings = await get_nsfwFilter_settings(chat_id)
            journal = not settings["journal"]
            await save_nsfwFilter_settings(chat_id, journal=journal)

            status = TEXTS["journal_status"].format(
                "📋" if journal else "❌",
                "включено" if journal else "выключено",
                "Все действия фиксируются" if journal else "Действия не записываются",
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status,
                reply_markup=await nsfw_kb(chat_id),
                parse_mode="HTML",
            )

        case "percentage":
            settings = await get_nsfwFilter_settings(chat_id)
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["percentage_input"].format(settings["percent"]),
                parse_mode="HTML",
                reply_markup=await nsfw_back(chat_id),
            )
            await state.set_state(Nsfw.PERCENTAGE)

        case "action":
            action = data_parts[2]
            await save_nsfwFilter_settings(chat_id, action=action)
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await nsfw_kb(chat_id),
                parse_mode="HTML",
            )

        case "duration":
            await callback.message.edit_text(
                text=TEXTS["time_input"],
                parse_mode="HTML",
                reply_markup=await nsfw_back(chat_id),
            )
            await state.update_data(chat_id=chat_id)
            await state.set_state(Nsfw.DURATION)

        case "settings":
            settings = await get_nsfwFilter_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "nsfw"),
                parse_mode="HTML",
            )

        case "back":
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await nsfw_kb(chat_id),
                parse_mode="HTML",
            )
            await state.clear()


async def handle_nsfw_callback(callback: CallbackQuery, target: str, state: FSMContext):
    chat_id = int(callback.data.split(":")[-1])

    match target:
        case "text":
            await callback.message.edit_text(
                text=TEXTS["edit_text"],
                reply_markup=await edit_message_text_kb(
                    chat_id, "nsfw", to_delete="text"
                ),
                parse_mode="HTML",
            )
            await state.set_state(EditForm.TEXT)

        case "buttons":
            await callback.message.edit_text(
                text=BUTTONS_MESSAGE,
                reply_markup=await edit_message_text_kb(
                    chat_id, "nsfw", to_delete="buttons"
                ),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            await state.set_state(EditForm.BUTTONS)

        case "preview":
            settings = await get_nsfwFilter_settings(chat_id)
            await callback.message.edit_text(
                text=settings["text"],
                reply_markup=await format_keyboard(settings["buttons"]),
                parse_mode="HTML",
            )
            await callback.message.answer(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "nsfw"),
                parse_mode="HTML",
            )

        case target if target.startswith("del"):
            to_del = target.split("del")[1]
            match to_del:
                case "text":
                    await save_nsfwFilter_settings(
                        chat_id, text="Обнаружен небезопасный контент!"
                    )
                case _:
                    await save_nsfwFilter_settings(chat_id, buttons=[])

            settings = await get_nsfwFilter_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "nsfw"),
                parse_mode="HTML",
            )

        case "back":
            await callback.message.edit_text(
                text=TEXTS["main"],
                reply_markup=await nsfw_kb(chat_id),
                parse_mode="HTML",
            )

        case "back_to_edit":
            settings = await get_nsfwFilter_settings(chat_id)
            await callback.message.edit_text(
                text=TEXTS["settings"].format(
                    "✅" if settings["text"] else "❌", settings["text"]
                ),
                reply_markup=await edit_message_kb(chat_id, "nsfw"),
                parse_mode="HTML",
            )
            await state.clear()


@nsfw_router.message(Nsfw.PERCENTAGE)
async def nsfw_percentage(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")

    try:
        percentage = message.text.strip()
        percentage_value = int(percentage)

        if not (0 <= percentage_value <= 100):
            raise ValueError

    except (ValueError, TypeError):
        await message.answer(text=TEXTS["error"], parse_mode="HTML")
        return

    await save_nsfwFilter_settings(chat_id, percent=percentage_value)
    await message.answer(
        text=TEXTS["success"].format(percentage_value, percentage_value),
        parse_mode="HTML",
        reply_markup=await nsfw_back(chat_id),
    )
    await state.clear()


@nsfw_router.message(Nsfw.DURATION)
async def nsfw_duration(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    try:
        duration = message.text.strip()
        duration_value = str(await parse_seconds_time(duration))
        if duration_value is None:
            await message.answer(
                "⚠️ Неверный формат. Используйте: 30s, 5m, 2h, 1d, 1w или 1y",
                reply_markup=await nsfw_back(chat_id),
            )
            return
        await save_nsfwFilter_settings(chat_id, duration_action=duration_value)
        await message.answer(
            text=f"⏳ Время наказания установлено на {duration}.",
            parse_mode="HTML",
            reply_markup=await nsfw_back(chat_id),
        )
        await state.clear()
    except (ValueError, TypeError):
        await message.answer(
            text="⚠️ Ошибка ввода\n\nВведите корректное число", parse_mode="HTML"
        )
        return


async def check_nsfw_photo(msg: Message, chat_id: int) -> None:
    try:
        nsfw_settings = await get_nsfwFilter_settings(chat_id)
        if not nsfw_settings["enable"]:
            return

        file_id = msg.photo[-1].file_id
        file_path = f"/tmp/{file_id}.jpg"

        await msg.bot.download(file_id, file_path)

        try:
            nsfw_score = n2.predict_image(file_path)
            print(nsfw_score)

            if nsfw_score * 100 >= nsfw_settings["percent"]:
                if nsfw_settings["delete_message"]:
                    await msg.delete()
                await punish_user(
                    msg,
                    nsfw_settings["action"],
                    nsfw_settings["duration_action"],
                    nsfw_settings["text"],
                )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception:
        pass
