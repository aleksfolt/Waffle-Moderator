import os
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageOriginChannel,
    MessageOriginUser,
)

import config
from BaseModeration.BaseModerationHelpers import punish_user
from database.antispam import (
    get_all_settings,
    get_forward_settings,
    get_quotes_settings,
    get_tlink_settings,
)
from database.utils import add_or_update_chat, get_chat, get_chat_admins, get_user_chats
from handlers.antiflood import check_antiflood
from handlers.blockStickers import block_gifs, block_stickers
from handlers.nsfwFilter import check_nsfw_photo
from keyboards.handlersKeyboards import chat_settings_kb, pm_link

handlers_router = Router()


async def get_chat_administrators(message: Message, chat_id):
    admins = await message.bot.get_chat_administrators(chat_id)
    admin_ids = []
    for admin in admins:
        if admin.status == "creator" or (
            admin.status == "administrator"
            and admin.can_manage_chat
            and admin.can_delete_messages
            and admin.can_manage_voice_chats
            and admin.can_restrict_members
            and admin.can_promote_members
            and admin.can_change_info
            and admin.can_invite_users
            and admin.can_pin_messages
        ):
            admin_ids.append(admin.user.id)
    return admin_ids


@handlers_router.message(Command("start", ignore_case=True))
async def start(message: Message):
    if message.chat.type == "private":
        chats = await get_user_chats(message.from_user.id)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=chat.title, callback_data=f"chat_{chat.chat_id}"
                    )
                ]
                for chat in chats
            ]
        )

        await message.answer(
            f"Привет! Я {config.BOT_NAME}, бот для модерации чатов. "
            f"Настройки Группы\n"
            "👉🏻 Выберите группу, настройки которой вы хотите изменить.",
            reply_markup=keyboard,
        )
    else:
        await message.answer("Hello!", reply_markup=await pm_link())


@handlers_router.callback_query(F.data.startswith("chat_"))
async def chat_callback(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    chat = await get_chat(chat_id)
    await callback.message.edit_text(
        text=f"Настройки группы {chat.title}\n\nВыберите один из параметров, который вы хотите изменить.",
        reply_markup=await chat_settings_kb(chat_id),
    )


async def update_chat_info(msg: Message) -> None:
    chat_id = msg.chat.id

    if msg.new_chat_title:
        await add_or_update_chat(chat_id=chat_id, title=msg.new_chat_title)


@handlers_router.my_chat_member()
async def handle_chat_member_update(event: ChatMemberUpdated):
    print("/event")
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    print(f"Статус изменился: {old_status} -> {new_status}")

    if event.new_chat_member.user.id == event.bot.id:
        if new_status in {"kicked", "left"}:
            chat = await get_chat(event.chat.id)
            admins = chat.admins if chat and chat.admins else []
            for admin in admins:
                try:
                    await event.bot.send_message(
                        chat_id=int(admin), text="Бот отвязан от чата."
                    )
                except Exception:
                    continue
        elif new_status == "member":
            await event.answer(
                f"Всем привет! Я — {config.BOT_NAME}, и я здесь, чтобы внести… "
                "ну, хоть какую-то видимость порядка. Так что не удивляйтесь, "
                "если что-то внезапно исчезнет."
            )
        elif new_status == "administrator":
            chat = await event.bot.get_chat(event.chat.id)
            members_count = await event.bot.get_chat_member_count(chat.id)
            admins = await get_chat_administrators(event, chat.id)
            all_admins = [
                admin.user.id
                for admin in await event.bot.get_chat_administrators(chat.id)
            ]

            await add_or_update_chat(
                chat_id=chat.id,
                title=chat.title,
                members_count=members_count,
                work=True,
                admins=admins,
                all_admins=all_admins,
            )

            await event.answer(
                "Спасибо за предоставленные права администратора! "
                "Информация о чате сохранена в базе данных.",
                reply_markup=await pm_link(),
            )


@handlers_router.chat_member()
async def handle_admin_status(event: ChatMemberUpdated):
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    user_id = event.new_chat_member.user.id

    chat = await get_chat(event.chat.id)
    if not chat:
        return

    if old_status not in ["administrator", "creator"] and new_status in [
        "administrator",
        "creator",
    ]:
        if not chat.all_admins:
            chat.all_admins = []
        if user_id not in chat.all_admins:
            chat.all_admins.append(user_id)
            await add_or_update_chat(chat_id=chat.chat_id, all_admins=chat.all_admins)

    elif old_status in ["administrator", "creator"] and new_status not in [
        "administrator",
        "creator",
    ]:
        if chat.all_admins and user_id in chat.all_admins:
            chat.all_admins.remove(user_id)
            await add_or_update_chat(chat_id=chat.chat_id, all_admins=chat.all_admins)


async def check_message_origin(msg: Message):
    chat_id = msg.chat.id
    entity_type = None
    should_punish = False

    if msg.external_reply:
        chat = msg.external_reply.chat
        origin = msg.external_reply.origin

        if chat and chat.type in ["group", "supergroup"]:
            entity_type = "chats"
        elif chat and chat.type == "channel":
            entity_type = "channels"
        elif isinstance(origin, MessageOriginUser):
            sender = origin.sender_user
            entity_type = "bots" if sender.is_bot else "users"
        elif isinstance(origin, MessageOriginChannel):
            entity_type = "channels"

        if entity_type:
            settings = await get_quotes_settings(chat_id, entity_type)

            if settings["enable"] and (
                not msg.from_user or msg.from_user.id not in settings["exceptions"]
            ):
                should_punish = True
                if settings["delete_message"]:
                    try:
                        await msg.delete()
                    except Exception:
                        pass

                if should_punish and msg.from_user:
                    await punish_user(
                        msg,
                        settings["action"],
                        settings["duration_actions"],
                        f"Цитата из чата ({entity_type})",
                    )

    return entity_type, should_punish


async def check_message_forward(msg: Message):
    chat_id = msg.chat.id
    entity_type = None
    should_punish = False

    if msg.forward_origin or msg.forward_from:
        if isinstance(msg.forward_origin, MessageOriginUser):
            sender = msg.forward_origin.sender_user
            entity_type = "bots" if sender.is_bot else "users"
        elif isinstance(msg.forward_origin, MessageOriginChannel):
            entity_type = "channels"
        elif msg.forward_from:
            entity_type = "bots" if msg.forward_from.is_bot else "users"
        elif msg.forward_from_chat:
            if msg.forward_from_chat.type in ["group", "supergroup"]:
                entity_type = "chats"
            elif msg.forward_from_chat.type == "channel":
                entity_type = "channels"
    else:
        return None, False

    if entity_type:
        settings = await get_forward_settings(chat_id, entity_type)

        if settings["enable"] and (
            not msg.from_user or msg.from_user.id not in settings["exceptions"]
        ):
            should_punish = True
            if settings["delete_message"]:
                try:
                    await msg.delete()
                except Exception:
                    pass

            if should_punish and msg.from_user:
                await punish_user(
                    msg,
                    settings["action"],
                    settings["duration_actions"],
                    f"Пересылка из чата ({entity_type})",
                )

    return entity_type, should_punish


async def check_tlink_message(msg: Message):
    chat_id = msg.chat.id
    should_punish = False
    has_tlink = False
    has_username = False
    has_bot = False

    settings = await get_tlink_settings(chat_id)

    if msg.entities and msg.text:
        for entity in msg.entities:
            if entity.type == "url":
                url = msg.text[entity.offset : entity.offset + entity.length]
                tlink_pattern = r"^(?:https?:\/\/)?(?:[\w-]+\.)?t(?:elegram)?\.me\/"
                if re.match(tlink_pattern, url, re.IGNORECASE):
                    has_tlink = True
                    break

    if msg.text:
        username_pattern = r"^@\w{4,}$"
        bot_username_pattern = r"^@\w{4,}bot$"

        if settings["username"] and re.match(username_pattern, msg.text):
            has_username = True

        if settings["bot"] and re.match(bot_username_pattern, msg.text):
            has_bot = True

    if (
        has_tlink
        or (has_username and settings["username"])
        or (has_bot and settings["bot"])
    ):
        if settings["enable"] and (
            not msg.from_user or msg.from_user.id not in settings["exceptions"]
        ):
            should_punish = True
            if settings["delete_message"]:
                try:
                    await msg.delete()
                except Exception as e:
                    print(f"Failed to delete message: {e}")

            if should_punish and msg.from_user:
                violation_type = (
                    "t.me link"
                    if has_tlink
                    else "username" if has_username else "bot username"
                )
                await punish_user(
                    msg,
                    settings["action"],
                    settings["duration_action"],
                    f"Телеграм ссылки ({violation_type})",
                )

    return should_punish


async def check_link_message(msg: Message):
    chat_id = msg.chat.id
    should_punish = False
    has_link = False

    settings = await get_all_settings(chat_id)

    if msg.entities and msg.text:
        for entity in msg.entities:
            if entity.type == "url":
                url = msg.text[entity.offset : entity.offset + entity.length]
                has_link = True
                print(f"🔗 Found link: {url}")
                break

    if has_link:
        if settings["enable"] and (
            not msg.from_user or msg.from_user.id not in settings["exceptions"]
        ):
            should_punish = True
            if settings["delete_message"]:
                try:
                    await msg.delete()
                except Exception as e:
                    print(f"Failed to delete message: {e}")

            if should_punish and msg.from_user:
                await punish_user(
                    msg,
                    settings["action"],
                    settings["duration_actions"],
                    "Ссылки в сообщении",
                )

    return should_punish


@handlers_router.message()
async def handle_message(msg: Message):
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    admin_ids = set(await get_chat_admins(chat_id))
    is_admin = user_id in admin_ids

    if not is_admin:
        await check_antiflood(msg, chat_id, user_id)
        if any([msg.forward_origin, msg.forward_from, msg.forward_from_chat]):
            entity_type, was_punished = await check_message_forward(msg)
            if was_punished:
                return

        if msg.external_reply or msg.reply_to_message:
            entity_type, was_punished = await check_message_origin(msg)
            if was_punished:
                return

        if (
            msg.entities
            and msg.text
            or (
                msg.text
                and (
                    msg.text.startswith("@")
                    or re.search(
                        r"t(?:elegram)?\.me|https?://t(?:elegram)?\.me",
                        msg.text.lower(),
                    )
                )
            )
        ):
            was_punished = await check_tlink_message(msg)
            if was_punished:
                return

        if msg.entities and msg.text:
            was_punished = await check_link_message(msg)
            if was_punished:
                return
    if msg.animation:
        await block_gifs(msg)
    elif msg.sticker:
        await block_stickers(msg)
    elif msg.photo:
        await check_nsfw_photo(msg, chat_id)

    await update_chat_info(msg)
