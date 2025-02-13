from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message

from BaseModeration.BaseModerationHelpers import (
    format_duration,
    format_text,
    parse_command,
    parse_time,
)
from database.moderation import get_moderation_settings
from database.utils import get_user_by_id_or_username
from keyboards.moderationKeyboards import get_moderation_action_kb
from middlefilters.HasPromoteRights import HasPromoteRights

muting_router = Router()


@muting_router.message(Command("mute", ignore_case=True), HasPromoteRights())
async def mute(msg: Message):
    try:
        chat_id = msg.chat.id
        settings = await get_moderation_settings(chat_id)
        mute_settings = settings.get("mute")

        if not mute_settings["enabled"]:
            return

        result, error = await parse_command(msg)
        if error:
            await msg.reply(error)
            return

        until_date = None
        if result["duration"] != "empty":
            until_date = await parse_time(result["duration"])
            print(f"\033[91m{until_date}\033[0m")

        formatted_duration = await format_duration(result["duration"])
        user_id = result["username_or_id"]

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
            target_first_name = db_user.first_name or "пользователь"
        else:
            target_first_name = "пользователь"

        if not user_id:
            await msg.reply(
                "Не удалось определить пользователя. Укажите корректный user_id или username."
            )
            return

        if mute_settings.get("delete_message") and msg.reply_to_message:
            await msg.reply_to_message.delete()

        response_text = await format_text(
            template=mute_settings["text"],
            message=msg,
            target_user_id=user_id,
            target_first_name=target_first_name,
            duration=formatted_duration,
            reason=result["reason"],
        )

        await msg.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            until_date=until_date,
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
        )

        await msg.reply(
            response_text,
            parse_mode="HTML",
            reply_markup=await get_moderation_action_kb(user_id, "mute"),
        )

    except Exception as e:
        await msg.reply(f"Произошла ошибка: {e}")


@muting_router.message(Command("unmute", ignore_case=True), HasPromoteRights())
async def unmute_command(msg: Message):
    try:
        chat_id = msg.chat.id
        settings = await get_moderation_settings(chat_id)
        unmute_settings = settings.get("mute")

        if not unmute_settings["enabled"]:
            return

        user_id = None
        first_name = "<a href='tg://user?id={user_id}'>пользователь</a>"

        if msg.reply_to_message:
            user_id = msg.reply_to_message.from_user.id
            first_name = f"<a href='tg://user?id={user_id}'>{msg.reply_to_message.from_user.first_name}</a>"
        else:
            parts = msg.text.split()
            if len(parts) < 2:
                await msg.reply("Пожалуйста, укажите пользователя для размута.")
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

        await msg.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_voice_notes=True,
                can_send_video_notes=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
            ),
        )

        await msg.reply(
            f"🔊 Пользователь {first_name} был размучен администратором.",
            parse_mode="HTML",
        )
    except BaseException as e:
        await msg.reply(f"Произошла ошибка: {e}")
