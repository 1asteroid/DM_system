import logging
import aiohttp
from bot.config import API_URL

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self):
        self._tokens: dict[int, dict] = {}   # tg_id → {access, refresh}

    async def _get(self, tg_id: int, path: str) -> dict | list | None:
        async with aiohttp.ClientSession() as s:
            try:
                r = await s.get(f"{API_URL}{path}", headers=self.get_headers(tg_id))
                if r.status == 200:
                    return await r.json()
            except Exception as e:
                logger.warning("GET %s failed: %s", path, e)
        return None

    async def _post(self, tg_id: int, path: str, json: dict | None = None) -> dict | None:
        async with aiohttp.ClientSession() as s:
            try:
                r = await s.post(f"{API_URL}{path}", json=json, headers=self.get_headers(tg_id))
                if r.status in (200, 201):
                    return await r.json()
            except Exception as e:
                logger.warning("POST %s failed: %s", path, e)
        return None

    async def login(self, email: str, password: str) -> dict | None:
        async with aiohttp.ClientSession() as s:
            try:
                r = await s.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
                if r.status == 200:
                    return await r.json()
            except Exception as e:
                logger.warning("Login failed: %s", e)
        return None

    def save_tokens(self, tg_id: int, data: dict):
        self._tokens[tg_id] = {
            "access":  data["access_token"],
            "refresh": data["refresh_token"],
        }

    def get_headers(self, tg_id: int) -> dict:
        token = self._tokens.get(tg_id, {}).get("access", "")
        return {"Authorization": f"Bearer {token}"}

    async def get_me(self, tg_id: int) -> dict | None:
        return await self._get(tg_id, "/auth/me")

    async def get_topics(self, tg_id: int) -> list:
        data = await self._get(tg_id, "/topics")
        if isinstance(data, dict):
            return data.get("items", [])
        return []

    async def get_topic(self, tg_id: int, topic_id: int) -> dict | None:
        return await self._get(tg_id, f"/topics/{topic_id}")

    async def get_notifications(self, tg_id: int) -> list:
        result = await self._get(tg_id, "/notifications")
        return result if isinstance(result, list) else []

    async def get_contacts(self, tg_id: int) -> list:
        result = await self._get(tg_id, "/messages/contacts")
        return result if isinstance(result, list) else []

    async def get_conversation(self, tg_id: int, other_user_id: int) -> list:
        result = await self._get(tg_id, f"/messages/conversation/{other_user_id}")
        return result if isinstance(result, list) else []

    async def send_message(self, tg_id: int, receiver_id: int, content: str) -> dict | None:
        return await self._post(tg_id, "/messages", {"receiver_id": receiver_id, "content": content})

    async def get_group_messages(self, tg_id: int, topic_id: int) -> list:
        result = await self._get(tg_id, f"/messages/group/{topic_id}")
        return result if isinstance(result, list) else []

    async def send_group_message(self, tg_id: int, topic_id: int, content: str) -> dict | None:
        return await self._post(tg_id, "/messages/group", {"topic_id": topic_id, "content": content})

    async def search_users(self, tg_id: int, query: str) -> list:
        async with aiohttp.ClientSession() as s:
            try:
                r = await s.get(
                    f"{API_URL}/users/search",
                    params={"q": query},
                    headers=self.get_headers(tg_id)
                )
                if r.status == 200:
                    return await r.json()
            except Exception as e:
                logger.warning("User search failed: %s", e)
        return []

    async def get_my_supervisor(self, tg_id: int) -> dict | None:
        return await self._get(tg_id, "/users/my-supervisor")

    async def dashboard(self, tg_id: int) -> dict | None:
        return await self._get(tg_id, "/reports/dashboard")

    async def get_risk_assessments(self, tg_id: int) -> list:
        result = await self._get(tg_id, "/risk/assessments")
        return result if isinstance(result, list) else []

    async def assess_risk(self, tg_id: int, topic_id: int) -> dict | None:
        return await self._post(tg_id, f"/risk/assess/{topic_id}")

    async def analyze_text(self, tg_id: int, topic_id: int, content: str) -> dict | None:
        return await self._post(tg_id, "/analysis/text", {"topic_id": topic_id, "content": content})

    async def save_telegram_id(self, tg_id: int) -> dict | None:
        return await self._post(tg_id, "/auth/telegram", {"telegram_id": str(tg_id)})


api_client = ApiClient()
