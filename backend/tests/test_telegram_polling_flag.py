import pytest
from types import SimpleNamespace
from app.services.telegram_service import TelegramService
from app.core.security import security_manager


class DummyBot:
    def __init__(self):
        self.deleted = False

    async def set_my_commands(self, *args, **kwargs):
        pass

    async def get_webhook_info(self):
        # Mimic no webhook set
        return SimpleNamespace(url="")

    async def delete_webhook(self, drop_pending_updates=True):
        self.deleted = True


class DummyApp:
    def __init__(self):
        self.updater = SimpleNamespace(start_polling=self._start_polling)
        self.started = False
        self.polled = False
        self._bot = DummyBot()

    async def initialize(self):  # not used in this test
        pass

    async def start(self):
        self.started = True

    async def stop(self):
        pass

    async def shutdown(self):
        pass

    async def _start_polling(self, drop_pending_updates=True):
        self.polled = True

    @property
    def bot(self):
        return self._bot


@pytest.mark.asyncio
async def test_start_polling_sets_running(monkeypatch):
    # Minimal fake Bot record
    bot = type(
        "B",
        (),
        {
            "id": "b1",
            "name": "Test",
            "description": None,
            "dify_endpoint": "http://example.com",
            "dify_api_key": security_manager.encrypt_data("k"),
            "dify_type": "chat",
            "response_mode": "blocking",
            "auto_generate_title": True,
            "enable_file_upload": True,
            "telegram_bot_token": security_manager.encrypt_data("t"),
        },
    )()
    svc = TelegramService(bot, db=None)
    svc.application = DummyApp()

    assert svc.running is False

    await svc.start_polling()

    assert svc.running is True
    assert svc.application.started
    assert svc.application.polled
