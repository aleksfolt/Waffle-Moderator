from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

from config import engine

Base = declarative_base()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    def __repr__(self):
        return (
            f"<User(user_id={self.user_id}, username='{self.username}', "
            f"first_name='{self.first_name}', last_name='{self.last_name}')>"
        )


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    first_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)

    def __repr__(self):
        return (
            f"<Session(session_id='{self.session_id}', user_id={self.user_id}, "
            f"created_at='{self.created_at}', expires_at='{self.expires_at}')>"
        )


class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    title = Column(String, nullable=False)
    members_count = Column(BigInteger, nullable=False, default=0)
    work = Column(Boolean, nullable=False, default=False)
    net = Column(BigInteger, nullable=True)
    admins = Column(JSON, nullable=False, default=[])
    all_admins = Column(JSON, nullable=False, default=[])

    def __repr__(self):
        return (
            f"<Chat(chat_id={self.chat_id}, title={repr(self.title)}, "
            f"members_count={self.members_count}, work={self.work}, "
            f"net={self.net}, admins={self.admins}, all_admins={self.all_admins})>"
        )


class Report(Base):
    __tablename__ = "reports"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    work = Column(Boolean, nullable=False, default=True)
    delete_reported_messages = Column(Boolean, nullable=False, default=False)
    report_text_template = Column(Text, nullable=False, default="Репорт отправлен!")
    buttons = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return (
            f"<Report(chat_id={self.chat_id}, work={self.work}, "
            f"delete_reported_messages={self.delete_reported_messages}, "
            f"report_text_template='{self.report_text_template}', "
            f"buttons={self.buttons})>"
        )


class Moderation(Base):
    __tablename__ = "moderation_commands"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    command_type = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    text = Column(Text, nullable=True)
    delete_message = Column(Boolean, nullable=False, default=False)
    journal = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return (
            f"<ModerationCommand(id={self.id}, chat_id={self.chat_id}, "
            f"command_type='{self.command_type}', enabled={self.enabled}, "
            f"text='{self.text}', delete_message={self.delete_message}, "
            f"journal={self.journal})>"
        )


class Block(Base):
    __tablename__ = "blocks"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    stickers = Column(JSON, nullable=False, default=list)
    gifs = Column(JSON, nullable=False, default=list)
    set_stickers = Column(JSON, nullable=False, default=list)

    def __repr__(self):
        return (
            f"<Block(chat_id={self.chat_id}, stickers={self.stickers}, "
            f"gifs={self.gifs}, set_stickers={self.set_stickers})>"
        )


class ChatSettings(Base):
    __tablename__ = "block_channels"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=False)
    text = Column(String, nullable=True, default="Обнаружен канал! Блокирую..")
    buttons = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return (
            f"<ChatSettings(chat_id={self.chat_id}, enable={self.enable}, "
            f"text='{self.text}')>"
        )


class Warns(Base):
    __tablename__ = "warns"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=True)
    text = Column(
        String,
        nullable=True,
        default="%%__mention__%% [%%__user_id__%%] предупрежден (%%__warn_count__%%/%%__max_warns__%%).",
    )
    action = Column(String, nullable=False, default="mute")
    duration_action = Column(String, nullable=False, default=3600)
    warns_count = Column(Integer, nullable=False, default=3)

    def __repr__(self):
        return (
            f"<Warns(chat_id={self.chat_id}, enable={self.enable}, "
            f"text='{self.text}', action='{self.action}', "
            f"duration_action={self.duration_action}, warns_count={self.warns_count})>"
        )


class UserWarn(Base):
    __tablename__ = "user_warns"

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, primary_key=True)
    warns = Column(Integer, default=0)

    def __repr__(self):
        return f"<Warn(user_id={self.user_id}, chat_id={self.chat_id}, warns={self.warns})>"


class AntiFlood(Base):
    __tablename__ = "antiflood"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    messages = Column(Integer, nullable=False, default=3)
    time = Column(Integer, nullable=False, default=2)
    enable = Column(Boolean, nullable=False, default=True)
    action = Column(String, nullable=False, default="mute")
    delete_message = Column(Boolean, nullable=False, default=True)
    duration_action = Column(String, nullable=False, default="3600")
    journal = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return (
            f"<AntiFlood(chat_id={self.chat_id}, messages={self.messages}, time={self.time}, "
            f"enable={self.enable}, action='{self.action}', delete_message={self.delete_message}, "
            f"duration_action='{self.duration_action}', journal={self.journal})>"
        )


class NsfwFilter(Base):
    __tablename__ = "nsfw_filter"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=False)
    percent = Column(Integer, nullable=False, default=80)
    journal = Column(Boolean, nullable=False, default=True)
    action = Column(String, nullable=False, default="mute")
    duration_action = Column(String, nullable=False, default="3600")
    delete_message = Column(Boolean, nullable=False, default=True)
    text = Column(String, nullable=True, default="Обнаружен небезопасный контент!")
    buttons = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return (
            f"<ChatSettings(chat_id={self.chat_id}, enable={self.enable}, percent={self.percent}, "
            f"journal={self.journal}, text='{self.text}', buttons={self.buttons})>"
        )


class AntiSpamTLink(Base):
    __tablename__ = "antispam_tlink"
    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=True)
    action = Column(String, nullable=False, default="mute")
    delete_message = Column(Boolean, nullable=False, default=True)
    duration_action = Column(String, nullable=False, default="3600")
    username = Column(Boolean, nullable=False, default=True)
    bot = Column(Boolean, nullable=False, default=True)
    exceptions = Column(JSON, nullable=True, default=list)

    def __repr__(self):
        return (
            f"<AntiSpamTLink(chat_id={self.chat_id}, enable='{self.enable}', "
            f"action='{self.action}', delete_message={self.delete_message}, "
            f"duration_action='{self.duration_action}', username={self.username}, "
            f"bot={self.bot}, exceptions={self.exceptions})>"
        )


class AntiSpamForward(Base):
    __tablename__ = "antispam_forward"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    enable = Column(Boolean, nullable=False, default=False)
    action = Column(String, nullable=False, default="mute")
    duration_actions = Column(String, nullable=False, default="3600")
    delete_message = Column(Boolean, nullable=False, default=True)
    exceptions = Column(JSON, nullable=True, default=list)

    def __repr__(self):
        return (
            f"<AntiSpamForward(id={self.id}, chat_id={self.chat_id}, entity_type='{self.entity_type}', "
            f"enable={self.enable}, action='{self.action}', duration_actions='{self.duration_actions}', "
            f"delete_message={self.delete_message}, exceptions={self.exceptions})>"
        )


class AntiSpamQuotes(Base):
    __tablename__ = "antispam_quotes"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    enable = Column(Boolean, nullable=False, default=False)
    action = Column(String, nullable=False, default="mute")
    duration_actions = Column(String, nullable=False, default="3600")
    delete_message = Column(Boolean, nullable=False, default=True)
    exceptions = Column(JSON, nullable=True, default=list)

    def __repr__(self):
        return (
            f"<AntiSpamQuotes(id={self.id}, chat_id={self.chat_id}, entity_type='{self.entity_type}', "
            f"enable={self.enable}, action='{self.action}', duration_actions='{self.duration_actions}', "
            f"delete_message={self.delete_message}, exceptions={self.exceptions})>"
        )


class AntiSpamAll(Base):
    __tablename__ = "antispam_all"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    enable = Column(Boolean, nullable=False, default=False)
    action = Column(String, nullable=False, default="mute")
    duration_actions = Column(String, nullable=False, default="3600")
    delete_message = Column(Boolean, nullable=False, default=True)
    exceptions = Column(JSON, nullable=True, default=list)

    def __repr__(self):
        return (
            f"<AntiSpamAll(id={self.id}, chat_id={self.chat_id}, enable={self.enable}, "
            f"action='{self.action}', duration_actions='{self.duration_actions}', "
            f"delete_message={self.delete_message}, exceptions={self.exceptions})>"
        )


class Rules(Base):
    __tablename__ = "rules"
    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=False)
    text = Column(String, nullable=True, default="Правила")
    buttons = Column(JSON, nullable=True, default=dict)
    permissions = Column(String, nullable=True, default="members")

    def __repr__(self):
        return (
            f"<Rules(id={self.id}, chat_id={self.chat_id}, enable={self.enable}, "
            f"text='{self.text}', buttons={self.buttons}, permissions='{self.permissions}')>"
        )


class Captcha(Base):
    __tablename__ = "captcha"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Captcha(chat_id={self.chat_id}, enable={self.enable})>"


class Meeting(Base):
    __tablename__ = "meetings"
    chat_id = Column(BigInteger, primary_key=True, unique=True)
    enable = Column(Boolean, nullable=False, default=True)
    text = Column(String, nullable=True, default="Приветствуем в нашем чате!")
    buttons = Column(JSON, nullable=True, default=dict)
    media_link = Column(String, nullable=True, default=None)
    always_send = Column(Boolean, nullable=False, default=False)
    delete_last_message = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return (
            f"<Meeting(id={self.id}, chat_id={self.chat_id}, enable={self.enable}, "
            f"text='{self.text}', buttons={self.buttons}, always_send={self.always_send}, "
            f"delete_last_message={self.delete_last_message})>"
        )


class MeetingHistory(Base):
    __tablename__ = "meeting_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=True)
    first_joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_welcomed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_chat_user", chat_id, user_id, unique=True),)

    def __repr__(self):
        return (
            f"<MeetingHistory(id={self.id}, chat_id={self.chat_id}, "
            f"user_id={self.user_id}, message_id={self.message_id}, "
            f"first_joined_at='{self.first_joined_at}', "
            f"last_welcomed_at='{self.last_welcomed_at}')>"
        )
