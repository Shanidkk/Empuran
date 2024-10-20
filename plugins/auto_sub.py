from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from utils import temp
from info import ADMINS, DATABASE_URI
from database.users_chats_db import db
import asyncio

mongo_client = AsyncIOMotorClient(DATABASE_URI)
db = mongo_client["join_request_db"]

request_collection_1 = db["requests_channel_1"]
request_collection_2 = db["requests_channel_2"]
pending_collection_1 = db["pending_channels_1"]
pending_collection_2 = db["pending_channels_2"]
settings_collection = db["channel_settings"]

async def add_request(chat_id: int, user_id: int, collection):
    existing_request = await collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if not existing_request:
        await collection.insert_one({"chat_id": chat_id, "user_id": user_id})
        await collection.update_one(
            {"chat_id": chat_id},
            {"$inc": {"total_requests": 1}},
            upsert=True
        )

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
    for id in ADMINS:
        await bot.send_message(chat_id=id, text=text)

async def complete_switching1(chat, bot):
    await db.add_fsub_chat(chat)
    try:
        link = (await bot.create_chat_invite_link(chat_id=int(chat), creates_join_request=temp.REQ_FSUB_MODE1)).invite_link
    except Exception as e:
        print(e)
        link = "None"
    bot.req_link1 = link
    temp.REQ_CHANNEL1 = chat
    await notify_admin_channel(bot, 1, chat, link)

async def complete_switching2(chat, bot):
    await db.add_fsub_chat2(chat)
    try:
        link = (await bot.create_chat_invite_link(chat_id=int(chat), creates_join_request=temp.REQ_FSUB_MODE2)).invite_link
    except Exception as e:
        print(e)
        link = "None"
    bot.req_link2 = link
    temp.REQ_CHANNEL2 = chat
    await notify_admin_channel(bot, 2, chat, link)

async def switch_channel(chat_id, fsub_mode, pending_collection, collection, bot):
    if fsub_mode == 0:
        return 
    next_channel = await get_next_pending_channel(pending_collection)
    if next_channel:
        await remove_pending_channel(next_channel, pending_collection)
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
        if join_req.invite_link.creator.id == b.me.id:
            await db.add_req_one(user_id)
            await add_request(chat_id, user_id, request_collection_1)
        total_requests = await get_total_requests(chat_id, request_collection_1)
    
    elif chat_id == temp.REQ_CHANNEL2:
        mode = 2
        if join_req.invite_link.creator.id == b.me.id:
            await db.add_req_two(user_id)
            await add_request(chat_id, user_id, request_collection_2)
        total_requests = await get_total_requests(chat_id, request_collection_2)

    if total_requests >= request_limit:
        if mode == 1:
            await switch_channel(chat_id, mode, pending_collection_1, request_collection_1, b)
        elif mode == 2:
            await switch_channel(chat_id, mode, pending_collection_2, request_collection_2, b)

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
        [InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_{ch['chat_id']}")]
        for ch in channels
    ]
    
    # Add the "Add New Channel" button even if there are no pending channels
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_1")])
    
    # Check if there are no channels and display a message
    if not channels:
        await message.reply(text="No pending channels.", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply(text="Pending Channels:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command('pending2') & filters.private & filters.user(ADMINS))
async def pending_channels_2(client, message):
    channels = await pending_collection_2.find({}).to_list(length=None)

    buttons = [
        [InlineKeyboardButton(f"{ch['name']}", callback_data=f"show_channel_{ch['chat_id']}")]
        for ch in channels
    ]
    
    # Add the "Add New Channel" button even if there are no pending channels
    buttons.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel_2")])
    
    # Check if there are no channels and display a message
    if not channels:
        await message.reply(text="No pending channels.", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply(text="Pending Channels for Second FSub:", reply_markup=InlineKeyboardMarkup(buttons))
        

@Client.on_callback_query(filters.regex(r"^add_channel_1$"))
async def add_channel_1(client: Client, query):
    await query.message.reply("Forward a message from the channel you want to add.")
    
    # Listen for forwarded message with timeout and error handling
    try:
        forwarded_message = await asyncio.wait_for(client.listen(query.message.chat.id, filters.forwarded), timeout=60)
    except asyncio.TimeoutError:
        await query.message.reply("Timeout! Please try forwarding the message again.")
        return

    if not forwarded_message.forward_from_chat:
        await query.message.reply("This message doesn't seem to be from a channel. Please forward a message from the channel you want to add.")
        return
    
    chat_id = forwarded_message.forward_from_chat.id
    chat_title = forwarded_message.forward_from_chat.title
    
    # Check if bot is an admin in the forwarded channel using try-except
    try:
        await client.get_chat(chat_id)
        chat_member = await client.get_chat_member(chat_id, client.me.id)
        
        if chat_member.status != "administrator":
            await forwarded_message.reply(f"The bot is not an admin in the channel '{chat_title}'. Please make the bot an admin and try again.")
            return
    except (ChatAdminRequired, BadRequest):
        await forwarded_message.reply(f"Failed to verify bot permissions in channel '{chat_title}'. Ensure the bot is an admin and try again.")
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
        forwarded_message = await asyncio.wait_for(client.listen(query.message.chat.id, filters.forwarded), timeout=60)
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
        await client.get_chat(chat_id)     
    except (ChatAdminRequired, BadRequest):
        await forwarded_message.reply(f"Failed to verify bot permissions in channel '{chat_title}'. Ensure the bot is an admin and try again.")
        return
    # Check for duplicates
    existing_channel = await pending_collection_2.find_one({"chat_id": chat_id})
    if existing_channel:
        await forwarded_message.reply(f"Channel '{chat_title}' is already in the pending list.")
        return
    # Add the channel to pending list
    await pending_collection_2.insert_one({"chat_id": chat_id, "name": chat_title})
    await forwarded_message.reply(f"Second FSub Channel '{chat_title}' has been added.")


@Client.on_callback_query(filters.regex(r"^show_channel_(\d+)$"))
async def show_channel_details(client: Client, query):
    chat_id = int(query.data.split("_")[2])
    channel = await pending_collection_1.find_one({"chat_id": chat_id})

    if channel:
        buttons = [[InlineKeyboardButton("❌ Remove Channel", callback_data=f"remove_channel_{chat_id}_1")]]
        await query.message.reply(f"Channel Name: {channel['name']}\nChannel ID: {chat_id}",
                                  reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.message.reply("Channel not found.")

@Client.on_callback_query(filters.regex(r"^remove_channel_(\d+)_1$"))
async def remove_channel_1(client: Client, query):
    chat_id = int(query.data.split("_")[2])
    await pending_collection_1.delete_one({"chat_id": chat_id})
    await query.message.reply(f"Channel {chat_id} has been removed from the pending list.")

@Client.on_callback_query(filters.regex(r"^remove_channel_(\d+)_2$"))
async def remove_channel_2(client: Client, query):
    chat_id = int(query.data.split("_")[2])
    await pending_collection_2.delete_one({"chat_id": chat_id})
    await query.message.reply(f"Channel {chat_id} has been removed from the pending list.")
