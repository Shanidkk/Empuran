import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from info import ADMINS
from utils import temp
from database.fsub_db import db
from database.join_leave_db import db as lvdb 
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO)


async def create_invite(bot: Client, chat_id: int, req_mode: bool) -> str:
    """Create an invite link for the given chat ID with request mode."""
    try:
        link = (await bot.create_chat_invite_link(chat_id=chat_id, creates_join_request=req_mode)).invite_link
        return link
    except Exception as e:
        logging.error(f"Error creating invite link for chat {chat_id}: {e}")
        return "None"


@Client.on_message(filters.command("setchat1") & filters.user(ADMINS))
async def set_fsub_chat1(bot: Client, message: Message):
    """Set the first Fsub Chat."""
    await message.react("🌭")
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage:** /setchat1 [chat_id]\n⚠️ Please provide a valid chat ID.", quote=True)
        return

    try:
        chat_id = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ **Invalid Chat ID!**\nChat ID must be a number.", quote=True)
        return

    text = f"✅ **Fsub Chat 1 Set!**\n📌 **Chat ID:** `{chat_id}`\n\n🔄 Generating invite link..."
    await message.reply_text(text, quote=True, parse_mode=enums.ParseMode.HTML)

    invite_link = await create_invite(bot, chat_id, temp.REQ_FSUB_MODE1)
    mode = (await db.get_fsub_mode1())["mode"]
    await db.add_fsub_chat1(chat_id, invite_link, mode)

    bot.req_link1 = invite_link
    temp.REQ_CHANNEL1 = chat_id

    await message.reply_text(
        f"✅ **Fsub Chat 1 Added Successfully!**\n📌 **Chat ID:** `{chat_id}`\n🔗 **Invite Link:** {invite_link}",
        quote=True,
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(filters.command("delchat1") & filters.user(ADMINS))
async def delete_fsub_chat1(bot: Client, message: Message):
    """Delete the first Fsub Chat."""
    await message.react("👍")
    await db.delete_fsub_chat1()
    temp.REQ_CHANNEL1 = None
    bot.req_link1 = None

    await message.reply_text("🗑 **Fsub Chat 1 Removed Successfully!**", quote=True)


@Client.on_message(filters.command("viewchat1") & filters.user(ADMINS))
async def view_fsub_chat1(bot: Client, message: Message):
    """View the first Fsub Chat."""
    await message.react("👍")
    chat = await db.get_fsub_chat1()

    if not chat:
        await message.reply_text("❌ **No Fsub Chat 1 found in the database.**", quote=True)
    else:
        await message.reply_text(
            f"📌 **Fsub Chat 1 Details:**\n"
            f"🆔 **Chat ID:** `{chat['chat_id']}`\n"
            f"🔗 **Invite Link:** {chat['invite_link']}",
            quote=True,
            parse_mode=enums.ParseMode.HTML
        )


@Client.on_message(filters.command("setchat2") & filters.user(ADMINS))
async def set_fsub_chat2(bot: Client, message: Message):
    """Set the second Fsub Chat."""
    await message.react("🍌")
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage:** /setchat2 [chat_id]\n⚠️ Please provide a valid chat ID.", quote=True)
        return

    try:
        chat_id = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ **Invalid Chat ID!**\nChat ID must be a number.", quote=True)
        return

    text = f"✅ **Fsub Chat 2 Set!**\n📌 **Chat ID:** `{chat_id}`\n\n🔄 Generating invite link..."
    await message.reply_text(text, quote=True, parse_mode=enums.ParseMode.HTML)

    invite_link = await create_invite(bot, chat_id, temp.REQ_FSUB_MODE2)
    mode = (await db.get_fsub_mode2())["mode"]
    await db.add_fsub_chat2(chat_id, invite_link, mode)

    bot.req_link2 = invite_link
    temp.REQ_CHANNEL2 = chat_id

    await message.reply_text(
        f"✅ **Fsub Chat 2 Added Successfully!**\n📌 **Chat ID:** `{chat_id}`\n🔗 **Invite Link:** {invite_link}",
        quote=True,
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(filters.command("delchat2") & filters.user(ADMINS))
async def delete_fsub_chat2(bot: Client, message: Message):
    """Delete the second Fsub Chat."""
    await message.react("👍")
    await db.delete_fsub_chat2()
    temp.REQ_CHANNEL2 = None
    bot.req_link2 = None

    await message.reply_text("🗑 **Fsub Chat 2 Removed Successfully!**", quote=True)

@Client.on_message(filters.command("fsub_mode1") & filters.user(ADMINS))
async def toggle_fsub_mode1(bot: Client, message: Message):
    """Toggle the global join request mode for Fsub Chat 1."""
    fsub_mode = await db.get_fsub_mode1()
    temp.REQ_FSUB_MODE1 = fsub_mode["mode"] == "normal"

    new_mode = "req" if temp.REQ_FSUB_MODE1 else "normal"
    if temp.REQ_CHANNEL1:
        new_link = (await bot.create_chat_invite_link(
            int(temp.REQ_CHANNEL1), creates_join_request=temp.REQ_FSUB_MODE1
        )).invite_link
        bot.req_link1 = new_link
        await db.update_fsub_link1(temp.REQ_CHANNEL1, new_link)
    await db.add_fsub_mode1(new_mode)
    await message.reply_text(f"✅ **Fsub Mode 1 Updated:** `{new_mode}`", quote=True)


@Client.on_message(filters.command("fsub_mode2") & filters.user(ADMINS))
async def toggle_fsub_mode2(bot: Client, message: Message):
    """Toggle the global join request mode for Fsub Chat 2."""
    fsub_mode = await db.get_fsub_mode2()
    temp.REQ_FSUB_MODE2 = fsub_mode["mode"] == "normal"
    
    new_mode = "req" if temp.REQ_FSUB_MODE2 else "normal"
    if temp.REQ_CHANNEL2:
        new_link = (await bot.create_chat_invite_link(
            int(temp.REQ_CHANNEL2), creates_join_request=temp.REQ_FSUB_MODE2
        )).invite_link
        bot.req_link2 = new_link
        await db.update_fsub_link2(temp.REQ_CHANNEL2, new_link)
    await db.add_fsub_mode2(new_mode)
    await message.reply_text(f"✅ **Fsub Mode 2 Updated:** `{new_mode}`", quote=True)

@Client.on_message(filters.command('purge') & filters.private & filters.user(ADMINS))
async def purge_requests(bot, message):
    """Ask the admin which data to purge."""
    args = message.command[1:]
    if args:  # Purge by specific chat ID
        return await confirm_purge(bot, message, f"chat_{args[0]}", f"Chat ID: {args[0]}")

    buttons = [
        [
            InlineKeyboardButton("🗑 Purge One", callback_data=f"purge_chat_{temp.REQ_CHANNEL1}"),
            InlineKeyboardButton("🗑 Purge Two", callback_data=f"purge_chat_{temp.REQ_CHANNEL2}"),
        ],
        [
            InlineKeyboardButton("🚨 Purge All", callback_data="purge_all"),
            InlineKeyboardButton("❌ Cancel", callback_data="purge_cancel"),
        ]
    ]
    await message.reply_text(
        "⚠️ **Select data to purge. This cannot be undone!**",
        quote=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def confirm_purge(bot, message, action, label):
    """Ask for confirmation before purging data."""
    buttons = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ No", callback_data="purge_cancel"),
        ]
    ]
    try:
        await message.edit_text(
            f"⚠️ **Confirm purge: {label}?**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        await message.reply_text(
            f"⚠️ **Confirm purge: {label}?**",
            quote=True,
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@Client.on_callback_query(filters.regex("^confirm_(all|chat_.+)$"))
async def execute_purge(client, query):
    """Handles purge confirmation for all requests or specific chat requests."""
    action = query.data.split("_", 1)[1]
    
    if action.startswith("chat"):
        chat_id = int(action.split("_")[1])
        await db.delete_all_reqs(chat_id)
        msg = f"✅ **Chat ID {chat_id} Cleared!**"
    else:
        await db.delete_all_reqs()
        msg = f"✅ **All Requests Cleared!**"
    
    try:
        await query.message.edit_text(msg)
    except Exception:
        await query.message.reply_text(msg, quote=True)
    
    await query.answer("Purge Completed!", show_alert=True)


@Client.on_callback_query(filters.regex("^purge_(chat_.+|all|cancel)$"))
async def cb_handler(client: Client, query):
    """Handles callback queries for purge actions."""
    data = query.data

    if data == "purge_cancel":
        await query.message.delete()
    elif data.startswith("purge_chat_"):
        chat_id = data.split("_")[-1]
        await confirm_purge(client, query.message, f"chat_{chat_id}", f"Chat ID: {chat_id}")
    elif data == "purge_all":
        await confirm_purge(client, query.message, "all", "All Requests")
    
    await query.answer()

@Client.on_message(filters.command("total_req") & filters.user(ADMINS))
async def total_requests(bot, message):
    """Fetch total request statistics from all subscribed channels."""
    wait = await message.reply_text("Fetching Request Stats...", quote=True)

    channels = []
    for i, req_channel in enumerate([temp.REQ_CHANNEL1, temp.REQ_CHANNEL2], start=1):
        if req_channel:
            total_requests = await db.get_all_reqs_count(chat_id=int(req_channel))
            chat = await bot.get_chat(int(req_channel))
            # Fetch FSUB mode
            fsub_mode_data = await db.get_fsub_mode1() if i == 1 else await db.get_fsub_mode2()
            fsub_mode = fsub_mode_data["mode"] if fsub_mode_data else "Unknown"
            # Get Join Count (If Normal Mode) or Request Count
            if fsub_mode == "normal":
                joined_count = await lvdb.get_stats(int(req_channel))  # How many joined
                count_text = f"✅ **Joined Users:** {joined_count['joined']}"
            else:
                count_text = f"📌 **Total Requests:** {total_requests}"
            channels.append((chat, req_channel, fsub_mode, count_text))
    if not channels:
        return await wait.edit("❌ No request channels found!")

    # Build response text
    text = "\n\n".join(
        f"○ **{chat.title}** [`{chat_id}`]\n"
        f"    • **FSUB Mode:** `{fsub_mode}`\n"
        f"    • {count_text}"
        for chat, chat_id, fsub_mode, count_text in channels
    )

    await wait.edit(text)

@Client.on_message(filters.command("get_fsub") & filters.user(ADMINS))
async def channel_info(bot, message):
    """Fetch and display forced subscription (FSUB) channel details."""
    wait = await message.reply_text("Fetching FSUB Stats...", quote=True)
    channels = [
        (1, await db.get_fsub_chat1()),
        (2, await db.get_fsub_chat2())
    ]
    text = ""
    for index, fsub_data in channels:
        if not fsub_data:
            continue  # Skip if no data is found

        chat_id = fsub_data.get("chat_id")
        chat = await bot.get_chat(int(chat_id))
        fsub_type = "Request" if fsub_data.get("mode") == "req" else "Normal"

        text += f"""➲ **Channel Number:** REQ_CHANNEL{index}
➲ **ID:** `{chat.id}`
➲ **Title:** {chat.title}
➲ **Link:** {fsub_data.get("invite_link", "N/A")}
➲ **Username:** { '@' + chat.username if chat.username else 'None'}
➲ **Chat Type:** {"Public Channel" if chat.username else "Private Channel"}
➲ **FSub Type:** {fsub_type}\n\n"""

    if not text:
        text = "❌ No FSUB channel data found!"

    await wait.edit(text=text, disable_web_page_preview=True)
