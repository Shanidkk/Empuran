from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
import pyromod.listen
from utils import temp

# MongoDB setup
MONGO_URI = "your_mongo_db_uri_here"
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["join_request_db"]

# Collections for requests and pending channels
request_collection_1 = db["requests_channel_1"]
request_collection_2 = db["requests_channel_2"]
pending_collection_1 = db["pending_channels_1"]
pending_collection_2 = db["pending_channels_2"]

# Function to add and count requests for a channel
async def add_request(chat_id: int, user_id: int, collection):
    existing_request = await collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if not existing_request:
        await collection.insert_one({"chat_id": chat_id, "user_id": user_id})
        await collection.update_one(
            {"chat_id": chat_id},
            {"$inc": {"total_requests": 1}},
            upsert=True
        )

# Get total requests for a specific chat
async def get_total_requests(chat_id: int, collection):
    chat_data = await collection.find_one({"chat_id": chat_id})
    return chat_data.get("total_requests", 0) if chat_data else 0

# Fetch the next pending channel
async def get_next_pending_channel(pending_collection):
    next_channel = await pending_collection.find_one({}, sort=[('_id', 1)])
    if next_channel:
        return next_channel["chat_id"]
    return None

# Remove the channel from the pending list after switching
async def remove_pending_channel(chat_id: int, pending_collection):
    await pending_collection.delete_one({"chat_id": chat_id})

# Handle switching when a channel reaches 10k subscribers
async def switch_channel(chat_id, fsub_mode, pending_collection, collection):
    if fsub_mode == 0:
        return 
    next_channel = await get_next_pending_channel(pending_collection)
    if next_channel:
        await remove_pending_channel(next_channel, pending_collection)
        if fsub_mode == 1:
            temp.REQ_CHANNEL1 = next_channel
        else:
            temp.REQ_CHANNEL2 = next_channel
        print(f"Switched to new channel {next_channel} for Force Sub mode {fsub_mode}")
    else:
        print(f"No more pending channels to switch to for mode {fsub_mode}")

# Handle join requests for both force subscriptions
@Client.on_chat_join_request()
async def join_reqs(b, join_req: ChatJoinRequest):
    user_id = join_req.from_user.id
    chat_id = join_req.chat.id
    mode = 0

    # Channel 1 Force Sub logic
    if chat_id == temp.REQ_CHANNEL1:
        mode = 1
        if join_req.invite_link.creator.id == b.me.id:
            await add_request(chat_id, user_id, request_collection_1)
        total_requests = await get_total_requests(chat_id, request_collection_1)
    
    # Channel 2 Force Sub logic
    elif chat_id == temp.REQ_CHANNEL2:
        mode = 2
        if join_req.invite_link.creator.id == b.me.id:
            await add_request(chat_id, user_id, request_collection_2)
        total_requests = await get_total_requests(chat_id, request_collection_2)

    # Check for switching when 10k requests are reached
    if total_requests >= 10000:
        if mode == 1:
            await switch_channel(chat_id, mode, pending_collection_1, request_collection_1)
        elif mode == 2:
            await switch_channel(chat_id, mode, pending_collection_2, request_collection_2)

# Handle pending channels list for first force subscription
@Client.on_message(filters.command('pending') & filters.private)
async def pending_channels(client, message):
    channels = await pending_collection_1.find({}).to_list(length=None)
    
    if not channels:
        text = "No pending channels."
        await message.reply(text=text)
        return

    buttons = [
        [InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_{ch['chat_id']}")]
        for ch in channels
    ]
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_1")])
    await message.reply(text="Pending Channels:", reply_markup=InlineKeyboardMarkup(buttons))

# Handle pending channels list for second force subscription
@Client.on_message(filters.command('pending2') & filters.private)
async def pending_channels_2(client, message):
    channels = await pending_collection_2.find({}).to_list(length=None)
    
    if not channels:
        text = "No pending channels."
        await message.reply(text=text)
        return

    buttons = [
        [InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_{ch['chat_id']}")]
        for ch in channels
    ]
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_2")])
    await message.reply(text="Pending Channels for Second FSub:", reply_markup=InlineKeyboardMarkup(buttons))

# Handle adding a new channel for first FSub
@Client.on_callback_query(filters.regex(r"^add_channel_1$"))
async def add_channel_1(client: Client, query):
    await query.message.reply("Forward a message from the channel you want to add.")
    forwarded_message = await client.listen(query.message.chat.id, filters.forwarded)
    
    chat_id = forwarded_message.forward_from_chat.id
    chat_title = forwarded_message.forward_from_chat.title
    await pending_collection_1.insert_one({"chat_id": chat_id, "name": chat_title})
    await forwarded_message.reply(f"Channel '{chat_title}' has been added.")

# Handle adding a new channel for second FSub
@Client.on_callback_query(filters.regex(r"^add_channel_2$"))
async def add_channel_2(client: Client, query):
    await query.message.reply("Forward a message from the channel you want to add for the second FSub.")
    forwarded_message = await client.listen(query.message.chat.id, filters.forwarded)
    
    chat_id = forwarded_message.forward_from_chat.id
    chat_title = forwarded_message.forward_from_chat.title
    await pending_collection_2.insert_one({"chat_id": chat_id, "name": chat_title})
    await forwarded_message.reply(f"Second FSub Channel '{chat_title}' has been added.")
