import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import db_manager
from app.models.bot import Bot
from app.core.security import security_manager


@pytest.mark.anyio
async def test_update_bot_does_not_wipe_dify_key_when_blank():
    # Seed a bot with a valid Dify key
    db = next(db_manager.get_db())
    bot = Bot(
        name="EditSecrets",
        dify_endpoint="http://dify.local",
        dify_api_key=security_manager.encrypt_data("REALKEY"),
        dify_type="chat",
        response_mode="streaming",
        max_tokens=1024,
        temperature=5,
        auto_generate_title=True,
        enable_file_upload=True,
    )
    db.add(bot);
    db.commit();
    db.refresh(bot)

    async with AsyncClient(app=app, base_url="http://test") as c:
        # Patch with empty dify_api_key (simulating blank field in edit form)
        r = await c.patch(f"/api/v1/bots/{bot.id}", json={"dify_api_key": ""})
        assert r.status_code == 200

    # Ensure key was NOT wiped
    db.refresh(bot)
    assert security_manager.decrypt_data(bot.dify_api_key) == "REALKEY"
