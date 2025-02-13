import secrets
from datetime import datetime, timedelta

from sqlalchemy.future import select
from sqlalchemy.sql.expression import delete

from config import get_session
from database.models import Session


async def create_session(
    user_id, first_name=None, username=None, photo_url=None, duration_days=7
):
    session_id = secrets.token_urlsafe(16)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=duration_days)

    async with get_session() as session:
        new_session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=created_at,
            expires_at=expires_at,
            first_name=first_name,
            username=username,
            photo_url=photo_url,
        )
        session.add(new_session)
        await session.commit()
        return new_session


async def get_user_session(session_id):
    async with get_session() as session:
        result = await session.execute(select(Session).filter_by(session_id=session_id))
        return result.scalars().first()


async def delete_session(session_id):
    async with get_session() as session:
        await session.execute(delete(Session).where(Session.session_id == session_id))
        await session.commit()


async def cleanup_expired_sessions():
    async with get_session() as session:
        await session.execute(
            delete(Session).where(Session.expires_at < datetime.utcnow())
        )
        await session.commit()
