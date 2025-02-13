from aiogram.fsm.state import State, StatesGroup


class EditForm(StatesGroup):
    TEXT = State()
    BUTTONS = State()
    MEDIA = State()


class warnForm(StatesGroup):
    DURATION = State()


class AntiFlood(StatesGroup):
    DURATION = State()


class Nsfw(StatesGroup):
    PERCENTAGE = State()
    DURATION = State()


class AntispamStates(StatesGroup):
    managing_chat = State()
    DURATION = State()
    EXCEPTIONS = State()
    FORWARD_EXCEPTIONS = State()
    FORWARD_DURATION = State()
    TLINK_EXCEPTIONS = State()
    TLINK_DURATION = State()
    QUOTES_DURATION = State()
    QUOTES_EXCEPTIONS = State()
    ALL_DURATION = State()
    ALL_EXCEPTIONS = State()


class RulesStates(StatesGroup):
    editing_text = State()

class ModStates(StatesGroup):
    managing_chat = State()