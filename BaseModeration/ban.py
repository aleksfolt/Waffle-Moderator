from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from BaseModeration.BaseModerationHelpers import format_text, parse_command, parse_time
from database.moderation import get_moderation_settings
from database.utils import get_user_by_id_or_username
from keyboards.moderationKeyboards import get_moderation_action_kb
from middlefilters.HasPromoteRights import HasPromoteRights

ban_router = Router()


@ban_router.message(Command("ban", ignore_case=True), HasPromoteRights())
async def ban(msg: Message):
    try:
        chat_id = msg.chat.id
        settings = await get_moderation_settings(chat_id)
        ban_settings = settings.get("ban")

        if not ban_settings["enabled"]:
            return

        result, error = await parse_command(msg)
        if error:
            await msg.reply(error)
            return

        until_date = None
        if result["duration"] != "empty":
            until_date = await parse_time(result["duration"])

        user_id = result["username_or_id"]
        first_name = "пользователь"

        if isinstance(user_id, str):
            if user_id.startswith("@"):
                db_user = await get_user_by_id_or_username(username=user_id.lstrip("@"))
            elif user_id.isdigit():
                db_user = await get_user_by_id_or_username(user_id=int(user_id))
            else:
                db_user = None
        else:
            db_user = await get_user_by_id_or_username(user_id=user_id)

        if db_user:
            user_id = db_user.user_id
            first_name = db_user.first_name

        if not user_id:
            await msg.reply(
                "Не удалось определить пользователя. Укажите корректный user_id или username."
            )
            return

        if ban_settings["delete_message"] and msg.reply_to_message:
            await msg.reply_to_message.delete()

        text = await format_text(
            template=ban_settings["text"],
            message=msg,
            target_user_id=user_id,
            target_first_name=first_name,
            duration=result["duration"],
            reason=result["reason"],
        )

        await msg.bot.ban_chat_member(
            chat_id=chat_id, user_id=user_id, until_date=until_date
        )

        await msg.reply(
            text,
            parse_mode="HTML",
            reply_markup=await get_moderation_action_kb(user_id, "ban"),
        )
    except Exception as e:
        await msg.reply(f"An error occurred: {e}")


@ban_router.message(Command("unban", ignore_case=True), HasPromoteRights())
async def unban_handler(msg: Message):
    try:
        chat_id = msg.chat.id
        settings = await get_moderation_settings(chat_id)
        ban_settings = settings.get("ban")

        if not ban_settings["enabled"]:
            return

        user_id = None
        first_name = "пользователь"

        if msg.reply_to_message:
            user_id = msg.reply_to_message.from_user.id
            first_name = f"<a href='tg://user?id={user_id}'>{msg.reply_to_message.from_user.first_name}</a>"
        else:
            parts = msg.text.split()
            if len(parts) < 2:
                await msg.reply("Пожалуйста, укажите пользователя для разбана.")
                return
            target = parts[1]

            if target.isdigit():
                user_id = int(target)
                db_user = await get_user_by_id_or_username(user_id=user_id)
                if db_user:
                    first_name = (
                        f"<a href='tg://user?id={user_id}'>{db_user.first_name}</a>"
                    )
            elif target.startswith("@"):
                db_user = await get_user_by_id_or_username(username=target.lstrip("@"))
                if db_user:
                    user_id = db_user.user_id
                    first_name = (
                        f"<a href='tg://user?id={user_id}'>{db_user.first_name}</a>"
                    )

        if not user_id:
            await msg.reply(
                "Не удалось определить пользователя. Укажите корректный user_id или username."
            )
            return

        await msg.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

        text = f"✅ Пользователь {first_name} был успешно разбанен."
        await msg.reply(text, parse_mode="HTML")
    except BaseException as e:
        await msg.reply(f"Произошла ошибка: {e}")
