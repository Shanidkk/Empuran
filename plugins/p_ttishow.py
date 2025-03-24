from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT, MELCOW_NEW_USERS
from database.users_chats_db import db
from database.join_leave_db import db as fsub_db
from database.ia_filterdb import Media, Mediaa, db as clientDB, db1 as clientDB2, db2 as clientDB3
from utils import get_size, temp, get_settings
from Script import script
from pyrogram.errors import ChatAdminRequired
from .auto_sub import get_total_requests_count
"""-----------------------------------------https://t.me/GetTGLink/4179 --------------------------------------"""

@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        if not await db.get_chat(message.chat.id):
            total=await bot.get_chat_members_count(message.chat.id)
            r_j = message.from_user.mention if message.from_user else "Anonymous" 
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, r_j))       
            await db.add_chat(message.chat.id, message.chat.title)
        if message.chat.id in temp.BANNED_CHATS:
            # Inspired from a boat of a banana tree
            buttons = [[
                InlineKeyboardButton('Support', url=f'https://t.me/{SUPPORT_CHAT}')
            ]]
            reply_markup=InlineKeyboardMarkup(buttons)
            k = await message.reply(
                text='<b>CHAT NOT ALLOWED 🐞\n\nMy admins has restricted me from working here ! If you want to know more about it contact support..</b>',
                reply_markup=reply_markup,
            )

            try:
                await k.pin()
            except:
                pass
            await bot.leave_chat(message.chat.id)
            return
        buttons = [[
            InlineKeyboardButton('ℹ️ Help', url=f"https://t.me/{temp.U_NAME}?start=help"),
            InlineKeyboardButton('📢 Updates', url='https://t.me/TeamEvamaria')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=f"<b>Thankyou For Adding Me In {message.chat.title} ❣️\n\nIf you have any questions & doubts about using me contact support.</b>",
            reply_markup=reply_markup)
    else:
        settings = await get_settings(message.chat.id)
        if settings["welcome"]:
            for u in message.new_chat_members:
                if (temp.MELCOW).get('welcome') is not None:
                    try:
                        await (temp.MELCOW['welcome']).delete()
                    except:
                        pass
                temp.MELCOW['welcome'] = await message.reply(f"<b>Hey , {u.mention}, Welcome to {message.chat.title}</b>")


@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        buttons = [[
            InlineKeyboardButton('Support', url=f'https://t.me/{SUPPORT_CHAT}')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text='<b>Hello Friends, \nMy admin has told me to leave from group so i go! If you wanna add me again contact my support group.</b>',
            reply_markup=reply_markup,
        )

        await bot.leave_chat(chat)
        await message.reply(f"left the chat `{chat}`")
    except Exception as e:
        await message.reply(f'Error - {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("Chat Not Found In DB")
    if cha_t['is_disabled']:
        return await message.reply(f"This chat is already disabled:\nReason-<code> {cha_t['reason']} </code>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('Chat Successfully Disabled')
    try:
        buttons = [[
            InlineKeyboardButton('Support', url=f'https://t.me/{SUPPORT_CHAT}')
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat_, 
            text=f'<b>Hello Friends, \nMy admin has told me to leave from group so i go! If you wanna add me again contact my support group.</b> \nReason : <code>{reason}</code>',
            reply_markup=reply_markup)
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Error - {e}")


@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("Chat Not Found In DB !")
    if not sts.get('is_disabled'):
        return await message.reply('This chat is not yet disabled.')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("Chat Successfully re-enabled")


@Client.on_message(filters.command('stats') & filters.incoming)
async def get_ststs(bot, message):
    rju = await message.reply('Fetching stats..')
    tot = await Media.count_documents()
    tota = await Mediaa.count_documents()
    total = tot + tota
    users = await db.total_users_count()
    chats = await db.total_chat_count()
    stats = await clientDB.command('dbStats')
    used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))        
    free_dbSize = 512-used_dbSize
    stats2 = await clientDB2.command('dbStats')
    used_dbSize2 = (stats2['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
    free_dbSize2 = 512-used_dbSize2
    stats3 = await clientDB3.command('dbStats')
    used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
    free_dbSize3 = 512-used_dbSize3
    await rju.edit(script.STATUS_TXT2.format(total, tot, round(used_dbSize2, 2), round(free_dbSize2, 2), tota, round(used_dbSize3, 2), round(free_dbSize3, 2), users, chats, round(used_dbSize, 2), round(free_dbSize, 2)))

# a function for trespassing into others groups, Inspired by a Vazha
# Not to be used , But Just to showcase his vazhatharam.
# @Client.on_message(filters.command('invite') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite Link Generation Failed, Iam Not Having Sufficient Rights")
    except Exception as e:
        return await message.reply(f'Error {e}')
    await message.reply(f'Here is your Invite Link {link.invite_link}')

@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban_a_user(bot, message):
    # https://t.me/GetTGLink/4185
    if len(message.command) == 1:
        return await message.reply('Give me a user id / username')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("This is an invalid user, make sure ia have met him before.")
    except IndexError:
        return await message.reply("This might be a channel, make sure its a user.")
    except Exception as e:
        return await message.reply(f'Error - {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if jar['is_banned']:
            return await message.reply(f"{k.mention} is already banned\nReason: {jar['ban_reason']}")
        await db.ban_user(k.id, reason)
        temp.BANNED_USERS.append(k.id)
        await message.reply(f"Successfully banned {k.mention}")


    
@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a user id / username')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("This is an invalid user, make sure ia have met him before.")
    except IndexError:
        return await message.reply("Thismight be a channel, make sure its a user.")
    except Exception as e:
        return await message.reply(f'Error - {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if not jar['is_banned']:
            return await message.reply(f"{k.mention} is not yet banned.")
        await db.remove_ban(k.id)
        temp.BANNED_USERS.remove(k.id)
        await message.reply(f"Successfully unbanned {k.mention}")


    
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    # https://t.me/GetTGLink/4184
    raju = await message.reply('Getting List Of Users')
    users = await db.get_all_users()
    out = "Users Saved In DB Are:\n\n"
    async for user in users:
        out += f"<a href=tg://user?id={user['id']}>{user['name']}</a>"
        if user['ban_status']['is_banned']:
            out += '( Banned User )'
        out += '\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption="List Of Users")

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    raju = await message.reply('Getting List Of chats')
    chats = await db.get_all_chats()
    out = "Chats Saved In DB Are:\n\n"
    async for chat in chats:
        out += f"**Title:** `{chat['title']}`\n**- ID:** `{chat['id']}`"
        if chat['chat_status']['is_disabled']:
            out += '( Disabled Chat )'
        out += '\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('chats.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('chats.txt', caption="List Of Chats")


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


@Client.on_callback_query(filters.regex("^purge_(all|chat_.+|cancel)$"))
async def confirm_callback(bot, query):
    action = query.data.split("_", 1)[1]
    if action == "cancel":
        return await query.message.edit_text("❌ **Action Cancelled!**")
    await confirm_purge(bot, query.message, action, f"Channel {action}" if action != "all" else "All Data")


@Client.on_callback_query(filters.regex("^confirm_(all|chat_.+)$"))
async def execute_purge(bot, query):
    action = query.data.split("_", 1)[1]
    if action.startswith("chat"):
        chat_id = action.split("_")[1]
        await db.delete_all_reqs(chat_id)
        msg = f"✅ **Chat ID {chat_id} Cleared!**"
    else:
        await db.delete_all_reqs()
        msg = f"✅ **All Data Cleared!**"
    
    await query.message.edit_text(msg)


@Client.on_message(filters.command("total_req") & filters.user(ADMINS))
async def total_requests(bot, message):
user_id = message.from_user.id
wait = await message.reply_text("Fetching Req Stats..", quote=True)

# Fetch channel data before iterating  
channels = []  
for i, req_channel in enumerate([temp.REQ_CHANNEL1, temp.REQ_CHANNEL2], start=1):  
    if req_channel:  
        total_requests = await get_total_requests_count(chat_id=temp.REQ_CHANNEL1, coll=i)
        stats = await fsub_db.get_stats(int(req_channel))  
        chat = await bot.get_chat(int(req_channel))  
        channels.append((chat, req_channel, total_requests, stats))  

# Build response text  
text = "\n\n".join(  
    f"○ {chat.title} [{chat_id}]\n"  
    f"    • Total {total} Requests\n"  
    f"    • Joined : {stats['joined']} | • Left : {stats['left']}"  
    for chat, chat_id, total, stats in channels  
)  
await wait.edit(text)


@Client.on_message(filters.command("get_fsub") & filters.user(ADMINS))
async def channel_info(bot, message):
    wait = await message.reply_text("Fetching FSUb Stats", quote=True)

    channel_ids = [temp.REQ_CHANNEL1, temp.REQ_CHANNEL2]
    text = ""

    for index, chat_id in enumerate(channel_ids, start=1):
        if not chat_id:
            continue

        chat = await bot.get_chat(int(chat_id))
        fsub_type = "Request" if (fsub1 := await (getattr(db, f"get_fsub_mode{index}")())) and fsub1["mode"] == "req" else "Normal"

        text += f"""➲ **Channel Number:** REQ_CHANNEL{index}
➲ **ID:** `{chat.id}`
➲ **Title:** {chat.title}
➲ **Link:** {chat.invite_link or 'N/A'}
➲ **Username:** { '@' + chat.username if chat.username else 'None'}
➲ **Chat Type:** {"Public Channel" if chat.username else "Private Channel"}
➲ **FSub Type:** {fsub_type}\n\n"""

    await wait.edit(text=text, disable_web_page_preview=True)
