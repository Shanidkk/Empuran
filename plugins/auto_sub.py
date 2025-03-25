from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from utils import temp
from info import ADMINS, DATABASE_URI
from database.fsub_db import db
import asyncio
from datetime import datetime

mongo_client = AsyncIOMotorClient(DATABASE_URI)
db2 = mongo_client["Kuttans"]

request_collection_1 = db2["requests_channel_1"]
request_collection_2 = db2["requests_channel_2"]
pending_collection_1 = db2["pending_channels_1"]
pending_collection_2 = db2["pending_channels_2"]
settings_collection = db2["channel_settings"]

async def add_request(chat_id: int, user_id: int, collection):
    existing_request = await collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if not existing_request:
        await collection.insert_one({"chat_id": chat_id, "user_id": user_id})
        await collection.update_one(
            {"chat_id": chat_id},
            {"$inc": {"total_requests": 1}},
            upsert=True
        )
        
async def get_total_requests_count(chat_id, coll):
    if coll == 1:
        collection = request_collection_1  # Corrected Collection
    else:
        collection = request_collection_2  # Corrected Collection
    chat_data = await collection.find_one({"chat_id": chat_id})
    return chat_data.get("total_requests", 0) if chat_data else 0
    
async def get_total_requests(chat_id: int, collection):
    chat_data = await collection.find_one({"chat_id": chat_id})
    return chat_data.get("total_requests", 0) if chat_data else 0

async def get_next_pending_channel(pending_collection):
    next_channel = await pending_collection.find_one({}, sort=[('_id', 1)])
    if next_channel:
        return next_channel["chat_id"]
    return None

async def remove_pending_channel(chat_id: int, pending_collection):
    await pending_collection.delete_one({"chat_id": chat_id})

async def get_request_limit():
    limit_data = await settings_collection.find_one({"setting": "request_limit"})
    return limit_data.get("value", 10000) if limit_data else 10000

async def set_request_limit(new_limit):
    await settings_collection.update_one(
        {"setting": "request_limit"},
        {"$set": {"value": new_limit}},
        upsert=True
    )

async def notify_admin_channel(bot, fsub_mode, next_channel, link):
    text = (f"Force Sub mode {fsub_mode} has switched channels.\n"
            f"New Channel ID: {next_channel}\n"
            f"Invite Link: {link}")
    await bot.send_message(chat_id=1957296068, text=text)

async def complete_switching1(chat, bot):
    """Switch and update fsub chat 1 details in the database."""
    try:
        link = (await bot.create_chat_invite_link(
            chat_id=int(chat), 
            creates_join_request=temp.REQ_FSUB_MODE1
        )).invite_link
    except Exception as e:
        logging.error(f"Error creating invite link for chat {chat}: {e}")
        link = "None"
    # Store the updated chat details in the database
    await db.add_fsub_chat1(chat, link)
    # Update bot and temp variables
    bot.req_link1 = link
    temp.REQ_CHANNEL1 = chat
    # Notify admin about the update
    await notify_admin_channel(bot, 1, chat, link)


async def complete_switching2(chat, bot):
    """Switch and update fsub chat 2 details in the database."""
    try:
        link = (await bot.create_chat_invite_link(
            chat_id=int(chat), 
            creates_join_request=temp.REQ_FSUB_MODE2
        )).invite_link
    except Exception as e:
        logging.error(f"Error creating invite link for chat {chat}: {e}")
        link = "None"
    # Store the updated chat details in the database
    await db.add_fsub_chat2(chat, link)
    bot.req_link2 = link
    temp.REQ_CHANNEL2 = chat
    # Notify admin about the update
    await notify_admin_channel(bot, 2, chat, link)
    

async def switch_channel(chat_id, fsub_mode, pending_collection, collection, bot):
    if fsub_mode == 0:
        return
    async with asyncio.Lock():  # Prevent race conditions
        next_channel = await get_next_pending_channel(pending_collection)
        if next_channel:
            await remove_pending_channel(next_channel, pending_collection)
            
            # Clear all user requests from the current channel before switching
            await collection.delete_many({"chat_id": chat_id})  # Clears user IDs

            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await collection.update_one(
                {"chat_id": next_channel},
                {"$set": {"switch_time": switch_time}},
                upsert=True
            )
            if fsub_mode == 1:
                await complete_switching1(next_channel, bot)
            else:
                await complete_switching2(next_channel, bot)
            print(f"Switched to new channel {next_channel} for Force Sub mode {fsub_mode}")
        else:
            print(f"No more pending channels to switch to for mode {fsub_mode}")


@Client.on_chat_join_request()
async def join_reqs(b, join_req: ChatJoinRequest):
    user_id = join_req.from_user.id
    chat_id = join_req.chat.id
    mode = 0
    request_limit = await get_request_limit()

    if chat_id == temp.REQ_CHANNEL1:
        mode = 1
        request_collection = request_collection_1
        pending_collection = pending_collection_1
        if user_id in temp.DOUBLE_MSGS:
            alert_msg = await b.send_message(
                chat_id=user_id,
                text="**⚠️ ഇനി Update Channel 2 ൽ കൂടെ ജോയിൻ ആയാൽ സിനിമ കിട്ടും.\n\n⚠️ You need to join my Update Channel 2 to get the file.**"
            )
            temp.ALERT_MESSAGES[user_id] = alert_msg.id  # Saves each chat's message
    elif chat_id == temp.REQ_CHANNEL2:
        mode = 2
        request_collection = request_collection_2
        pending_collection = pending_collection_2
        if user_id in temp.DOUBLE_MSGS:
            alert_msg = await b.send_message(
                chat_id=user_id,
                text="**⚠️ ഇനി Update Channel 1 ൽ കൂടെ ജോയിൻ ആയാൽ സിനിമ കിട്ടും.\n\n⚠️ You need to join my Update Channel 1 to get the file.**"
            )
            temp.ALERT_MESSAGES[user_id] = alert_msg.id  # Saves each chat's message
    else:
        return  # Ignore requests from other chats

    if join_req.invite_link.creator.id == b.me.id:
        await db.add_req(user_id, chat_id)  # Fixed add_req call
        await add_request(chat_id, user_id, request_collection)
    total_requests = await get_total_requests_count(chat_id, mode)  # Fixing request counting
    await b.send_message(chat_id=1957296068, text=f" Total = {total_requests}\n Limit = {request_limit}")
    if total_requests >= request_limit:
        await switch_channel(chat_id, mode, pending_collection, request_collection, b)


@Client.on_message(filters.command('set_limit') & filters.user(ADMINS))
async def set_request_limit_command(client, message):
    try:
        new_limit = int(message.text.split()[1])
        await set_request_limit(new_limit)
        await message.reply(f"Request limit updated to {new_limit}.")
    except Exception as e:
        await message.reply("Failed to update request limit. Make sure you provide a valid number.")

@Client.on_message(filters.command('pending') & filters.private & filters.user(ADMINS))
async def pending_channels(client, message):
    channels = await pending_collection_1.find({}).to_list(length=None)
    
    buttons = [
        [InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_1#{ch['chat_id']}")]
        for ch in channels
    ]
    
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_1")])
    
    if not channels:
        await message.reply(text="No pending channels.", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply(text="Pending Channels:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command('pending2') & filters.private & filters.user(ADMINS))
async def pending_channels_2(client, message):
    channels = await pending_collection_2.find({}).to_list(length=None)
    
    buttons = [
        [InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_2#{ch['chat_id']}")]
        for ch in channels
    ]
    
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_2")])
    
    if not channels:
        await message.reply(text="No pending channels.", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply(text="Pending Channels:", reply_markup=InlineKeyboardMarkup(buttons))

# Add more logic to handle other situations...


async def show_channel_details_1(client: Client, query):
    _, chat_id = query.data.split("#")
    print(chat_id)
    channel = await pending_collection_1.find_one({"chat_id": int(chat_id)})

    if channel:
        buttons = [[InlineKeyboardButton("❌ Remove Channel", callback_data=f"remove_channel_1#{chat_id}")]]
        await query.message.edit_text(f"Channel Name: {channel['name']}\nChannel ID: {chat_id}",
                                      reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.message.reply("Channel not found.")

# Handle showing channel details and options for the second Force Sub mode

async def show_channel_details_2(client: Client, query):
    _, chat_id = query.data.split("#")
    print(chat_id)
    channel = await pending_collection_2.find_one({"chat_id": int(chat_id)})

    if channel:
        buttons = [[InlineKeyboardButton("❌ Remove Channel", callback_data=f"remove_channel_2#{chat_id}")]]
        await query.message.edit_text(f"Channel Name: {channel['name']}\nChannel ID: {chat_id}",
                                      reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.message.reply("Channel not found.")

# Handle removing a channel from the pending list (first Force Sub mode)

async def remove_channel_1(client: Client, query):
    _, chat_id = query.data.split("#")
    chat_id = int(chat_id)
    await pending_collection_1.delete_one({"chat_id": chat_id})
    await query.message.edit_text(f"Channel {chat_id} has been removed from the pending list.")

# Handle removing a channel from the pending list (second Force Sub mode)
async def remove_channel_2(client: Client, query):
    _, chat_id = query.data.split("#")
    chat_id = int(chat_id)
    await pending_collection_2.delete_one({"chat_id": chat_id})
    await query.message.edit_text(f"Channel {chat_id} has been removed from the pending list.")
    
@Client.on_callback_query(filters.regex(r"^add_channel_1$"))
async def add_channel_1(client: Client, query):
    await query.message.reply("Forward a message from the channel you want to add.")
    # Listen for forwarded message with timeout and error handling
    try:
        forwarded_message = await asyncio.wait_for(client.listen(query.message.chat.id), timeout=60)
    except asyncio.TimeoutError:
        await query.message.reply("Timeout! Please try forwarding the message again.")
        return

    if not forwarded_message.forward_from_chat:
        await query.message.reply("This message doesn't seem to be from a channel. Please forward a message from the channel you want to add.")
        return
    
    chat_id = int(forwarded_message.forward_from_chat.id)
    chat_title = forwarded_message.forward_from_chat.title
    
    # Check if bot is an admin in the forwarded channel using try-except
    try:
        await client.get_chat(int(chat_id))     
    except Exception as e:
        await forwarded_message.reply(f"Failed to verify bot permissions in channel '{chat_title}'. {e}    Ensure the bot is an admin and try again.")
        return
    
    # Check for duplicates
    existing_channel = await pending_collection_1.find_one({"chat_id": chat_id})
    if existing_channel:
        await forwarded_message.reply(f"Channel '{chat_title}' is already in the pending list.")
        return
    
    # Add the channel to pending list
    await pending_collection_1.insert_one({"chat_id": chat_id, "name": chat_title})
    await forwarded_message.reply(f"Channel '{chat_title}' has been added.")

@Client.on_callback_query(filters.regex(r"^add_channel_2$"))
async def add_channel_2(client: Client, query):
    await query.message.reply("Forward a message from the channel you want to add for the second FSub.")
    # Listen for forwarded message with timeout and error handling
    try:
        forwarded_message = await asyncio.wait_for(client.listen(query.message.chat.id), timeout=60)
    except asyncio.TimeoutError:
        await query.message.reply("Timeout! Please try forwarding the message again.")
        return
    if not forwarded_message.forward_from_chat:
        await query.message.reply("This message doesn't seem to be from a channel. Please forward a message from the channel you want to add.")
        return
    chat_id = int(forwarded_message.forward_from_chat.id)
    chat_title = forwarded_message.forward_from_chat.title
    # Check if bot is an admin in the forwarded channel using try-except
    try:
        await client.get_chat(int(chat_id))     
    except Exception as e:
        await forwarded_message.reply(f"Failed to verify bot permissions in channel '{chat_title}'. {e}    Ensure the bot is an admin and try again.")
        return
    # Check for duplicates
    existing_channel = await pending_collection_2.find_one({"chat_id": chat_id})
    if existing_channel:
        await forwarded_message.reply(f"Channel '{chat_title}' is already in the pending list.")
        return
    # Add the channel to pending list
    await pending_collection_2.insert_one({"chat_id": chat_id, "name": chat_title})
    await forwarded_message.reply(f"Second FSub Channel '{chat_title}' has been added.")
