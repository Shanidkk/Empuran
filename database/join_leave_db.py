import motor.motor_asyncio
from info import DATABASE_NAME, DATABASE_URI


class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.invite_stats = self.db.invite_stats  # For tracking joins/leaves
        self.user_invites = self.db.user_invites  # for storing user invite links

    async def init_indexes(self):
        """Ensure indexes for optimized lookups."""
        await self.invite_stats.create_index([("chat_id", 1), ("user_id", 1)])
        await self.user_invites.create_index([("chat_id", 1), ("user_id", 1)])

    async def update_stats(self, chat_id: int, user_id: int, action: str):
        """Update join/leave stats only if the user joined via our invite link."""
        if action == "join":
            await self.invite_stats.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$inc": {"joined": 1}},
                upsert=True,
            )
        elif action == "leave":
            await self.invite_stats.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$inc": {"left": 1}},
                upsert=True,
            )

    async def store_user_invite(self, user_id: int, chat_id: int, invite_link: str):
        """Store which invite link a user used to join."""
        await self.user_invites.update_one(
            {"user_id": user_id, "chat_id": chat_id},
            {"$set": {"invite_link": invite_link}},
            upsert=True,
        )

    async def get_user_invite(self, user_id: int, chat_id: int):
        """Retrieve the invite link a user joined through."""
        data = await self.user_invites.find_one(
            {"user_id": user_id, "chat_id": chat_id}
        )
        return data.get("invite_link") if data else None

    async def get_stats(self, chat_id: int):
        """Retrieve join/leave statistics for a chat."""
        data = await self.invite_stats.aggregate(
            [
                {"$match": {"chat_id": chat_id}},
                {
                    "$group": {
                        "_id": None,
                        "joined": {"$sum": "$joined"},
                        "left": {"$sum": "$left"},
                    }
                },
            ]
        ).to_list(1)

        return data[0] if data else {"joined": 0, "left": 0}


db = Database(DATABASE_URI, DATABASE_NAME)
