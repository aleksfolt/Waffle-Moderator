from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from BaseModeration.BaseModerationHelpers import format_text
from database.moderation import get_moderation_settings
from database.utils import get_user_by_id_or_username
from middlefilters.HasPromoteRights import HasPromoteRights

kick_router = Router()


@kick_router.message(Command("kick", ignore_case=True), HasPromoteRights())
async def kick(msg: Message):
    try:
        chat_id = msg.chat.id
        settings = await get_moderation_settings(chat_id)
        kick_settings = settings.get("kick")

        if not kick_settings["enabled"]:
            await msg.reply("Команда /kick отключена.")
            return

        user_id = None
        reason = "Без причины"
        first_name = "пользователь"

        if msg.reply_to_message:
            user_id = msg.reply_to_message.from_user.id
            first_name = msg.reply_to_message.from_user.first_name
            parts = msg.text.split(maxsplit=1)
            if len(parts) > 1:
                reason = parts[1]
        else:
            parts = msg.text.split(maxsplit=2)
            if len(parts) < 2:
                await msg.reply(
                    "Пожалуйста, укажите пользователя для кика или используйте команду как реплай."
                )
                return

            target = parts[1]
            reason = parts[2] if len(parts) > 2 else "Без причины"

            if target.isdigit():
                user_id = int(target)
                db_user = await get_user_by_id_or_username(user_id=user_id)
                if db_user:
                    first_name = db_user.first_name
            elif target.startswith("@"):
                db_user = await get_user_by_id_or_username(username=target.lstrip("@"))
                if db_user:
                    user_id = db_user.user_id
                    first_name = db_user.first_name

        if not user_id:
            await msg.reply(
                "Не удалось определить пользователя. Укажите корректный user_id или username."
            )
            return

        if kick_settings["delete_message"] and msg.reply_to_message:
            await msg.reply_to_message.delete()

        await msg.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await msg.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

        response = await format_text(
            template=kick_settings["text"],
            message=msg,
            target_user_id=user_id,
            target_first_name=first_name,
            reason=reason,
        )

        await msg.reply(response, parse_mode="HTML")

    except Exception as e:
        await msg.reply(f"Произошла ошибка: {e}")
