import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_NAME, DATABASE_URI

logging.basicConfig(level=logging.INFO)


class Database:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

        # Collections for storing fsub chats
        self.fsub_chat1 = self.db["fsub_chat1"]
        self.fsub_chat2 = self.db["fsub_chat2"]

    async def add_fsub_chat1(self, chat_id: int, invite_link: str) -> bool:
        """Add or update fsub chat 1 details."""
        try:
            await self.fsub_chat1.delete_many({})  # Remove existing entry
            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            await self.fsub_chat1.insert_one({
                "chat_id": chat_id,
                "invite_link": invite_link,
                "switch_time": switch_time
            })
            return True
        except Exception as e:
            logging.error(f"Error adding fsub chat 1: {e}")
            return False

    async def add_fsub_chat2(self, chat_id: int, invite_link: str) -> bool:
        """Add or update fsub chat 2 details."""
        try:
            await self.fsub_chat2.delete_many({})  # Remove existing entry
            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            await self.fsub_chat2.insert_one({
                "chat_id": chat_id,
                "invite_link": invite_link,
                "switch_time": switch_time
            })
            return True
        except Exception as e:
            logging.error(f"Error adding fsub chat 2: {e}")
            return False

    async def get_fsub_chat1(self) -> dict | None:
        """Retrieve fsub chat 1 details."""
        return await self.fsub_chat1.find_one({})

    async def get_fsub_chat2(self) -> dict | None:
        """Retrieve fsub chat 2 details."""
        return await self.fsub_chat2.find_one({})

    async def update_fsub_link1(self, chat_id: int, new_link: str) -> bool:
        """Update the invite link for fsub chat 1."""
        try:
            result = await self.fsub_chat1.update_one(
                {"chat_id": chat_id},
                {"$set": {"invite_link": new_link}}
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating invite link for chat 1: {e}")
            return False

    async def update_fsub_link2(self, chat_id: int, new_link: str) -> bool:
        """Update the invite link for fsub chat 2."""
        try:
            result = await self.fsub_chat2.update_one(
                {"chat_id": chat_id},
                {"$set": {"invite_link": new_link}}
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating invite link for chat 2: {e}")
            return False

    async def delete_fsub_chat1(self) -> bool:
        """Delete all data from fsub chat 1."""
        try:
            await self.fsub_chat1.delete_many({})
            return True
        except Exception as e:
            logging.error(f"Error deleting fsub chat 1: {e}")
            return False

    async def delete_fsub_chat2(self) -> bool:
        """Delete all data from fsub chat 2."""
        try:
            await self.fsub_chat2.delete_many({})
            return True
        except Exception as e:
            logging.error(f"Error deleting fsub chat 2: {e}")
            return False

    async def get_all_fsub_chats(self) -> dict:
        """Retrieve both fsub chats in a structured format."""
        chat1 = await self.get_fsub_chat1() or {}
        chat2 = await self.get_fsub_chat2() or {}

        return {
            "fsub_chat1": {
                "chat_id": chat1.get("chat_id"),
                "invite_link": chat1.get("invite_link"),
                "switch_time": chat1.get("switch_time")
            },
            "fsub_chat2": {
                "chat_id": chat2.get("chat_id"),
                "invite_link": chat2.get("invite_link"),
                "switch_time": chat2.get("switch_time")
            }
        }


# Initialize Database
db = Database(DATABASE_URI, DATABASE_NAME)
