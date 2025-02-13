from typing import Optional

from sqlalchemy.future import select

from config import get_session
from database.models import Moderation
from utils.texts import default_moderation_settings


async def get_moderation_settings(chat_id: int, command_type: str = None) -> dict:
    async with get_session() as session:
        query = select(Moderation).filter_by(chat_id=chat_id)

        if command_type:
            query = query.filter_by(command_type=command_type)

        commands = await session.execute(query)
        commands = commands.scalars().all()

        settings = {}
        if command_type:
            if command_type in default_moderation_settings:
                settings[command_type] = default_moderation_settings[
                    command_type
                ].copy()
        else:
            settings = default_moderation_settings.copy()

        for command in commands:
            if command.command_type in settings:
                settings[command.command_type] = {
                    "enabled": command.enabled,
                    "delete_message": command.delete_message,
                    "journal": command.journal,
                    "text": command.text,
                }

        return settings


async def save_moderation_settings(
    chat_id: int,
    command_type: str,
    text: Optional[str] = None,
    delete_message: Optional[bool] = None,
    journal: Optional[bool] = None,
    enabled: Optional[bool] = None,
):
    async with get_session() as session:
        command = await session.scalar(
            select(Moderation).filter_by(chat_id=chat_id, command_type=command_type)
        )

        if command:
            command.text = text if text is not None else command.text
            command.delete_message = (
                delete_message if delete_message is not None else command.delete_message
            )
            command.journal = journal if journal is not None else command.journal
            command.enabled = enabled if enabled is not None else command.enabled
        else:
            new_command = Moderation(
                chat_id=chat_id,
                command_type=command_type,
                text=(
                    text
                    if text is not None
                    else default_moderation_settings[command_type]["text"]
                ),
                delete_message=delete_message if delete_message is not None else False,
                journal=journal if journal is not None else True,
                enabled=enabled if enabled is not None else True,
            )
            session.add(new_command)

        await session.commit()
