import httpx
import json
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from ..models.bot import Bot
from ..core.security import security_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DifyService:
    """Service for interacting with Dify API."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.endpoint = bot.dify_endpoint.rstrip('/')
        self.api_key = security_manager.decrypt_data(bot.dify_api_key)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def send_message(
            self,
            message: str,
            conversation_id: Optional[str] = None,
            user_id: str = None,
            files: Optional[list] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send message to Dify and stream response."""
        url = f"{self.endpoint}/chat-messages"

        payload = {
            "inputs": {},
            "query": message,
            "response_mode": self.bot.response_mode,
            "user": user_id or "default-user",
            "auto_generate_name": self.bot.auto_generate_title
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        try:
            if self.bot.response_mode == "streaming":
                async with self.client.stream(
                        "POST",
                        url,
                        json=payload,
                        headers=self.headers
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data:
                                try:
                                    event = json.loads(data)
                                    yield event
                                except json.JSONDecodeError:
                                    logger.error(f"Failed to parse SSE data: {data}")
            else:
                response = await self.client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                yield response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Dify: {e.response.status_code} - {e.response.text}")
            yield {
                "event": "error",
                "message": f"Error from Dify API: {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error sending message to Dify: {str(e)}")
            yield {
                "event": "error",
                "message": f"Error connecting to Dify: {str(e)}"
            }

    async def upload_file(self, file_data: bytes, filename: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Upload file to Dify."""
        url = f"{self.endpoint}/files/upload"

        files = {
            'file': (filename, file_data)
        }
        data = {
            'user': user_id
        }

        try:
            response = await self.client.post(
                url,
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading file to Dify: {str(e)}")
            return None

    async def get_conversation_history(
            self,
            conversation_id: str,
            user_id: str,
            limit: int = 20
    ) -> Optional[Dict[str, Any]]:
        """Get conversation history from Dify."""
        url = f"{self.endpoint}/messages"
        params = {
            "conversation_id": conversation_id,
            "user": user_id,
            "limit": limit
        }

        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return None

    async def health_check(self) -> bool:
        """Check if Dify API is accessible."""
        url = f"{self.endpoint}/parameters"

        try:
            response = await self.client.get(url, headers=self.headers, timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for bot {self.bot.name}: {str(e)}")
            return False
