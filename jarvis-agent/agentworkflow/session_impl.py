from typing import List
import os
from supabase import create_client, Client

class PostgreSQLSession:
    """Custom session implementation following the Session protocol."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment variables.")
        self.supabase: Client = create_client(url, key)

    async def get_items(self, limit: int | None = None) -> List[dict]:
        """Retrieve conversation history for this session."""
        response = self.supabase.table("sessions").select("history").eq("id", self.session_id).execute()
        return response.data[0]["history"] if response and response.data else []

    async def add_items(self, items: List[dict]) -> None:
        """Store new items for this session."""
        old_items = await self.get_items()
        if not old_items:
            old_items = []
        items = old_items + items
        self.supabase.table("sessions").update({"history": items}).eq("id", self.session_id).execute()

    async def pop_item(self) -> dict | None:
        """Remove and return the most recent item from this session."""
        items = await self.get_items()
        if not items:
            return None
        item = items.pop()
        self.supabase.table("sessions").update({"history": items}).eq("id", self.session_id).execute()
        return item

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        self.supabase.table("sessions").update({"history": []}).eq("id", self.session_id).execute()