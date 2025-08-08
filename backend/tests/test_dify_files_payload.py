import pytest
from app.services.dify_service import DifyService
from app.core.security import security_manager


@pytest.mark.asyncio
async def test_send_message_includes_files(monkeypatch):
    bot = type("B", (), {
        "name": "Test",
        "dify_endpoint": "http://example.com",
        "dify_api_key": security_manager.encrypt_data("k"),
        "response_mode": "blocking",
        "auto_generate_title": True,
    })()
    svc = DifyService(bot)

    captured = {}

    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):
            # Simulate a minimal non-streaming response body
            return {"ok": True}

    async def fake_post(url, json=None, headers=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = json
        return DummyResp()

    # Patch the underlying HTTP client's post
    monkeypatch.setattr(svc.client, "post", fake_post)

    gen = svc.send_message(
        "hi",
        user_id="u1",
        files=[{"type": "image", "transfer_method": "local_file", "upload_file_id": "fid"}],
    )

    # Drain the async generator (it may yield zero or more events depending on mode)
    _ = [event async for event in gen]

    assert "payload" in captured
    assert "files" in captured["payload"]
    assert captured["payload"]["files"][0]["upload_file_id"] == "fid"
