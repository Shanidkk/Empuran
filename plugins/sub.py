from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, Message
from info import ADMINS
from database.users_chats_db import db
from utils import temp
from motor.motor_asyncio import AsyncIOMotorClient

# Replace with your MongoDB URI
MONGO_URI = "your_mongo_db_uri_here"
client = AsyncIOMotorClient(MONGO_URI)
db = client["join_request_db"]
request_collection = db["requests"]

# Function to add and count requests
async def add_request(chat_id: int, user_id: int):
    # Check if user already exists in the current chat's request list
    existing_request = await request_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    
    if not existing_request:
        # Add new request and update the total count
        await request_collection.insert_one({"chat_id": chat_id, "user_id": user_id})
        
        # Increment the request count for the chat
        await request_collection.update_one(
            {"chat_id": chat_id},
            {"$inc": {"total_requests": 1}},
            upsert=True
        )
        
        print(f"Request from user {user_id} added for chat {chat_id}")
    else:
        print(f"Duplicate request from user {user_id} ignored for chat {chat_id}")

# Get total requests for a specific chat
async def get_total_requests(chat_id: int):
    chat_data = await request_collection.find_one({"chat_id": chat_id})
    if chat_data:
        return chat_data.get("total_requests", 0)
    else:
        return 0


@Client.on_chat_join_request()
async def join_reqs(b, join_req: ChatJoinRequest):
   # print("join req found")
    user_id = join_req.from_user.id
    try:
        if join_req.chat.id == temp.REQ_CHANNEL1:
            if join_req.invite_link.creator.id == b.me.id:
                await db.add_req_one(user_id)
        if join_req.chat.id == temp.REQ_CHANNEL2:
            if join_req.invite_link.creator.id == b.me.id:
                await db.add_req_two(user_id)
    except Exception as e:
        print(f"Error adding join request: {e}")

