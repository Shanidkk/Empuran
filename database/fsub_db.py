import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_NAME, DATABASE_URI

logging.basicConfig(level=logging.INFO)

class Database:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client["JoinReqManager"]

        # Collections
        self.fsub_chat1 = self.db["fsub_chat1"]
        self.fsub_chat2 = self.db["fsub_chat2"]
        self.req = self.db["user_requests"]  # Collection for storing user requests

    # ================================
    # ✅ FSUB CHAT MANAGEMENT FUNCTIONS
    # ================================

    async def add_fsub_chat1(self, chat_id: int, invite_link: str, mode: str = "req") -> bool:
        """Add or update fsub chat 1 details with mode."""
        try:
            await self.fsub_chat1.delete_many({})
            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            await self.fsub_chat1.insert_one({
                "chat_id": chat_id,
                "invite_link": invite_link,
                "switch_time": switch_time,
                "mode": mode  # NEW: Store mode
            })
            return True
        except Exception as e:
            logging.error(f"Error adding fsub chat 1: {e}")
            return False

    async def add_fsub_chat2(self, chat_id: int, invite_link: str, mode: str = "normal") -> bool:
        """Add or update fsub chat 2 details with mode."""
        try:
            await self.fsub_chat2.delete_many({})
            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            await self.fsub_chat2.insert_one({
                "chat_id": chat_id,
                "invite_link": invite_link,
                "switch_time": switch_time,
                "mode": mode  # NEW: Store mode
            })
            return True
        except Exception as e:
            logging.error(f"Error adding fsub chat 2: {e}")
            return False

    async def get_fsub_chat1(self) -> dict | None:
        """Retrieve fsub chat 1 details, including mode."""
        return await self.fsub_chat1.find_one({})

    async def get_fsub_chat2(self) -> dict | None:
        """Retrieve fsub chat 2 details, including mode."""
        return await self.fsub_chat2.find_one({})

    async def delete_fsub_chat1(self) -> bool:
        """Delete fsub chat 1 data."""
        try:
            result = await self.fsub_chat1.delete_many({})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting fsub chat 1: {e}")
            return False

    async def delete_fsub_chat2(self) -> bool:
        """Delete fsub chat 2 data."""
        try:
            result = await self.fsub_chat2.delete_many({})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting fsub chat 2: {e}")
            return False
            
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

    async def get_all_fsub_chats(self) -> dict:
        """Retrieve both fsub chats in a structured format, including mode."""
        chat1 = await self.get_fsub_chat1() or {}
        chat2 = await self.get_fsub_chat2() or {}

        return {
            "fsub_chat1": {
                "chat_id": chat1.get("chat_id"),
                "invite_link": chat1.get("invite_link"),
                "switch_time": chat1.get("switch_time"),
                "mode": chat1.get("mode", "normal")  # NEW: Include mode
            },
            "fsub_chat2": {
                "chat_id": chat2.get("chat_id"),
                "invite_link": chat2.get("invite_link"),
                "switch_time": chat2.get("switch_time"),
                "mode": chat2.get("mode", "normal")  # NEW: Include mode
            }
        }

    # ================================
    # ✅ USER REQUEST MANAGEMENT FUNCTIONS
    # ================================

    async def add_req(self, user_id: int, chat_id: int) -> bool:
        """Add a request entry for a user."""
        try:
            await self.req.update_one(
                {"user_id": user_id},
                {"$push": {"requests": {"chat_id": chat_id}}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error adding request for user {user_id}: {e}")
            return False

    async def get_req(self, user_id: int, chat_id: int) -> dict | None:
        """Retrieve a specific request made by a user for a chat."""
        try:
            user = await self.req.find_one({"user_id": user_id})
            if user:
                return next((r for r in user["requests"] if r["chat_id"] == chat_id), None)
            return None
        except Exception as e:
            logging.error(f"Error retrieving request for user {user_id}: {e}")
            return None

    async def delete_req(self, user_id: int, chat_id: int) -> bool:
        """Delete a specific request from a user for a chat."""
        try:
            result = await self.req.update_one(
                {"user_id": user_id},
                {"$pull": {"requests": {"chat_id": chat_id}}}
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error deleting request for user {user_id}: {e}")
            return False

    async def delete_all_reqs(self, chat_id: int = None) -> bool:
        """Delete all requests for a specific chat or all requests globally."""
        try:
            if chat_id:
                await self.req.update_many({}, {"$pull": {"requests": {"chat_id": chat_id}}})
            else:
                await self.req.delete_many({})
            return True
        except Exception as e:
            logging.error(f"Error deleting requests: {e}")
            return False

    async def get_all_reqs_count(self, chat_id: int = None) -> int:
        """Get the count of all requests for a specific chat or globally."""
        try:
            if chat_id:
                return await self.req.count_documents({"requests.chat_id": chat_id})
            return await self.req.count_documents({})
        except Exception as e:
            logging.error(f"Error counting requests: {e}")
            return 0

    # ================================
    # ✅ NEW: FSUB MODE MANAGEMENT FUNCTIONS
    # ================================

    async def get_fsub_mode1(self) -> dict | None:
        """Retrieve the FSub mode for chat 1."""
        chat = await self.get_fsub_chat1()
        return {"mode": chat.get("mode", "normal")} if chat else None

    async def get_fsub_mode2(self) -> dict | None:
        """Retrieve the FSub mode for chat 2."""
        chat = await self.get_fsub_chat2()
        return {"mode": chat.get("mode", "normal")} if chat else None

    async def add_fsub_mode1(self, chat_id: int, mode: str) -> bool:
        """Update the FSub mode for chat 1."""
        try:
            result = await self.fsub_chat1.update_one(
                {"chat_id": chat_id},
                {"$set": {"mode": mode}},
                upsert=True
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating fsub mode for chat 1: {e}")
            return False

    async def add_fsub_mode2(self, chat_id: int, mode: str) -> bool:
        """Update the FSub mode for chat 2."""
        try:
            result = await self.fsub_chat2.update_one(
                {"chat_id": chat_id},
                {"$set": {"mode": mode}},
                upsert=True
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating fsub mode for chat 2: {e}")
            return False


# Initialize Database
db = Database(DATABASE_URI, DATABASE_NAME)
