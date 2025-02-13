import html
import re
import time
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import redis_client
from database.meeting import (
    create_meeting_history,
    get_meeting_settings,
    get_user_meeting_history,
    update_meeting_message,
)
from database.warns import add_warn, get_warn_settings, get_warns_count, reset_warns
from keyboards.moderationKeyboards import get_moderation_action_kb


TEXTS = {
    "punishments": {
        "mute": "🔇 Мут {}.",
        "ban": "🚫 Бан {}",
        "kick": "👢 Кик из чата.",
        "error": "❌ Ошибка: {}",
    },
    "default_text": "%%__mention__%% [%%__user_id__%%] предупрежден (%%__warn_count__%%/%%__max_warns__%%).",
    "warnings": {
        "max_reached": "🚨 {} Достиг максимального количества предупреждений.\n{}!"
    },
}


async def parse_command(message: Message):

    parts = message.text.split(maxsplit=2)

    username_or_id = None
    duration = None
    reason = None

    if len(parts) > 1:
        username_or_id = (
            parts[1] if (parts[1].startswith("@") or parts[1].isdigit()) else None
        )

    if message.reply_to_message:
        reply_text = " ".join(parts[1:])
        match = re.match(r"^(\d+[smhdwy])", reply_text)
        if match:
            duration = match.group(0)
            reason = reply_text[len(duration) :].strip() or "empty"
        else:
            reason = reply_text.strip() or "empty"
    else:
        if len(parts) > 2:
            match = re.match(r"^(\d+)([smhdwy])$", parts[2].split()[0])
            if match:
                duration = match.group(0)
                reason = " ".join(parts[2].split()[1:]) or "empty"
            else:
                reason = parts[2]

    if not username_or_id:
        if message.reply_to_message:
            username_or_id = message.reply_to_message.from_user.id
        else:
            return None, (
                "Ошибка: Укажите username или ID, если команда не является "
                "ответом на сообщение."
            )

    return {
        "username_or_id": username_or_id,
        "duration": duration or "♾️",
        "reason": reason or "Не указана.",
    }, None


async def parse_time(time: Optional[str]):
    if not time:
        return None

    re_match = re.match(r"(\d+)([a-z])", time.lower().strip())
    now_datetime = datetime.now()

    if re_match:
        value = int(re_match.group(1))
        unit = re_match.group(2)

        if unit == "s":
            time_delta = timedelta(seconds=value)
        elif unit == "m":
            time_delta = timedelta(minutes=value)
        elif unit == "h":
            time_delta = timedelta(hours=value)
        elif unit == "d":
            time_delta = timedelta(days=value)
        elif unit == "w":
            time_delta = timedelta(weeks=value)
        elif unit == "y":
            time_delta = timedelta(days=365 * value)
        else:
            return None
    else:
        return None
    print(f"\033[91m{time_delta}\033[0m")
    new_datetime = now_datetime + time_delta
    return new_datetime


async def parse_seconds_time(time: str):
    if not time:
        return None

    if time.lower().strip() == "forever":
        return "forever"

    re_match = re.match(r"(\d+)([a-z])", time.lower().strip())

    if re_match:
        value = int(re_match.group(1))
        unit = re_match.group(2)

        if unit == "s":
            seconds = value
        elif unit == "m":
            seconds = value * 60
        elif unit == "h":
            seconds = value * 3600
        elif unit == "d":
            seconds = value * 86400
        elif unit == "w":
            seconds = value * 604800
        elif unit == "y":
            seconds = value * 31536000
        else:
            return None
    else:
        return None

    return seconds


async def format_duration(duration: str) -> str:
    forms = {
        "s": ("секунда", "секунды", "секунд"),
        "m": ("минута", "минуты", "минут"),
        "h": ("час", "часа", "часов"),
        "d": ("день", "дня", "дней"),
        "w": ("неделя", "недели", "недель"),
        "y": ("год", "года", "лет"),
    }

    match = re.match(r"(\d+)([smhdwy])", duration)
    if not match:
        return duration

    value = int(match.group(1))
    unit = match.group(2)

    if unit in forms:
        word_forms = forms[unit]
        if value % 10 == 1 and value % 100 != 11:
            word = word_forms[0]
        elif 2 <= value % 10 <= 4 and not (12 <= value % 100 <= 14):
            word = word_forms[1]
        else:
            word = word_forms[2]
        return f"{value} {word}"
    return duration


async def has_promote_rights(message) -> bool:
    admins = await message.bot.get_chat_administrators(chat_id=message.chat.id)

    for admin in admins:
        if admin.user.id == message.from_user.id:
            if (
                isinstance(admin, types.ChatMemberAdministrator)
                and admin.can_restrict_members
            ):
                return True
            if isinstance(admin, types.ChatMemberOwner):
                return True

    return False


async def format_text(
    template: str,
    message: Message,
    target_user_id: int,
    target_first_name: str,
    duration: Optional[str] = "",
    reason: Optional[str] = "Без причины",
    warns_count: Optional[int] = 0,
    max_warns: Optional[int] = 0,
) -> str:
    chat_title = html.escape(message.chat.title or "")
    chat_id = message.chat.id
    message_link = (
        f"https://t.me/c/{str(chat_id).replace('-100', '')}/{message.message_id}"
    )

    mention = (
        f"<a href='tg://user?id={target_user_id}'>{html.escape(target_first_name)}</a>"
    )

    return (
        template.replace("%%__mention__%%", mention)
        .replace("%%__duration__%%", html.escape(duration))
        .replace("%%__reason__%%", html.escape(reason))
        .replace("%%__chat_title__%%", chat_title)
        .replace("%%__message_link__%%", message_link)
        .replace("%%__full_name__%%", html.escape(target_first_name))
        .replace("%%__user_id__%%", str(target_user_id))
        .replace("%%__warn_count__%%", str(warns_count))
        .replace("%%__max_warns__%%", str(max_warns))
    )


async def format_buttons(input_text: str) -> dict | bool:
    try:
        if not isinstance(input_text, str) or not input_text.strip():
            return False

        inline_keyboard = []
        for line in input_text.strip().split("\n"):
            if not line.strip():
                continue

            row = []
            for button in line.split(" && "):
                parts = button.strip().split(" - ", 1)
                if len(parts) != 2:
                    return False

                text, url = map(str.strip, parts)
                if not text or not url:
                    return False

                if not url.startswith(("http://", "https://")):
                    url = "http://" + url

                row.append({"text": text, "url": url})

            if row:
                inline_keyboard.append(row)

        return {"inline_keyboard": inline_keyboard} if inline_keyboard else False

    except Exception:
        return False


async def format_keyboard(json_data):
    builder = InlineKeyboardBuilder()

    if isinstance(json_data, dict) and "inline_keyboard" in json_data:
        keyboard_rows = json_data["inline_keyboard"]

        if isinstance(keyboard_rows, list):
            for row in keyboard_rows:
                buttons = [
                    InlineKeyboardButton(text=button["text"], url=button["url"])
                    for button in row
                ]
                builder.row(*buttons)

    return builder.as_markup()


async def apply_punishment(bot, chat_id: int, user_id: int, action: str, duration):
    try:
        if duration == "forever":
            until_date = None
            duration_str = "навсегда"
        elif isinstance(duration, str) and duration.isdigit():
            seconds = int(duration)
            until_date = datetime.now() + timedelta(seconds=seconds)
            duration_str = until_date.strftime("%Y-%m-%d")
        else:
            return TEXTS["errors"]["invalid_time"]

        if action == "mute":
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_photos=False,
                    can_send_videos=False,
                    can_send_voice_notes=False,
                    can_send_video_notes=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                ),
                use_independent_chat_permissions=False,
                until_date=int(until_date.timestamp()) if until_date else None,
            )
            return TEXTS["punishments"]["mute"].format(duration_str)

        elif action == "ban":
            await bot.ban_chat_member(
                chat_id,
                user_id,
                until_date=int(until_date.timestamp()) if until_date else None,
            )
            return TEXTS["punishments"]["ban"].format(duration_str)

        else:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
            return TEXTS["punishments"]["kick"]

    except Exception as e:
        return TEXTS["punishments"]["error"].format(str(e))


async def punish_user(msg: Message, action: str, duration: str, violation: str):
    user_id = msg.from_user.id
    duration_seconds = int(duration) if action in ["mute", "ban"] else 0

    user_name = html.escape(msg.from_user.first_name)
    mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"

    until_date = (
        int(time.time()) + duration_seconds if action in ["mute", "ban"] else None
    )
    formatted_date = (
        time.strftime("%d %B %Y в %H:%M", time.localtime(until_date))
        if until_date
        else ""
    )

    messages = {
        "warn": f"""
⚠️ <b>Предупреждение</b>
└ Участник: {mention}
└ Причина: нарушение правил чата ({violation})
""",
        "mute": f"""
🔇 <b>Мут в чате</b>
└ Участник: {mention}
└ Причина: нарушение правил чата ({violation})
└ Срок: до {formatted_date}
""",
        "kick": f"""
🚷 <b>Исключение из чата</b>
└ Участник: {mention}
└ Причина: нарушение правил чата ({violation})
└ Тип: единоразовое исключение
""",
        "ban": f"""
⛔ <b>Блокировка в чате</b>
└ Участник: {mention}
└ Причина: нарушение правил чата ({violation})
└ Срок: до {formatted_date}
""",
    }

    if action == "warn":
        settings = await get_warn_settings(msg.chat.id)
        current_warns = await get_warns_count(msg.chat.id, user_id)

        await add_warn(msg.chat.id, user_id)
        new_warns_count = current_warns + 1

        if new_warns_count >= settings["warns_count"]:
            punishment = await apply_punishment(
                bot=msg.bot,
                chat_id=msg.chat.id,
                user_id=user_id,
                action=settings["action"],
                duration=settings["duration_action"],
            )
            mention = f"<a href='tg://user?id={user_id}'>{html.escape(msg.from_user.first_name)}</a>"

            try:
                await msg.answer(
                    TEXTS["warnings"]["max_reached"].format(mention, punishment),
                    parse_mode="HTML",
                    reply_markup=await get_moderation_action_kb(
                        user_id, settings["action"]
                    ),
                )
            except Exception as e:
                print(f"Error sending max warns message: {str(e)}")

            await reset_warns(msg.chat.id, user_id)
            return

        try:
            await msg.answer(
                messages[action],
                parse_mode="HTML",
                reply_markup=await get_moderation_action_kb(user_id, action),
            )
        except Exception as e:
            print(f"Error sending regular warn message: {str(e)}")
        return

    elif action == "mute":
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_voice_notes=False,
            can_send_video_notes=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        try:
            await msg.chat.restrict(
                user_id, permissions=permissions, until_date=until_date
            )
        except Exception as e:
            print(f"Error muting user: {str(e)}")

    elif action == "kick":
        try:
            await msg.chat.ban(user_id)
            await msg.chat.unban(user_id)
        except Exception as e:
            print(f"Error kicking user: {str(e)}")

    elif action == "ban":
        try:
            await msg.chat.ban(user_id, until_date=until_date)
        except Exception as e:
            print(f"Error banning user: {str(e)}")

    try:
        await msg.answer(
            messages[action],
            parse_mode="HTML",
            reply_markup=await get_moderation_action_kb(user_id, action),
        )
    except Exception as e:
        print(f"Error sending punishment message: {str(e)}")

    punished_key = f"punished:{msg.chat.id}:{user_id}"
    try:
        await redis_client.delete(punished_key)
    except Exception as e:
        print(f"Error deleting Redis key: {str(e)}")


async def is_user_restricted(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.is_restricted()
    except Exception:
        return False


async def restrict_user(bot: Bot, chat_id: int, user_id: int):
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
        )
        return True
    except Exception as e:
        print(f"Error restricting user: {e}")
        return False


async def unrestrict_user(bot: Bot, chat_id: int, user_id: int):
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        return True
    except Exception as e:
        print(f"Error unrestricting user: {e}")
        return False


async def get_captcha_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Я не робот 🤖", callback_data=f"cunmute:{user_id}"
                )
            ]
        ]
    )


async def handle_welcome_message(message: Message):
    settings = await get_meeting_settings(message.chat.id)
    if not settings["enable"]:
        return

    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue

        try:
            history = await get_user_meeting_history(message.chat.id, new_member.id)

            if not settings["always_send"] and history is not None:
                continue

            if settings["delete_last_message"] and history and history.message_id:
                try:
                    await message.bot.delete_message(
                        chat_id=message.chat.id, message_id=history.message_id
                    )
                except Exception as e:
                    print(f"Error deleting previous welcome message: {e}")

            formatted_text = await format_text(
                template=settings["text"],
                message=message,
                target_user_id=new_member.id,
                target_first_name=new_member.first_name,
            )

            kwargs = {
                "text": formatted_text,
                "reply_markup": await format_keyboard(settings["buttons"]),
                "parse_mode": "HTML",
            }

            welcome_message = None

            if settings["media_link"]:
                try:
                    kwargs["link_preview_options"] = LinkPreviewOptions(
                        url=settings["media_link"], show_above_text=True
                    )
                    welcome_message = await message.answer(**kwargs)
                except (TelegramBadRequest, ValueError) as e:
                    print(f"Error sending message with media link: {e}")
                    kwargs.pop("link_preview_options", None)

            if not welcome_message:
                welcome_message = await message.answer(**kwargs)

            if history:
                await update_meeting_message(
                    message.chat.id, new_member.id, welcome_message.message_id
                )
            else:
                await create_meeting_history(
                    message.chat.id, new_member.id, welcome_message.message_id
                )
        except Exception as e:
            print(f"Error handling welcome message: {e}")
