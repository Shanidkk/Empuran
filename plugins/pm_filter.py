# Kanged From @TroJanZheX
import asyncio
lock = asyncio.Lock()
import re
import ast
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, LOG_CHANNEL
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, QueryIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, is_requested_one, is_requested_two
from database.users_chats_db import db
from database.ia_filterdb import Media, Mediaa, get_bad_files, get_file_details, get_search_results, db as clientDB, db1 as clientDB2, db2 as clientDB3
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import find_gfilter, get_gfilters
import logging
from plugins.commands import incol
from .auto_sub import remove_channel_2, remove_channel_1, show_channel_details_2, show_channel_details_1


logger = logging.getLogger(__name__)
# Disable logging completely
logging.getLogger().setLevel(logging.CRITICAL)

BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    g = await global_filters(client, message)
    if g == False:
        k = await manual_filters(client, message)
        if k == False:
            await auto_filter(client, message)

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if content.startswith("/") or content.startswith("#"): return  # ignore commands and hashtags
    await message.reply_text("<b>Just type the movie name in the group. I can only work in groups\n\nഇവിടെ ചോദിച്ചാൽ സിനിമ കിട്ടില്ല ഗ്രൂപ്പിൽ മാത്രം സിനിമ ചോദിക്കുക\n\n ask in Group Link👇\nhttps://t.me/new_movies_group_2021\n https://t.me/new_movies_group_2021</b>")
    await bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"<b>#PM_MSG\n\nName : {user}\n\nID : {user_id}\n\nMessage : {content}</b>"
)

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("Search for Yourself", show_alert=True)

    try:
        offset = int(offset)
    except ValueError:
        offset = 0

    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)

    if not files:
        await query.answer("no files", show_alert=True)
        return

    settings = await get_settings(query.message.chat.id)

    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] ⊳ {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if 0 < offset < 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10

    if n_offset == '':
        btn.append(
            [InlineKeyboardButton("↵ Bᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("Nᴇxᴛ ⤷", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("↵ Bᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("Nᴇxᴛ ⤷", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer("okda", show_alert=True)
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("Not your request", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movie = movies[(int(movie_))]
    await query.answer("Cʜᴇᴄᴋɪɴɢ Fᴏʀ Mᴏᴠɪᴇ Iɴ Dᴀᴛᴀʙᴀsᴇ...")
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
            await query.message.delete()
        else:
            reqstr1 = query.from_user.id if query.from_user else 0
            reqstr = await bot.get_users(reqstr1)                
            k = await query.message.edit("ᴍᴏᴠɪᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ...")
            await asyncio.sleep(10)
            await k.delete()

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data.startswith("show_channel_1"):
        await show_channel_details_1(client, query)
    elif query.data.startswith("show_channel_2"):
        await show_channel_details_2(client, query)
    elif query.data.startswith("remove_channel_1"):
        await remove_channel_1(client, query)
    elif query.data.startswith("remove_channel_2"):
        await remove_channel_2(client, query)
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
            
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.file_name
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        buttons = [[
            InlineKeyboardButton('സിനിമ പ്രേമി', url='https://t.me/+A0B5zHQ2_wkxZjdl')
            ],[
            InlineKeyboardButton('മൂവീസ് ക്ലബ്', url='https://t.me/+A0B5zHQ2_wkxZjdl')
         ]]
        try:
            if settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
        except QueryIdInvalid:
            await query.answer("This query is no longer valid.", show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if temp.REQ_CHANNEL1 and not await is_requested_one(client, query):
            await query.answer("നിങ്ങൾ മുകളിൽ കാണുന്ന ചാനലിൽ ജോയിൻ ആയിട്ടില്ല❌ ഒന്നൂടെ ആയി നോക്കുക ശേഷം സിനിമ വരും✅\n\n𝗌𝗈𝗅𝗏𝖾 𝗂𝗌𝗌𝗎𝖾?-𝖨𝖿 𝖳𝗁𝖾𝗋𝖾 𝖠𝗋𝖾 2 𝖢𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝖳𝗈 𝖩𝗈𝗂𝗇, 𝖩𝗈𝗂𝗇 𝖥𝗂𝗋𝗌𝗍 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝖳𝗁𝖾𝗇 𝖩𝗈𝗂𝗇 𝖳𝗁𝖾 𝖲𝖾𝖼𝗈𝗇𝖽 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝗔𝗳𝘁𝗲𝗿 5𝘀𝗲𝗰", show_alert=True)
            return
        if temp.REQ_CHANNEL2 and not await is_requested_two(client, query):
            await query.answer("Update Channel 2 ഒന്നൂടെ ജോയിൻ ആവുക എന്നിട്ട് Try Again ക്ലിക്ക് ചെയ്യുക സിനിമ കിട്ടുന്നതാണ്🫶🏼\n\n𝗌𝗈𝗅𝗏𝖾 𝗂𝗌𝗌𝗎𝖾?-𝖨𝖿 𝖳𝗁𝖾𝗋𝖾 𝖠𝗋𝖾 2 𝖢𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝖳𝗈 𝖩𝗈𝗂𝗇, 𝖩𝗈𝗂𝗇 𝖥𝗂𝗋𝗌𝗍 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝖳𝗁𝖾𝗇 𝖩𝗈𝗂𝗇 𝖳𝗁𝖾 𝖲𝖾𝖼𝗈𝗇𝖽 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝗔𝗳𝘁𝗲𝗿 5𝘀𝗲𝗰", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.file_name
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        buttons = [[
            InlineKeyboardButton('സിനിമ പ്രേമി', url='https://t.me/+IJh-LnhpCUQwMjE1')
         ]]
        await query.answer()
        xd = await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == "checksubp" else False,
            reply_markup=InlineKeyboardMarkup(
               [[
                InlineKeyboardButton('സിനിമ പ്രേമി', url='https://t.me/+_PdIBkSu7bAwOTVl')
               ],[
                InlineKeyboardButton('മൂവീസ് ക്ലബ്', url='https://t.me/+_PdIBkSu7bAwOTVl')
               ]]
            )  
        )
        if title and any(keyword in title.lower() for keyword in ['predvd', 'predvdrip']):
            f_caption += "\n⚠️<b><i>ഈ മൂവിയുടെ ഫയൽ എവിടെയെങ്കിലും ഫോർവേഡ് ചെയ്തു വെക്കുക എന്നിട്ട് ഡൗൺലോഡ് ചെയ്യുക\n\n3 മിനിറ്റിൽ ഇവിടുന്ന് ഡിലീറ്റ് ആവും🗑\n\n⚠️Forward the file of this Movie somewhere and download it\n\nWill be deleted from here in 3 minutes🗑</i></b>"
            inline_keyboard = [
                 [InlineKeyboardButton("🔸𝗠𝗢𝗩𝗜𝗘𝗦 𝗚𝗥𝗢𝗨𝗣🔸", url="https://t.me/new_movies_group_2021")]
                ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            await xd.edit_caption(caption=f_caption, reply_markup=reply_markup)
            await asyncio.sleep(180)                   
            await xd.delete()

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fᴇᴛᴄʜɪɴɢ Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} ᴏɴ DB... Pʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        files_media1, files_media2, total_media = await get_bad_files(keyword)        
        await query.message.edit_text(f"<b>Fᴏᴜɴᴅ {total_media} Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nFɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇss ᴡɪʟʟ sᴛᴀʀᴛ ɪɴ 5 sᴇᴄᴏɴᴅs!</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                # Delete files from Media collection
                for file in files_media1:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 100 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
                # Delete files from Mediaa collection
                for file in files_media2:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Mediaa.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 100 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.exception
                await query.message.edit_text(f'Eʀʀᴏʀ: {e}')
            else:
                await query.message.edit_text(f"<b>Pʀᴏᴄᴇss Cᴏᴍᴘʟᴇᴛᴇᴅ ғᴏʀ ғɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ !\n\nSᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}.</b>")
            
    elif query.data == "pages":
        await query.answer()
    elif query.data == "matt":
        btn = [[                
            InlineKeyboardButton('𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖦𝗋𝗈𝗎𝗉', url=f"https://t.me/color_films")
            ],[   
            InlineKeyboardButton('𝖻𝖺𝖼𝗄', callback_data='help')
            ]]
        await query.message.edit_text(text=f"<u><b>𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖥𝗈𝗅𝗅𝗈𝗐 𝖱𝗎𝗅𝖾𝗌</b></u>\n\n𝖠𝗌𝗄 𝖥𝗈𝗋 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀\n\n𝖬𝗎𝗌𝗍 𝖢𝗁𝖾𝖼𝗄 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝗂𝗇 𝖦𝗈𝗈𝗀𝗅𝖾 \n\n𝖠𝗌𝗄 𝖥𝗈𝗋 𝖬𝗈𝗏𝗂𝖾𝗌 𝖨𝗇 𝖤𝗇𝗀𝗅𝗂𝗌𝗁 𝖫𝖾𝗍𝗍𝖾𝗋𝗌 𝖮𝗇𝗅𝗒\n\n𝖣𝗈𝗇'𝗍 𝖠𝗌𝗄 𝖥𝗈𝗋 𝖴𝗇𝗋𝖾𝗅𝖾𝖺𝗌𝖾𝖽 𝖬𝗈𝗏𝗂𝖾𝗌\n\n[𝖬𝗈𝗏𝗂𝖾 𝖭𝖺𝗆𝖾, 𝖸𝖾𝖺𝗋, 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾] 𝖠𝗌𝗄 𝖳𝗁𝗂𝗌 𝖶𝖺𝗒\n\n𝖣𝗈 𝖭𝗈𝗍 𝖴𝗌𝖾 𝖶𝗈𝗋𝖽𝗌 𝖫𝗂𝗄𝖾 𝖣𝗎𝖻, 𝖬𝗈𝗏𝗂𝖾, 𝖫𝗂𝗇𝗄, 𝖯𝗅𝗌𝗌, 𝖲𝖾𝗇𝗍 𝖾𝗍𝖼 𝖮𝗍𝗁𝖾𝗋 𝖳𝗁𝖺𝗇 𝖳𝗁𝖾 𝖶𝖺𝗒 𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝖾𝖽 𝖠𝖻𝗈𝗏𝖾\n\n𝖣𝗈𝗇'𝗍 𝖴𝗌𝖾 𝖲𝗍𝗒𝗅𝗂𝗌𝗁 𝖥𝗈𝗇𝗍 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍\n\n𝖣𝗈𝗇'𝗍 𝖴𝗌𝖾 𝖲𝗒𝗆𝖻𝗈𝗅𝗌 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝗅𝗂𝗄𝖾 (+:;'!-|...𝖾𝗍𝖼)\n\n𝖨𝖿 𝖸𝗈𝗎 𝖣𝗈𝗇'𝗍 𝖦𝖾𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝖠𝗇𝖽 𝖲𝖾𝗋𝗂𝖾𝗌⌛️\n𝖢𝗈𝗇𝗍𝖺𝖼𝗍 𝖠𝖽𝗆𝗂𝗇 - @hey_vro2004\n\n<u><b>𝖬𝗈𝗏𝗂𝖾𝗌 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖥𝗈𝗋𝗆𝖺𝗍</b></u>\n𝖪𝗎𝗋𝗎𝗉 𝖬𝗈𝗏𝗂𝖾❌\n𝖪𝗎𝗋𝗎𝗉 2021 ✅\n𝖪𝗀𝖿: 𝖢𝗁𝖺𝗉𝗍𝖾𝗋 2❌\n𝖪𝗀𝖿 𝖢𝗁𝖺𝗉𝗍𝖾𝗋 2✅\n\n<u><b>𝖲𝖾𝗋𝗂𝖾𝗌 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖱𝗎𝗅𝖾𝗌</b></u>\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝗌𝖾𝖺𝗌𝗈𝗇 1❌\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖲01✅\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖤𝗉𝗂𝗌𝗈𝖽𝖾 1❌\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖲01𝖤01✅\n\n 𝖢𝗅𝗂𝖼𝗄 𝖡𝖾𝗅𝗈𝗐 𝖡𝗎𝗍𝗍𝗈𝗇𝗌 𝖠𝗇𝖽 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝗈𝗋 𝖲𝖾𝗋𝗂𝖾𝗌 𝖨𝗇 𝖬𝗈𝗏𝗂𝖾𝗌 𝖦𝗋𝗈𝗎𝗉💡", reply_markup=InlineKeyboardMarkup(btn))
    elif query.data == "oooi":
        xd = query.message.reply_to_message.text.replace(" ", "+")
        btn = [[                
            InlineKeyboardButton("𝗖𝗹𝗶𝗰𝗸 𝗛𝗲𝗿𝗲 𝗖𝗼𝗿𝗿𝗲𝗰𝘁 𝗠𝗼𝘃𝗶𝗲 𝗡𝗮𝗺𝗲", url=f"https://www.google.com/search?q={xd}")
            ],[   
            InlineKeyboardButton('𝖻𝖺𝖼𝗄', callback_data='nlang')
            ]]
        await query.message.edit_text(text=f"<u><b>𝗛𝗲𝘆 {query.from_user.mention} 👋 𝗣𝗹𝗲𝗮𝘀𝗲 𝗙𝗼𝗹𝗹𝗼𝘄 𝗕𝗲𝗹𝗼𝘄 𝗠𝗼𝘃𝗶𝗲𝘀 𝗢𝗿 𝗦𝗲𝗿𝗶𝗲𝘀 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗶𝗻𝗴 𝗥𝘂𝗹𝗲𝘀</b></u>\n\n𝗠𝗮𝗸𝗲 𝗦𝘂𝗿𝗲 𝗧𝗵𝗲 𝗠𝗼𝘃𝗶𝗲 𝗶𝘀 𝗥𝗲𝗹𝗲𝗮𝘀𝗲𝗱 𝗢𝗻 𝗢𝗧𝗧 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺𝘀\n\n𝖠𝗌𝗄 𝖥𝗈𝗋 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀\n\n𝖬𝗎𝗌𝗍 𝖢𝗁𝖾𝖼𝗄 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝗂𝗇 𝖦𝗈𝗈𝗀𝗅𝖾 \n\n𝖠𝗌𝗄 𝖥𝗈𝗋 𝖬𝗈𝗏𝗂𝖾𝗌 𝖨𝗇 𝖤𝗇𝗀𝗅𝗂𝗌𝗁 𝖫𝖾𝗍𝗍𝖾𝗋𝗌 𝖮𝗇𝗅𝗒\n\n𝖣𝗈𝗇'𝗍 𝖠𝗌𝗄 𝖥𝗈𝗋 𝖴𝗇𝗋𝖾𝗅𝖾𝖺𝗌𝖾𝖽 𝖬𝗈𝗏𝗂𝖾𝗌\n\n[𝖬𝗈𝗏𝗂𝖾 𝖭𝖺𝗆𝖾, 𝖸𝖾𝖺𝗋, 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾] 𝖠𝗌𝗄 𝖳𝗁𝗂𝗌 𝖶𝖺𝗒\n\n𝖣𝗈 𝖭𝗈𝗍 𝖴𝗌𝖾 𝖶𝗈𝗋𝖽𝗌 𝖫𝗂𝗄𝖾 𝖣𝗎𝖻, 𝖬𝗈𝗏𝗂𝖾, 𝖫𝗂𝗇𝗄, 𝖯𝗅𝗌𝗌, 𝖲𝖾𝗇𝗍 𝖾𝗍𝖼 𝖮𝗍𝗁𝖾𝗋 𝖳𝗁𝖺𝗇 𝖳𝗁𝖾 𝖶𝖺𝗒 𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝖾𝖽 𝖠𝖻𝗈𝗏𝖾\n\n𝖣𝗈𝗇'𝗍 𝖴𝗌𝖾 𝖲𝗍𝗒𝗅𝗂𝗌𝗁 𝖥𝗈𝗇𝗍 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍\n\n𝖣𝗈𝗇'𝗍 𝖴𝗌𝖾 𝖲𝗒𝗆𝖻𝗈𝗅𝗌 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝗅𝗂𝗄𝖾 (+:;'!-|...𝖾𝗍𝖼)\n\n𝗜𝗳 𝘆𝗼𝘂 𝗱𝗼𝗻'𝘁 𝗴𝗲𝘁 𝘁𝗵𝗮𝘁 𝗠𝗼𝘃𝗶𝗲𝘀 𝗼𝗿 𝗦𝗲𝗿𝗶𝗲𝘀 𝗲𝘃𝗲𝗻 𝗮𝗳𝘁𝗲𝗿 𝗳𝗼𝗹𝗹𝗼𝘄𝗶𝗻𝗴 𝘁𝗵𝗲 𝗿𝘂𝗹𝗲𝘀 𝗮𝗯𝗼𝘃𝗲, 𝘂𝗽𝗹𝗼𝗮𝗱 𝘁𝗵𝗲 𝗺𝗼𝘃𝗶𝗲 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 - <a href=https://t.me/ooppinne>𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘</a>\n\n<u><b>𝖬𝗈𝗏𝗂𝖾𝗌 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖥𝗈𝗋𝗆𝖺𝗍</b></u>\n𝖪𝗎𝗋𝗎𝗉 𝖬𝗈𝗏𝗂𝖾❌\n𝖪𝗎𝗋𝗎𝗉 2021 ✅\n𝖪𝗀𝖿: 𝖢𝗁𝖺𝗉𝗍𝖾𝗋 2❌\n𝖪𝗀𝖿 𝖢𝗁𝖺𝗉𝗍𝖾𝗋 2✅\n\n<u><b>𝖲𝖾𝗋𝗂𝖾𝗌 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖱𝗎𝗅𝖾𝗌</b></u>\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝗌𝖾𝖺𝗌𝗈𝗇 1❌\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖲01✅\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖤𝗉𝗂𝗌𝗈𝖽𝖾 1❌\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖲01𝖤01✅\n\n<b>🎬ഫസ്റ്റ് ആയിട്ട് നിങ്ങൾ ശ്രദ്ധിക്കേണ്ടത് മൂവി നെയിം ആണ് അതിനായി താക്കെ കാണുന്ന ബട്ടൺ ക്ലിക്കോ ചെയ്ത്  ഗൂഗിൾ പോയി നെയിം സെർച്ച് ചെയ്ത കറക്റ്റ് മൂവി നെയിം കോപ്പി ചെയ്തിട്ട് ഗ്രൂപ്പ് ൽ ഇട്ടാൽ കിട്ടും🤍\n\n💡മുകളിൽ ഉള്ള കാര്യങ്ങൾ ഫോളോ ചെയ്തിട്ടും മൂവി കിട്ടുന്നില്ല എനിക്കിൽ മൂവി 👉<a href=https://t.me/ooppinne>𝗠𝗦𝗚 𝗛𝗘𝗥𝗘</a> msg അയയ്ക്കുക 30 min ശേഷം മൂവി ബോട്ട് ഇൽ അപ്ലോഡ് ആക്കുന്നതാണ് 🎉</b>", reply_markup=InlineKeyboardMarkup(btn))
    elif query.data == "dey":
        btn = [[                
            InlineKeyboardButton('𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖦𝗋𝗈𝗎𝗉', url=f"https://t.me/color_films")
            ],[   
            InlineKeyboardButton('𝖻𝖺𝖼𝗄', callback_data='but')
            ]]
        await query.message.edit_text(text=f"<u><b>𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖥𝗈𝗅𝗅𝗈𝗐 𝖱𝗎𝗅𝖾𝗌</b></u>\n\n𝖠𝗌𝗄 𝖥𝗈𝗋 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀\n\n𝖬𝗎𝗌𝗍 𝖢𝗁𝖾𝖼𝗄 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝗂𝗇 𝖦𝗈𝗈𝗀𝗅𝖾 \n\n𝖠𝗌𝗄 𝖥𝗈𝗋 𝖬𝗈𝗏𝗂𝖾𝗌 𝖨𝗇 𝖤𝗇𝗀𝗅𝗂𝗌𝗁 𝖫𝖾𝗍𝗍𝖾𝗋𝗌 𝖮𝗇𝗅𝗒\n\n𝖣𝗈𝗇'𝗍 𝖠𝗌𝗄 𝖥𝗈𝗋 𝖴𝗇𝗋𝖾𝗅𝖾𝖺𝗌𝖾𝖽 𝖬𝗈𝗏𝗂𝖾𝗌\n\n[𝖬𝗈𝗏𝗂𝖾 𝖭𝖺𝗆𝖾, 𝖸𝖾𝖺𝗋, 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾] 𝖠𝗌𝗄 𝖳𝗁𝗂𝗌 𝖶𝖺𝗒\n\n𝖣𝗈 𝖭𝗈𝗍 𝖴𝗌𝖾 𝖶𝗈𝗋𝖽𝗌 𝖫𝗂𝗄𝖾 𝖣𝗎𝖻, 𝖬𝗈𝗏𝗂𝖾, 𝖫𝗂𝗇𝗄, 𝖯𝗅𝗌𝗌, 𝖲𝖾𝗇𝗍 𝖾𝗍𝖼 𝖮𝗍𝗁𝖾𝗋 𝖳𝗁𝖺𝗇 𝖳𝗁𝖾 𝖶𝖺𝗒 𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝖾𝖽 𝖠𝖻𝗈𝗏𝖾\n\n𝖣𝗈𝗇'𝗍 𝖴𝗌𝖾 𝖲𝗍𝗒𝗅𝗂𝗌𝗁 𝖥𝗈𝗇𝗍 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍\n\n𝖣𝗈𝗇'𝗍 𝖴𝗌𝖾 𝖲𝗒𝗆𝖻𝗈𝗅𝗌 𝖶𝗁𝗂𝗅𝖾 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝗅𝗂𝗄𝖾 (+:;'!-|...𝖾𝗍𝖼)\n\n𝖨𝖿 𝖸𝗈𝗎 𝖣𝗈𝗇'𝗍 𝖦𝖾𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝖠𝗇𝖽 𝖲𝖾𝗋𝗂𝖾𝗌⌛️\n𝖢𝗈𝗇𝗍𝖺𝖼𝗍 𝖠𝖽𝗆𝗂𝗇 - @hey_vro2004\n\n<u><b>𝖬𝗈𝗏𝗂𝖾𝗌 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖥𝗈𝗋𝗆𝖺𝗍</b></u>\n𝖪𝗎𝗋𝗎𝗉 𝖬𝗈𝗏𝗂𝖾❌\n𝖪𝗎𝗋𝗎𝗉 2021 ✅\n𝖪𝗀𝖿: 𝖢𝗁𝖺𝗉𝗍𝖾𝗋 2❌\n𝖪𝗀𝖿 𝖢𝗁𝖺𝗉𝗍𝖾𝗋 2✅\n\n<u><b>𝖲𝖾𝗋𝗂𝖾𝗌 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝗂𝗇𝗀 𝖱𝗎𝗅𝖾𝗌</b></u>\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝗌𝖾𝖺𝗌𝗈𝗇 1❌\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖲01✅\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖤𝗉𝗂𝗌𝗈𝖽𝖾 1❌\n𝖲𝗍𝖺𝗇𝗀𝖾𝗋 𝖳𝗁𝗂𝗇𝗀𝗌 𝖲01𝖤01✅\n\n 𝖢𝗅𝗂𝖼𝗄 𝖡𝖾𝗅𝗈𝗐 𝖡𝗎𝗍𝗍𝗈𝗇𝗌 𝖠𝗇𝖽 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖬𝗈𝗏𝗂𝖾𝗌 𝗈𝗋 𝖲𝖾𝗋𝗂𝖾𝗌 𝖨𝗇 𝖬𝗈𝗏𝗂𝖾𝗌 𝖦𝗋𝗈𝗎𝗉💡", reply_markup=InlineKeyboardMarkup(btn))
        
    elif query.data == "reqinfo":
        await query.answer("⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nᴀꜰᴛᴇʀ 10 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ\n\nɪꜰ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ꜱᴇᴇ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴍᴏᴠɪᴇ / sᴇʀɪᴇs ꜰɪʟᴇ, ʟᴏᴏᴋ ᴀᴛ ᴛʜᴇ ɴᴇxᴛ ᴘᴀɢᴇ\n\n❣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴄɪɴᴇᴍᴀʟᴀ.ᴄᴏᴍ", show_alert=True)

    elif query.data == "pat":
        btn = [[                
            InlineKeyboardButton('𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖦𝗋𝗈𝗎𝗉', url=f"https://t.me/color_films")
            ],[   
            InlineKeyboardButton('𝖻𝖺𝖼𝗄', callback_data='help')
            ]]
        await query.message.edit_text(text=f"1. 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐌𝐨𝐯𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩 - 𝐂𝐥𝐢𝐜𝐤 𝐇𝐞𝐫𝐞\n\n2. 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝖨𝗇 𝖤𝗇𝗀𝗅𝗂𝗌𝗁 𝖫𝖾𝗍𝗍𝖾𝗋𝗌. 𝖬𝗎𝗌𝗍 𝖥𝗈𝗅𝗅𝗈𝗐𝗂𝗇𝗀 𝖧𝗈𝗐 𝖳𝗈 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 ⚙\n\n3. 𝖸𝗈𝗎 𝖢𝖺𝗇 𝖢𝗅𝗂𝖼𝗄 𝖮𝗇 𝖳𝗁𝖾 𝖬𝗈𝗏𝗂𝖾 𝖡𝗎𝗍𝗍𝗈𝗇 𝖥𝗂𝗅𝖾𝗌 𝖨𝗇 𝖳𝗁𝖾 𝖰𝗎𝖺𝗅𝗂𝗍𝗒 𝖸𝗈𝗎 𝖶𝖺𝗇𝗍 𝖨𝗇 𝖬𝗒 𝖬𝖾𝗌𝗌𝖺𝗀𝖾 𝖳𝗁𝖺𝗍 𝖢𝗈𝗆𝖾𝗌 𝖠𝗌 𝖠 𝖱𝖾𝗉𝗅𝗒 𝖳𝗈 𝖳𝗁𝖾 𝗆𝗈𝗏𝗂𝖾 𝖸𝗈𝗎 𝖱𝖾𝗊𝗎𝖾𝗌𝗍𝖾𝖽🎯\n\n4. 𝖳𝗁𝖾𝗇 𝖢𝗅𝗂𝖼𝗄 𝖲𝗍𝖺𝗋𝗍 𝖡𝖾𝗅𝗈𝗐 𝖮𝗋 𝖠𝗎𝗍𝗈 𝖲𝗍𝖺𝗋𝗍. 𝖥𝗂𝗇𝖺𝗅𝗅𝗒 𝖸𝗈𝗁 𝖶𝗂𝗅𝗅 𝖦𝖾𝗍 𝖳𝗁𝖾 𝖥𝗂𝗅𝖾𝗌 🌎\n\n𝖭𝖡: 𝖸𝗈𝗎𝗋 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖮𝗇𝗅𝗒 𝖨𝗇 𝖬𝗒 𝖬𝗈𝗏𝗂𝖾𝗌 𝖦𝗋𝗈𝗎𝗉 𝖫𝗂𝗇𝗄 𝖢𝗁𝖾𝖼𝗄 𝗂𝗇 𝖠𝖻𝗈𝗏𝖾", reply_markup=InlineKeyboardMarkup(btn))
        
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('× ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ×', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton('Cᴏᴍᴍᴜɴɪᴛʏ', callback_data='but'),
            InlineKeyboardButton('Bᴏᴛ ɪɴғᴏ', callback_data='why')
        ], [
            InlineKeyboardButton('ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about')
        ],[
            InlineKeyboardButton('ᴀᴅᴍɪɴs ᴇxᴛʀᴀ ғᴇᴀᴛᴜʀᴇs', callback_data='machu')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer('Piracy Is Crime')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('ᴍ ғɪʟᴛᴇʀ', callback_data='manuelfilter'),
            InlineKeyboardButton('ᴀ ғɪʟᴛᴇʀ', callback_data='autofilter')
       ], [
            InlineKeyboardButton('ᴄᴏɴɴᴇᴄᴛ', callback_data='coct'),
            InlineKeyboardButton('sᴇᴛᴛɪɴɢs', callback_data='mmm')
       ], [
            InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ʀᴇǫᴜᴇsᴛ', callback_data='matt'),
            InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', callback_data='pat')
       ], [
            InlineKeyboardButton('ᴇxᴛʀᴀ ᴍᴏᴅᴇs', callback_data='pacha')
       ], [   
            InlineKeyboardButton('ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('sᴛᴀᴛᴜs', callback_data='stats'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ', callback_data='source')
        ], [
            InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('ᴄʟᴏsᴇ', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('ʙᴜᴛᴛᴏɴs', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "pacha":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('ᴀᴅᴍɪɴ', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXSERI_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='manuelfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "mmm":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SETIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )    
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
            )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('ᴀᴅᴍɪɴ', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "admin":
        if query.from_user.id not in ADMINS:
            await query.answer("മോനെ അത് ലോക്കാ ❌", show_alert=True)
            return
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='extra')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "machu":
        if query.from_user.id not in ADMINS:
            await query.answer("മോനെ അത് ലോക്കാ ❌", show_alert=True)
            return
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MCAHU_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "why":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ ʜᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('ʙᴏᴛ ᴏᴡɴᴇʀ', url=f"https://t.me/heyboy2k04")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "but":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ ʜᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('ɢʀᴏᴜᴘ ᴀᴅᴍɪɴ', url=f"https://t.me/heyboy2k04")
        ],[
            InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ʀᴇǫᴜᴇsᴛ ᴍᴏᴠɪᴇs', callback_data='dey')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.WHYER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )        
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)        
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
        await query.message.edit_text(
            text=script.STATUS_TXT2.format(total, tot, round(used_dbSize2, 2), round(free_dbSize2, 2), tota, round(used_dbSize3, 2), round(free_dbSize3, 2), users, chats, round(used_dbSize, 2), round(free_dbSize, 2)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
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
        await query.message.edit_text(
            text=script.STATUS_TXT2.format(total, tot, round(used_dbSize2, 2), round(free_dbSize2, 2), tota, round(used_dbSize3, 2), round(free_dbSize3, 2), users, chats, round(used_dbSize, 2), round(free_dbSize, 2)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "eng":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("Search on Google", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention} 👋<b><u> If you want to get the movie, follow the below…</u>👇\n\n<i>🔹Ask for correct spelling. (English Letters)\n\n🔸Ask for movies in English Lettes only.\n\n🔹Don't ask for unreleased movies.\n\n🔸 [Movie Name, Year, Language] Ask this way.\n\n🔹 Don't Use symbols while requesting movies. (+:;'!-`|...etc)\n\n🌏 Use the Google Button below for your movie details</b></i>", reply_markup=InlineKeyboardMarkup(btn))    

    elif query.data == "mal":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("Search on Google", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>നിങ്ങൾക്ക് സിനിമ കിട്ടണമെങ്കിൽ, താഴെ പറയുന്ന കാര്യങ്ങളിൽ ശ്രദ്ധിക്കുക...👇</u><I>\n\n🔹കറക്റ്റ് സ്പെല്ലിംഗിൽ ചോദിക്കുക. (ഇംഗ്ലീഷിൽ മാത്രം)\n\n🔸സിനിമകൾ ഇംഗ്ലീഷിൽ Type ചെയ്ത് മാത്രം ചോദിക്കുക.\n\n🔹റിലീസ് ആകാത്ത സിനിമകൾ ചോദിക്കരുത്.\n\n🔸[സിനിമയുടെ പേര്, വർഷം, ഭാഷ] ഈ രീതിയിൽ ചോദിക്കുക.\n\n🔹സിനിമ Request ചെയ്യുമ്പോൾ Symbols ഒഴിവാക്കുക. [+:;'*!-`&.. etc]\n\n🌏 നിങ്ങളുടെ സിനിമ വിശദാംശങ്ങൾക്കായി ചുവടെയുള്ള ഗൂഗിൾ ബട്ടൺ ഉപയോഗിക്കുക</b></i>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "tam":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("Search on Google", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]    
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>நீங்கள் திரைப்படத்தைப் பெற விரும்பினால், கீழே குறிப்பிடப்பட்டுள்ள விஷயங்களைப் பின்பற்றவும்...👇</u><i>\n\n🔹சரியான எழுத்துப்பிழை கேட்கவும். (ஆங்கிலத்தில் மட்டும்)\n\n🔸திரைப்படங்களை ஆங்கிலத்தில் டைப் செய்து மட்டும் கேட்கவும்.\n\n🔹வெளியாத திரைப்படங்களைக் கேட்காதீர்கள்.\n\n🔸 [திரைப்படத்தின் பெயர், ஆண்டு, மொழி] இந்த வழியில் கேளுங்கள்.\n\n🔹திரைப்படங்களைக் கோரும் போது சின்னங்களைத் தவிர்க்கவும். [+:;'*!-&.. etc]\n\n🌎 உங்கள் திரைப்பட விவரங்களுக்கு கீழே உள்ள Google பட்டனைப் பயன்படுத்தவும்</b></i>", reply_markup=InlineKeyboardMarkup(btn))
     
    elif query.data == "tel":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("Search on Google", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>రు సినిమాని పొందాలనుకుంటే, క్రింద పేర్కొన్న విషయాలను అనుసరించండి...👇</u><i>\n\n🔹సరైన స్పెల్లింగ్ కోసం అడగండి. (ఇంగ్లీష్‌లో మాత్రమే)\n\n🔸సినిమాలను ఆంగ్లంలో టైప్ చేసి మాత్రమే అడగండి.\n\n🔹విడుదల కాని సినిమాలను అడగవద్దు.\n\n🔸 [సినిమా పేరు, సంవత్సరం, భాష] ఈ విధంగా అడగండి.\n\n🔹సినిమాలను అభ్యర్థించేటప్పుడు చిహ్నాలను నివారించండి. [+:;'*!-&.. etc]\n\n🌎 మీ సినిమా వివరాల కోసం దిగువన ఉన్న Google బటన్‌ని ఉపయోగించండి</b></i>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "hin":
       xd = query.message.reply_to_message.text.replace(" ", "+")
       btn = [
           [
               InlineKeyboardButton("Search on Google", url=f"https://www.google.com/search?q={xd}"),
               InlineKeyboardButton("back", callback_data="nlang")
           ]
       ]
       await query.message.edit_text(text=f"Hey {query.from_user.mention}👋 <b><u>यदि आप मूवी प्राप्त करना चाहते हैं, तो नीचे दिए गए चरणों का पालन करें...</u><i>👇\n\n🔹सही वर्तनी के लिए पूछें। (केवल अंग्रेज़ी में)\n\n🔸फिल्में अंग्रेजी में टाइप करें और केवल पूछें।\n\n🔹अप्रकाशित फिल्मों के लिए न पूछें।\n\n🔸 [मूवी का नाम, वर्ष, भाषा] इस तरह पूछें।\n\n🔹फिल्मों का अनुरोध करते समय प्रतीकों से बचें। [+:;'*!-&.. आदि]\n\n🌎अपनी मूवी के विवरण के लिए नीचे दिए गए Google बटन का उपयोग करें</b></i>", reply_markup=InlineKeyboardMarkup(btn))
    
    elif query.data == "nlang":
       xd = query.message.reply_to_message.text.replace(" ", "+")  
       btn_duction = InlineKeyboardButton("𝖬𝗎𝗌𝗍 𝖱𝖾𝖺𝖽", callback_data="endio")
       btn_ductior = InlineKeyboardButton("𝖱𝗎𝗅𝖾𝗌", callback_data="oooi")  
       btn_dadduco = InlineKeyboardButton("𝖥𝗈𝗋𝗆𝖺𝗍", callback_data="minfo")
        
       intro_row = [btn_duction, btn_ductior, btn_dadduco]
       btn_eng = InlineKeyboardButton("ᴇɴɢ", callback_data="eng")
       btn_mal = InlineKeyboardButton("ᴍᴀʟ", callback_data="mal")
       btn_hin = InlineKeyboardButton("ʜɪɴ", callback_data="hin")
       btn_tam = InlineKeyboardButton("ᴛᴀᴍ", callback_data="tam")
       btn_tel = InlineKeyboardButton("ᴛᴇʟ", callback_data="tel")

       language_row = [btn_eng, btn_mal, btn_hin, btn_tam, btn_tel]
       btn_google = InlineKeyboardButton("𝗖𝗼𝗿𝗿𝗲𝗰𝘁 𝗦𝗽𝗲𝗹𝗹𝗶𝗻𝗴 (𝗀𝗈𝗈𝗀𝗅𝖾)", url=f"https://www.google.com/search?q={xd}")

       google_row = [btn_google]

       keyboard = InlineKeyboardMarkup(inline_keyboard=[intro_row, language_row, google_row])
 
       await query.message.edit_text(text=f"<b>❝ 𝖧𝖾𝗒 {query.from_user.mention} 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝖨𝗌 𝖶𝗋𝗈𝗇𝗀 ❞\n\n➪ 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝖮𝖿 𝖬𝗈𝗏𝗂𝖾 <u>𝖢𝗁𝖾𝖼𝗄 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 (𝗀𝗈𝗈𝗀𝗅𝖾)</u> 𝖡𝗎𝗍𝗍𝗈𝗇 𝖡𝖾𝗅𝗈𝗐 𝖶𝗂𝗅𝗅 𝖧𝖾𝗅𝗉 𝖸𝗈𝗎..𓁉\n\n➪ 𝖲𝖾𝗅𝖾𝖼𝗍 𝖸𝗈𝗎𝗋 𝖫𝖺𝗇𝗀𝖺𝗎𝗀𝖾 𝖥𝗋𝗈𝗆 𝖳𝗁𝖾 𝖫𝗂𝗌𝗍 𝖡𝖾𝗅𝗈𝗐 𝖳𝗈 𝖬𝗈𝗋𝖾 𝖧𝖾𝗅𝗉..☃︎</b>", reply_markup=keyboard)
         
    elif query.data == "minfo":
       await query.answer(
       text=(
            "🥇𝐆𝐨 𝐓𝐨 𝐆𝐨𝐨𝐠𝐥𝐞 𝐂𝐨𝐩𝐲 𝐂𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠 𝐢𝐧 𝗢𝗻𝗹𝘆 𝗘𝗻𝗴𝗹𝗶𝘀𝗵 𝗟𝗲𝘁𝘁𝗲𝗿𝘀 𝐀𝐧𝐝 𝐒𝐞𝐧𝐭 𝐢𝐭🎯\n\n"
            "𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐅𝐨𝐫𝐦𝐚𝐭:-\n"
            "Movies - Varisu 2023\n"
            "Series - Dark S01E01\n\n"
            "𝗠𝗼𝗿𝗲 𝗜𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻 :- 𝖢𝗅𝗂𝖼𝗄 𝖮𝗇 𝖳𝗁𝖾 𝖡𝗎𝗍𝗍𝗈𝗇 𝖨𝗇 𝖸𝗈𝗎𝗋 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾 𝖻𝖾𝗅𝗈𝗐🪝"
        ),
        show_alert=True
    )
    elif query.data == "endio": 
       await query.answer(f"കിട്ടോ.. ഉണ്ടോ.. തരുമോ.അയക്കാമോ. sent. ലിങ്ക്.. Plz. Movie... എന്നിങ്ങനെ ഉള്ള വാക്കുകൾ ഒഴിവാക്കുക. മൂവിയുടെ പേര് വർഷം ഭാഷ✍️. വേറേ ഒന്നും കൂട്ടി എഴുതരുത്.🔎",show_alert=True)

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('Piracy Is Crime')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Bot PM', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["botpm"] else '❌ No',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('IMDB', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('Piracy Is Crime')


async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                reqst_gle = search.replace(" ", "+")
                btn_duction = InlineKeyboardButton("𝖬𝗎𝗌𝗍 𝖱𝖾𝖺𝖽", callback_data="endio")
                btn_ductior = InlineKeyboardButton("𝖱𝗎𝗅𝖾𝗌", callback_data="oooi")  
                btn_dadduco = InlineKeyboardButton("𝖥𝗈𝗋𝗆𝖺𝗍", callback_data="minfo")
        
                intro_row = [btn_duction, btn_ductior, btn_dadduco]
                btn_eng = InlineKeyboardButton("ᴇɴɢ", callback_data="eng")
                btn_mal = InlineKeyboardButton("ᴍᴀʟ", callback_data="mal")
                btn_hin = InlineKeyboardButton("ʜɪɴ", callback_data="hin")
                btn_tam = InlineKeyboardButton("ᴛᴀᴍ", callback_data="tam")
                btn_tel = InlineKeyboardButton("ᴛᴇʟ", callback_data="tel")

                language_row = [btn_eng, btn_mal, btn_hin, btn_tam, btn_tel]
                btn_google = InlineKeyboardButton("𝗖𝗼𝗿𝗿𝗲𝗰𝘁 𝗦𝗽𝗲𝗹𝗹𝗶𝗻𝗴 (𝖦𝗈𝗈𝗀𝗅𝖾)", url=f"https://www.google.com/search?q={reqst_gle}")
                google_row = [btn_google]

                keyboard = InlineKeyboardMarkup(inline_keyboard=[intro_row, language_row, google_row])
                try:
                    k = await msg.reply_text(text=f"<b>❝ 𝖧𝖾𝗒 {msg.from_user.mention} 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝖨𝗌 𝖶𝗋𝗈𝗇𝗀 ❞\n\n➪ 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝖮𝖿 𝖬𝗈𝗏𝗂𝖾 <u>𝖢𝗁𝖾𝖼𝗄 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 (𝗀𝗈𝗈𝗀𝗅𝖾)</u> 𝖡𝗎𝗍𝗍𝗈𝗇 𝖡𝖾𝗅𝗈𝗐 𝖶𝗂𝗅𝗅 𝖧𝖾𝗅𝗉 𝖸𝗈𝗎..𓁉\n\n➪ 𝖲𝖾𝗅𝖾𝖼𝗍 𝖸𝗈𝗎𝗋 𝖫𝖺𝗇𝗀𝖺𝗎𝗀𝖾 𝖥𝗋𝗈𝗆 𝖳𝗁𝖾 𝖫𝗂𝗌𝗍 𝖡𝖾𝗅𝗈𝗐 𝖳𝗈 𝖬𝗈𝗋𝖾 𝖧𝖾𝗅𝗉..☃︎</b>", reply_markup=keyboard)
                    await asyncio.sleep(120)
                    await k.delete()
                    return       
                except Exception as e:
                    return 
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] ⊳ {file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if offset != "":
        try:
            offset = int(offset)
        except ValueError:
            offset = 0
    else:
        offset = 0
    
    if offset == 0:
        btn.append(
            [InlineKeyboardButton(text="1/1", callback_data="pages")]
        )
    else:
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
            InlineKeyboardButton(text="Nᴇxᴛ ⤷", callback_data=f"next_{req}_{key}_{offset}")]
       )
    
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>𝖥𝗂𝗅𝗆 : {search} \n𝖱𝖾𝗌𝗎𝗅𝗍𝗌 : {total_results}\n𝖴𝗌𝖾𝗋 : {message.from_user.mention}\n\n[Usᴇ Bᴇʟᴏᴡ Nᴇxᴛ Bᴜᴛᴛᴏɴ]</b>"
    if imdb and imdb.get('poster'):
        try:
            ok = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            ok = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            ok = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        ok = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    del_data = incol.find_one({"_id": "delete_time"})
    if del_data:
        time_seconds = del_data.get("time_seconds")        
        await asyncio.sleep(time_seconds)
        await msg.delete()
        await ok.delete()      
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(msg):
    mv_id = msg.id
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    try:
        movies = await get_poster(mv_rqst, bulk=True)
    except Exception as e:
        logger.exception(e)
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[        
        InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ ᴏɴ ɢᴏᴏɢʟᴇ​ 🔎', url=f"https://www.google.com/search?q={reqst_gle}")
        ]]        
        k = await msg.reply_text(
            text=("<b>I couldn't find the file you requested 😕\nTry to do the following...\n\n=> Request with correct spelling\n\n=> Don't ask movies that are not released in OTT platforms\n\n=> Try to ask in [MovieName, Language] this format.\n\n=> Use the button below to search on Google 😌</b>"),
            reply_markup=InlineKeyboardMarkup(button),
            reply_to_message_id=msg.id
        )                                           
        await msg.delete()
        await asyncio.sleep(60)
        await k.delete()      
        return
    movielist = []
    if not movies:
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[        
        InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ ᴏɴ ɢᴏᴏɢʟᴇ​ 🔎', url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        k = await msg.reply_text(
            text=("<b>I couldn't find the file you requested 😕\nTry to do the following...\n\n=> Request with correct spelling\n\n=> Don't ask movies that are not released in OTT platforms\n\n=> Try to ask in [MovieName, Language] this format.\n\n=> Use the button below to search on Google 😌</b>"),
            reply_markup=InlineKeyboardMarkup(button),
            reply_to_message_id=msg.id
        )                                           
        await msg.delete()
        await asyncio.sleep(60)
        await k.delete()
        return
    movielist = [movie.get('title') for movie in movies]
    SPELL_CHECK[mv_id] = movielist
    btn = [
        [
            InlineKeyboardButton(
                text=movie_name.strip(),
                callback_data=f"spolling#{reqstr1}#{k}",
            )
        ]
        for k, movie_name in enumerate(movielist)
    ]
    btn.append([InlineKeyboardButton(text="✘ ᴄʟᴏsᴇ ✘", callback_data=f'spolling#{reqstr1}#close_spellcheck')])
    spell_check_del = await msg.reply_text(
        text="I Cᴏᴜʟᴅɴ'ᴛ Fɪɴᴅ Aɴʏᴛʜɪɴɢ Rᴇʟᴀᴛᴇᴅ Tᴏ Tʜᴀᴛ. Dɪᴅ Yᴏᴜ Mᴇᴀɴ Aɴʏ Oɴᴇ Oғ Tʜᴇsᴇ?",
        reply_markup=InlineKeyboardMarkup(btn),
        reply_to_message_id=msg.id
    )
    await asyncio.sleep(90)
    await spell_check_del.delete()
    await msg.delete()

async def global_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            knd3 = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            await asyncio.sleep(60)
                            await knd3.delete()
                            await message.delete()

                        else:
                            button = eval(btn)
                            knd2 = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            await asyncio.sleep(60)
                            await knd2.delete()
                            await message.delete()

                    elif btn == "[]":
                        knd1 = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        await asyncio.sleep(60)
                        await knd1.delete()
                        await message.delete()

                    else:
                        button = eval(btn)
                        knd = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        await asyncio.sleep(60)
                        await knd.delete()
                        await message.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
        
async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
