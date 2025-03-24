import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from config import ADMINS, temp, db

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
    fsub_mode = await db.get_fsub_mode1()
    temp.REQ_FSUB_MODE1 = fsub_mode["mode"] != "req"

    new_mode = "req" if temp.REQ_FSUB_MODE1 else "normal"
    await db.add_fsub_mode1(new_mode)

    try:
        new_link = await create_invite(bot, temp.REQ_CHANNEL1, temp.REQ_FSUB_MODE1)
        bot.req_link1 = new_link
        await db.update_fsub_link1(temp.REQ_CHANNEL1, new_link)
    except Exception as e:
        logging.error(f"Error updating invite link for Fsub Chat 1: {e}")

    await message.reply_text(f"✅ **Fsub Chat 1 Mode Updated:** `{new_mode}`", quote=True)


@Client.on_message(filters.command("fsub_mode2") & filters.user(ADMINS))
async def toggle_fsub_mode2(bot: Client, message: Message):
    """Toggle the join request mode for Fsub Chat 2."""
    fsub_mode = await db.get_fsub_mode2()
    temp.REQ_FSUB_MODE2 = fsub_mode["mode"] != "req"

    new_mode = "req" if temp.REQ_FSUB_MODE2 else "normal"
    await db.add_fsub_mode2(new_mode)

    try:
        new_link = await create_invite(bot, temp.REQ_CHANNEL2, temp.REQ_FSUB_MODE2)
        bot.req_link2 = new_link
        await db.update_fsub_link2(temp.REQ_CHANNEL2, new_link)
    except Exception as e:
        logging.error(f"Error updating invite link for Fsub Chat 2: {e}")

    await message.reply_text(f"✅ **Fsub Chat 2 Mode Updated:** `{new_mode}`", quote=True)
