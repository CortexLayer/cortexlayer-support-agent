from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from backend.app.core.config import settings
from backend.app.utils.logger import logger

# ✅ MUST exist at module level for monkeypatching
sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)


async def send_email_fallback(
    to_email: str,
    query: str,
    ai_response: str,
    confidence: float,
) -> bool:
    """
    Send email fallback when AI confidence is low.
    """

    message = Mail(
        from_email="support@cortexlayer.com",
        to_emails=to_email,
        subject=f"Your Question: {query[:50]}...",
        html_content=f"""
        <h3>We need a human to help</h3>
        <p><b>Question:</b> {query}</p>
        <p><b>AI Response (confidence {confidence:.0%}):</b></p>
        <p>{ai_response}</p>
        """,
    )

    try:
        sg_client.send(message)
        logger.info(f"📧 Fallback email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
