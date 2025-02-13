from typing import Optional

from sqlalchemy.future import select

from config import get_session
from database.models import Report


async def get_report_settings(chat_id: int):
    async with get_session() as session:
        report = await session.scalar(select(Report).filter_by(chat_id=chat_id))
        if report:
            return {
                "enable_reports": report.work,
                "delete_reported_messages": report.delete_reported_messages,
                "report_text_template": report.report_text_template,
                "buttons": report.buttons if report.buttons else [],
            }
        return {
            "enable_reports": True,
            "delete_reported_messages": False,
            "report_text_template": "Репорт отправлен!",
            "buttons": [],
        }


async def save_report_settings(
    chat_id: int,
    enable_reports: Optional[bool] = None,
    delete_reported_messages: Optional[bool] = None,
    report_text_template: Optional[str] = None,
    buttons: Optional[list] = None,
):
    async with get_session() as session:
        report = await session.scalar(select(Report).filter_by(chat_id=chat_id))

        if report:
            if enable_reports is not None:
                report.work = enable_reports
            if delete_reported_messages is not None:
                report.delete_reported_messages = delete_reported_messages
            if report_text_template is not None:
                report.report_text_template = report_text_template
            if buttons is not None:
                report.buttons = buttons
        else:
            report = Report(
                chat_id=chat_id,
                work=enable_reports if enable_reports is not None else False,
                delete_reported_messages=(
                    delete_reported_messages
                    if delete_reported_messages is not None
                    else False
                ),
                report_text_template=(
                    report_text_template if report_text_template is not None else ""
                ),
                buttons=buttons if buttons is not None else [],
            )
            session.add(report)

        await session.commit()
