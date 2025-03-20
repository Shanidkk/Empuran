# ©️ ebiza
from pyrogram import Client
from pyrogram.types import ChatMemberUpdated

from database.join_leave_db import db
from utils import temp


# Track Joins & Leaves via Specific Invite Links
@Client.on_chat_member_updated()
async def track_join_leave(bot: Client, event: ChatMemberUpdated):
    chat_id = event.chat.id

    if chat_id not in [temp.REQ_CHANNEL1, temp.REQ_CHANNEL2]:
        return

    links = [bot.req_link1, bot.req_link2]
    user_id = (
        event.new_chat_member.user.id
        if event.new_chat_member
        else event.old_chat_member.user.id
    )

    if event.new_chat_member:
        if event.invite_link.invite_link in links:
            await db.update_stats(chat_id, user_id, "join")
            await db.store_user_invite(user_id, chat_id, event.invite_link.invite_link)
        
        # print(f"User ID: {user_id}")
        # print("Alert Messages: ", temp.ALERT_MESSAGES)
        if user_id not in temp.ALERT_MESSAGES:
            if chat_id == temp.REQ_CHANNEL1:
                text = "**⚠️ ഇനി Update Channel 2 ൽ കൂടെ ജോയിൻ ആയാൽ സിനിമ കിട്ടും.\n\n⚠️ You need to join my Update Channel 2 to get the file.**"
            else:
                text = "**⚠️ ഇനി Update Channel 1 ൽ കൂടെ ജോയിൻ ആയാൽ സിനിമ കിട്ടും.\n\n⚠️ You need to join my Update Channel 1 to get the file.**"
            alert_msg = await bot.send_message(
                chat_id=user_id,
                text=text,
            )
            temp.ALERT_MESSAGES[user_id] = alert_msg.id  # Saves each chat's message
    elif event.old_chat_member:
        user_invite_link = await db.get_user_invite(user_id, chat_id)
        if user_invite_link in links:
            await db.update_stats(chat_id, user_id, "leave")
