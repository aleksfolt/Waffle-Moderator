from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.blockItems import (
    add_item_to_block,
    get_items_from_block,
    remove_item_from_block,
)
from keyboards.handlersKeyboards import stickers_kb

stick_router = Router()


@stick_router.message(Command("block", ignore_case=True))
async def block(msg: Message):
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    if not msg.reply_to_message:
        await msg.reply("Ответьте на стикер/гиф, который хотите заблокировать.")
        return

    if msg.reply_to_message.animation:
        await msg.answer(
            text="✅ Хорошо, GIF заблокирован.",
            reply_to_message_id=msg.reply_to_message.message_id,
        )
        await add_item_to_block(
            chat_id=chat_id,
            to_block="gifs",
            item=msg.reply_to_message.animation.file_id,
        )
        return

    if msg.reply_to_message.sticker:
        await msg.answer(
            text="Выберите что хотите заблокировать:",
            reply_to_message_id=msg.reply_to_message.message_id,
            reply_markup=await stickers_kb(user_id),
        )
        return
    await msg.reply("Ответьте на стикер/гиф, который хотите заблокировать.")


@stick_router.callback_query(F.data.startswith("block:"))
async def block_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id != int(callback.data.split(":")[2]):
        await callback.answer("Все для тебя, но только не эта кнопка.", show_alert=True)
        return

    chat_id = callback.message.chat.id
    sticker = callback.message.reply_to_message.sticker
    if not sticker:
        await callback.answer("Неверное действие: стикер отсутствует.", show_alert=True)
        return
    if callback.data.split(":")[1] == "sticker":
        await add_item_to_block(
            chat_id=chat_id, to_block="stickers", item=sticker.file_id
        )
        await callback.message.edit_text("✅ Стикер успешно заблокирован.")
    else:
        await add_item_to_block(
            chat_id=chat_id, to_block="set_stickers", item=sticker.set_name
        )
        await callback.message.edit_text("✅ Набор стикеров успешно заблокирован.")


@stick_router.message(Command("unblock", ignore_case=True))
async def unblock(msg: Message):
    chat_id = msg.chat.id

    if not msg.reply_to_message or not (
        msg.reply_to_message.sticker or msg.reply_to_message.animation
    ):
        await msg.reply("Ответьте на стикер или GIF, который хотите разблокировать.")
        return

    if msg.reply_to_message.sticker:
        sticker_id = msg.reply_to_message.sticker.file_id
        sticker_set_name = msg.reply_to_message.sticker.set_name

        await remove_item_from_block(chat_id, "stickers", sticker_id)
        if sticker_set_name:
            await remove_item_from_block(chat_id, "set_stickers", sticker_set_name)

        await msg.reply("✅ Стикер/набор успешно разблокированы.")
        return

    if msg.reply_to_message.animation:
        gif_id = msg.reply_to_message.animation.file_id

        await remove_item_from_block(chat_id, "gifs", gif_id)

        await msg.reply("✅ GIF успешно разблокирован.")


async def block_stickers(msg: Message):
    chat_id = msg.chat.id
    sticker_id = msg.sticker.file_id
    sticker_set_name = msg.sticker.set_name

    blocked_stickers = await get_items_from_block(chat_id, "stickers")
    blocked_sets = await get_items_from_block(chat_id, "set_stickers")

    if sticker_id in blocked_stickers or (
        sticker_set_name and sticker_set_name in blocked_sets
    ):
        await msg.delete()


async def block_gifs(msg: Message):
    chat_id = msg.chat.id
    gif_id = msg.animation.file_id

    blocked_gifs = await get_items_from_block(chat_id, "gifs")

    if gif_id in blocked_gifs:
        await msg.delete()
