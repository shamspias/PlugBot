import types
import pytest

from app.services.telegram_service import TelegramService


class DummyBot:
    async def set_my_commands(self, *a, **kw): pass

    async def get_webhook_info(self):
        class I: url = ""

        return I()

    async def delete_webhook(self, *a, **kw): pass


class DummyUpdater:
    def __init__(self): self.started = False

    async def start_polling(self, drop_pending_updates: bool = True):
        self.started = True

    async def stop(self): pass


class DummyApp:
    def __init__(self):
        self.bot = DummyBot()
        self.updater = DummyUpdater()

    async def initialize(self): pass

    async def start(self): pass

    async def stop(self): pass

    async def shutdown(self): pass

    def add_handler(self, h): pass


@pytest.mark.asyncio
async def test_initialize_does_not_mark_running(monkeypatch):
    # Minimal Bot/DB stand-ins
    class B: telegram_bot_token = None

    bot = types.SimpleNamespace(
        id="b1", name="t", description="", telegram_bot_token="enc"
    )
    # Fake decrypt to return token
    from app.core import security
    monkeypatch.setattr(security.security_manager, "decrypt_data", lambda v: "token")

    svc = TelegramService(bot, db=None)
    dummy_app = DummyApp()
    monkeypatch.setattr("app.services.telegram_service.Application",
                        types.SimpleNamespace(builder=lambda: types.SimpleNamespace(
                            token=lambda t: types.SimpleNamespace(build=lambda: dummy_app))))
    assert svc.running is False
    ok = await svc.initialize()
    assert ok is True
    # Crucial: still not running until polling starts
    assert svc.running is False

    await svc.start_polling()
    assert svc.running is True
    assert dummy_app.updater.started is True
