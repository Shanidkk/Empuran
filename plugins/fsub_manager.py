import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from info import ADMINS
from utils import temp
from database.fsub_db import db
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
    await db.add_fsub_chat1(chat_id, invite_link)

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
    await db.add_fsub_chat2(chat_id, invite_link)

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
    """Toggle the join request mode for Fsub Chat 1."""
    if not temp.REQ_CHANNEL1:
        return await message.reply_text("❌ No Fsub Chat 1 set!")

    fsub_mode = await db.get_fsub_mode1()
    temp.REQ_FSUB_MODE1 = fsub_mode["mode"] == "normal"

    new_mode = "req" if temp.REQ_FSUB_MODE1 else "normal"
    await db.add_fsub_mode1(temp.REQ_CHANNEL1, new_mode)

    try:
        new_link = await create_invite(bot, temp.REQ_CHANNEL1, temp.REQ_FSUB_MODE1)
        if new_link != "None":
            bot.req_link1 = new_link
            await db.update_fsub_link1(temp.REQ_CHANNEL1, new_link)
    except Exception as e:
        logging.error(f"Error updating invite link for Fsub Chat 1: {e}")

    await message.reply_text(f"✅ **Fsub Chat 1 Mode Updated:** `{new_mode}`", quote=True)


@Client.on_message(filters.command("fsub_mode2") & filters.user(ADMINS))
async def toggle_fsub_mode2(bot: Client, message: Message):
    """Toggle the join request mode for Fsub Chat 2."""
    if not temp.REQ_CHANNEL2:
        return await message.reply_text("❌ No Fsub Chat 2 set!")

    fsub_mode = await db.get_fsub_mode2()
    temp.REQ_FSUB_MODE2 = fsub_mode["mode"] == "normal"

    new_mode = "req" if temp.REQ_FSUB_MODE2 else "normal"
    await db.add_fsub_mode2(temp.REQ_CHANNEL2, new_mode)

    try:
        new_link = await create_invite(bot, temp.REQ_CHANNEL2, temp.REQ_FSUB_MODE2)
        if new_link != "None":
            bot.req_link2 = new_link
            await db.update_fsub_link2(temp.REQ_CHANNEL2, new_link)
    except Exception as e:
        logging.error(f"Error updating invite link for Fsub Chat 2: {e}")

    await message.reply_text(f"✅ **Fsub Chat 2 Mode Updated:** `{new_mode}`", quote=True)
    
@Client.on_message(filters.command('purge') & filters.private & filters.user(ADMINS))
async def purge_requests(bot, message):
    args = message.command[1:]
    if args:  # Purge by chat ID
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
async def execute_purge(bot, query):
    """Handles purge confirmation for all requests or specific chat requests."""
    action = query.data.split("_", 1)[1]
    
    if action.startswith("chat"):
        chat_id = int(action.split("_")[1])
        await db.delete_all_reqs(chat_id)
        msg = f"✅ **Chat ID {chat_id} Cleared!**"
    else:
        await db.delete_all_reqs()
        msg = f"✅ **All Requests Cleared!**"
    
    await query.message.edit_text(msg)


@Client.on_message(filters.command("total_req") & filters.user(ADMINS))
async def total_requests(bot, message):
    """Fetch total request statistics from all subscribed channels."""
    user_id = message.from_user.id
    wait = await message.reply_text("Fetching Request Stats...", quote=True)

    channels = []
    for i, req_channel in enumerate([temp.REQ_CHANNEL1, temp.REQ_CHANNEL2], start=1):
        if req_channel:
            total_requests = await db.get_all_reqs_count(chat_id=int(req_channel))
            chat = await bot.get_chat(int(req_channel))
            channels.append((chat, req_channel, total_requests))

    if not channels:
        return await wait.edit("❌ No request channels found!")

    # Build response text
    text = "\n\n".join(
        f"○ **{chat.title}** [`{chat_id}`]\n"
        f"    • **Total Requests:** {total}"
        for chat, chat_id, total in channels
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
