from aiogram import Router, F

word_triggers = Router()


@word_triggers.callback_query(F.data.startswith("forbidden_words:"))
async def forbidden_words():
    # TODO: реализовать логику запрещенных слов
    pass