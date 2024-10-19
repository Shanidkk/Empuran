from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest
from motor.motor_asyncio import AsyncIOMotorClient
import pyromod.listen  # Import pyromod's listen to handle incoming messages
from utils import temp

# MongoDB setup
MONGO_URI = "your_mongo_db_uri_here"
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["join_request_db"]
channel_collection = db["channels"]
pending_collection = db["pending_channels"]
request_collection = db["requests"]

# Add new channel to the pending list
async def add_channel_to_pending(chat_id: int, chat_name: str):
    await channel_collection.insert_one({"chat_id": chat_id, "name": chat_name})
    print(f"Channel {chat_name} added to pending list")

# Remove a channel from the pending list
async def remove_channel_from_pending(chat_id: int):
    await channel_collection.delete_one({"chat_id": chat_id})
    print(f"Channel with ID {chat_id} removed from pending list")

# Fetch the pending channels
async def get_pending_channels():
    return await channel_collection.find({}).to_list(length=None)

# Add and count requests for each channel
async def add_request(chat_id: int, user_id: int):
    existing_request = await request_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    
    if not existing_request:
        # Add new request and increment count
        await request_collection.insert_one({"chat_id": chat_id, "user_id": user_id})
        await request_collection.update_one(
            {"chat_id": chat_id},
            {"$inc": {"total_requests": 1}},
            upsert=True
        )
        print(f"Request from user {user_id} added for chat {chat_id}")

# Get total requests for a specific chat
async def get_total_requests(chat_id: int):
    chat_data = await request_collection.find_one({"chat_id": chat_id})
    return chat_data.get("total_requests", 0) if chat_data else 0

# Handle switching when a channel reaches 10k subscribers
async def switch_channel(chat_id, fsub_channel, fsub_mode):
    await pending_collection.insert_one({"chat_id": chat_id, "fsub_channel": fsub_channel})
    print(f"Switched to new channel {chat_id}")

# Handle pending channels for first force subscription
@Client.on_message(filters.command('pending') & filters.private)
async def pending_channels(client, message):
    channels = await get_pending_channels()  # Fetch pending channels from the DB
    
    if not channels:
        text = "No pending channels."
        await message.reply(text=text)
        return

    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_{ch['chat_id']}")])
    
    # Add button for adding a new channel
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(text="Pending Channels:", reply_markup=reply_markup)

# Handle pending channels for second force subscription
@Client.on_message(filters.command('pending2') & filters.private)
async def pending_channels_2(client, message):
    channels = await get_pending_channels()  # Fetch pending channels for second FSub
    
    if not channels:
        text = "No pending channels."
        await message.reply(text=text)
        return

    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_{ch['chat_id']}")])
    
    # Add button for adding a new channel
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_2")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(text="Pending Channels for Second FSub:", reply_markup=reply_markup)

# Handle button click for showing channel remove option
@Client.on_callback_query(filters.regex(r"^show_channel_(\d+)$"))
async def show_channel_options(client: Client, query: CallbackQuery):
    chat_id = int(query.data.split("_")[-1])
    
    # Show option to remove the channel
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❌ Remove Channel", callback_data=f"remove_channel_{chat_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="pending_channels")]
        ]
    )
    
    await query.message.edit_text(f"Channel ID: {chat_id}\nWhat would you like to do?", reply_markup=reply_markup)

# Handle removing channel from the pending list
@Client.on_callback_query(filters.regex(r"^remove_channel_(\d+)$"))
async def remove_channel_handler(client: Client, query: CallbackQuery):
    chat_id = int(query.data.split("_")[-1])
    
    await remove_channel_from_pending(chat_id)
    await query.message.edit_text(f"Channel with ID {chat_id} has been removed.")
    
    # Optionally show the pending channels again
    await pending_channels(client, query.message)

# Handle "Add New Channel" button click
@Client.on_callback_query(filters.regex(r"^add_channel$"))
async def add_channel_button_handler(client: Client, query: CallbackQuery):
    await query.message.reply("Please forward a message from the channel you want to add.")
    
    # Wait for the forwarded message
    forwarded_message = await client.listen(query.message.chat.id, filters.forwarded)
    
    chat_id = forwarded_message.forward_from_chat.id
    chat_title = forwarded_message.forward_from_chat.title
    
    await add_channel_to_pending(chat_id, chat_title)
    await forwarded_message.reply(f"Channel '{chat_title}' has been added with ID: {chat_id}")

# Handle "Add New Channel" for Second FSub button click
@Client.on_callback_query(filters.regex(r"^add_channel_2$"))
async def add_channel_2_button_handler(client: Client, query: CallbackQuery):
    await query.message.reply("Please forward a message from the second FSub channel you want to add.")
    
    # Wait for the forwarded message
    forwarded_message = await client.listen(query.message.chat.id, filters.forwarded)
    
    chat_id = forwarded_message.forward_from_chat.id
    chat_title = forwarded_message.forward_from_chat.title
    
    await add_channel_to_pending(chat_id, chat_title)
    await forwarded_message.reply(f"Second FSub Channel '{chat_title}' has been added with ID: {chat_id}")

# Handle join requests and switch FSub channel when needed
@Client.on_chat_join_request()
async def join_reqs(b, join_req: ChatJoinRequest):
    user_id = join_req.from_user.id
    chat_id = join_req.chat.id
    mode = 0
    # Add request and count for channel 1
    if chat_id == temp.REQ_CHANNEL1:
        mode = 1
        if join_req.invite_link.creator.id == b.me.id:
            await db.add_req_one(user_id)
            await add_request(chat_id, user_id)
    
    # Add request and count for channel 2
    if chat_id == temp.REQ_CHANNEL2:
        mode = 2
        if join_req.invite_link.creator.id == b.me.id:
            await db.add_req_two(user_id)
            await add_request(chat_id, user_id)
    total_requests = await get_total_requests(chat_id)
    if total_requests >= 10000:
        await switch_channel(chat_id, temp.REQ_CHANNEL2, fsub_mode=mode)
