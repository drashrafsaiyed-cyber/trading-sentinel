"""Telegram bot client for sending alerts to users."""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramClient:
    """Minimal async Telegram sender. No-ops gracefully if token unset."""

    def __init__(self, token: str | None = None):
        self.token = token or settings.telegram_bot_token

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a Telegram chat. Returns True on success."""
        if not self.enabled:
            logger.debug("Telegram token not set — skipping send to %s", chat_id)
            return False

        url = f"{TELEGRAM_API}/bot{self.token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True
                logger.warning("Telegram send failed: %s %s", resp.status_code, resp.text[:200])
                return False
        except Exception as e:  # noqa: BLE001 — network best-effort
            logger.error("Telegram send error: %s", e)
            return False

    async def get_me(self) -> dict | None:
        """Verify the bot token (used for health checks)."""
        if not self.enabled:
            return None
        url = f"{TELEGRAM_API}/bot{self.token}/getMe"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json().get("result")
        except Exception as e:  # noqa: BLE001
            logger.error("Telegram getMe error: %s", e)
        return None


telegram = TelegramClient()
