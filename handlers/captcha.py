from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.captcha import get_captcha_settings, save_captcha_settings
from keyboards.captchaKeyboards import captcha_kb
from utils.states import ModStates

captcha_router = Router()

TEXTS = {
    "main": (
        "<b>🤖 Капча</b>\n"
        "В этом меню вы можете включить или выключить капчу для новых участников.\n\n"
        "Статус: {}"
    )
}


@captcha_router.callback_query(F.data.startswith("captcha:"))
async def captcha_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.data.split(":")[-1]
    await state.set_state(ModStates.managing_chat)
    await state.update_data(chat_id=chat_id)
    settings = await get_captcha_settings(chat_id)
    status = "✅" if settings["enable"] else "❌"
    await callback.message.edit_text(
        text=TEXTS["main"].format(status),
        reply_markup=await captcha_kb(chat_id),
        parse_mode="HTML",
    )


@captcha_router.callback_query(F.data.startswith("scaptcha:"))
async def captcha_settings(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = int(data.get("chat_id"))
    action = callback.data.split(":")[1]

    if action == "switch":
        settings = await get_captcha_settings(chat_id)
        enable = not settings["enable"]
        await save_captcha_settings(chat_id=chat_id, enable=enable)

        status = "✅" if enable else "❌"
        await callback.message.edit_text(
            text=TEXTS["main"].format(status),
            reply_markup=await captcha_kb(chat_id),
            parse_mode="HTML",
        )
