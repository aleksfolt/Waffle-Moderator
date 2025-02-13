from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from BaseModeration.BaseModerationHelpers import parse_seconds_time, punish_user
from config import redis_client
from database.antiflood import get_antiflood_settings, save_antiflood_settings
from keyboards.antifloodKeyboards import (
    antiflood_kb,
    back_to_antiflood,
    numbers_keyboard,
)
from utils.states import AntiFlood, ModStates

antiflood_router = Router()

TEXTS = {
    "main": (
        "🛡 Антифлуд — система защиты чата от спама и частых сообщений. "
        "Позволяет задать лимит сообщений за определённое время и автоматически "
        "применять меры: предупреждение, мут, кик, бан или удаление сообщений."
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
    "choose_messages": ("Выберите количество сообшений для срабатывания антифлуда:"),
    "choose_time": ("Выберите время в секундах на срабатывание антифлуда:"),
    "moderation_actions": {
        "ban": "бан.",
        "kick": "кик из чата.",
        "mute": "обеззвучивание.",
        "warn": "предупреждение.",
    },
    "status": ("\n\n{} {}"),
    "action_set": ("\n\n<b>✅ Установлено {}</b>"),
    "saved": ("✅ Успешно сохранено!"),
}


@antiflood_router.callback_query(F.data.startswith("antiflood:"))
async def anti_flood_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    await callback.message.edit_text(
        TEXTS["main"], reply_markup=await antiflood_kb(chat_id)
    )


@antiflood_router.callback_query(F.data.startswith("af:"))
async def antiflood_callback(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split(":")
    data = await state.get_data()
    chat_id = data.get("chat_id")
    action = data_parts[1]

    match action:
        case "msgs":
            await callback.message.edit_text(
                text=TEXTS["choose_messages"],
                reply_markup=await numbers_keyboard(chat_id, "messages"),
            )

        case "time":
            await callback.message.edit_text(
                text=TEXTS["choose_time"],
                reply_markup=await numbers_keyboard(chat_id, "time"),
            )

        case "switch":
            settings = await get_antiflood_settings(chat_id)
            enable = not settings["enable"]
            await save_antiflood_settings(chat_id, enable=enable)

            status = TEXTS["status"].format(
                "✅" if enable else "❌",
                "Антифлуд включён" if enable else "Антифлуд выключен",
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status, reply_markup=await antiflood_kb(chat_id)
            )

        case "action":
            action = data_parts[2]
            await save_antiflood_settings(chat_id, action=action)

            await callback.message.edit_text(
                text=TEXTS["main"]
                + TEXTS["action_set"].format(TEXTS["moderation_actions"][action]),
                reply_markup=await antiflood_kb(chat_id),
                parse_mode="HTML",
            )

        case "duration":
            await state.update_data(chat_id=chat_id)
            await callback.message.edit_text(
                text=TEXTS["time_input"], reply_markup=await back_to_antiflood(chat_id)
            )
            await state.set_state(AntiFlood.DURATION)

        case "delete_messages":
            settings = await get_antiflood_settings(chat_id)
            enable = not settings["delete_message"]
            await save_antiflood_settings(chat_id, delete_message=enable)

            status = TEXTS["status"].format(
                "✅" if enable else "❌",
                "Удалять сообщения" if enable else "Удалять сообщения",
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status, reply_markup=await antiflood_kb(chat_id)
            )

        case "journal":
            settings = await get_antiflood_settings(chat_id)
            enable = not settings["journal"]
            await save_antiflood_settings(chat_id, journal=enable)

            status = TEXTS["status"].format(
                "✅" if enable else "❌",
                "Журнал включен" if enable else "Журнал выключен",
            )
            await callback.message.edit_text(
                text=TEXTS["main"] + status, reply_markup=await antiflood_kb(chat_id)
            )

        case "back":
            await callback.message.edit_text(
                text=TEXTS["main"], reply_markup=await antiflood_kb(chat_id)
            )
            await state.clear()


async def handle_antiflood_callback(
    callback: CallbackQuery, target: str, state: FSMContext
):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    messages = callback.data.split(":")[3]

    match target:
        case "messages":
            await save_antiflood_settings(chat_id, messages=int(messages))
            await callback.message.edit_text(
                text=TEXTS["choose_messages"],
                reply_markup=await numbers_keyboard(chat_id, "messages"),
            )
        case "time":
            await save_antiflood_settings(chat_id, time=int(messages))
            await callback.message.edit_text(
                text=TEXTS["choose_time"],
                reply_markup=await numbers_keyboard(chat_id, "time"),
            )


@antiflood_router.message(AntiFlood.DURATION)
async def warn_duration(msg: Message, state: FSMContext):
    duration = str(msg.text)
    format_duration = await parse_seconds_time(duration)
    data = await state.get_data()
    chat_id = data.get("chat_id")

    if format_duration is None:
        await msg.answer(
            "⚠️ Неверный формат. Используйте: 30s, 5m, 2h, 1d, 1w или 1y",
            reply_markup=await back_to_antiflood(chat_id),
        )
        return

    await save_antiflood_settings(chat_id, duration_action=str(format_duration))
    await msg.answer(text=TEXTS["saved"], reply_markup=await back_to_antiflood(chat_id))
    await state.clear()


async def check_antiflood(msg: Message, chat_id: int, user_id: int) -> None:
    try:
        settings = await get_antiflood_settings(chat_id)
        if not settings["enable"]:
            return

        messages_limit = settings["messages"]
        time_limit = settings["time"]
        action = settings["action"]

        redis_key = f"antiflood:{chat_id}:{user_id}"
        punished_key = f"punished:{chat_id}:{user_id}"
        flood_messages_key = f"flood_msgs:{chat_id}:{user_id}"

        is_punished = await redis_client.exists(punished_key)
        if is_punished:
            return

        async with redis_client.pipeline() as pipe:
            pipe.incr(redis_key)
            pipe.expire(redis_key, time_limit)
            pipe.rpush(flood_messages_key, msg.message_id)
            pipe.expire(flood_messages_key, time_limit)
            result = await pipe.execute()

            current_count = result[0]

            if current_count > messages_limit:
                await redis_client.setex(punished_key, time_limit, "1")

                flooded_messages = await redis_client.lrange(flood_messages_key, 0, -1)
                for msg_id in flooded_messages:
                    try:
                        await msg.bot.delete_message(chat_id, int(msg_id))
                    except Exception:
                        pass

                if action:
                    await punish_user(
                        msg, action, settings["duration_action"], "флуд в чате."
                    )

                await redis_client.delete(redis_key)
                await redis_client.delete(flood_messages_key)
    except Exception:
        pass
