import pytest
from backend.app.services.email_service import send_email_fallback

class DummyResponse:
    status_code = 202

class DummySendGrid:
    def send(self, message):
        return DummyResponse()

@pytest.mark.asyncio
async def test_send_email_fallback(monkeypatch):
    # Mock SendGrid client
    monkeypatch.setattr(
        "backend.app.services.email_service.sg_client",
        DummySendGrid()
    )

    result = await send_email_fallback(
        to_email="test@example.com",
        query="Test question",
        ai_response="Test response",
        confidence=0.2
    )

    assert result is True
