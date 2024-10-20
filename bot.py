import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL
from utils import temp, load_datas
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from plugins.commands import restarti
import os 
import sys
from dotenv import load_dotenv
from pyromod import listen 

load_dotenv("./dynamic.env", override=True, encoding="utf-8")

async def restart_bot(bot):
    progress_document = restarti.find_one({"_id": "frestart"})
    if progress_document:
        last_restart = progress_document.get("restart")
        if last_restart == "on":
            restarti.update_one(
                {"_id": "frestart"},
                {"$set": {"restart": "off"}},
                upsert=True
            )
            os.execl(sys.executable, sys.executable, "bot.py")
        else:
            return 


class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        await load_datas()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)        
        if temp.REQ_CHANNEL1:  
            try:
                _link = await self.create_chat_invite_link(chat_id=int(temp.REQ_CHANNEL1), creates_join_request=True)
                self.req_link1 = _link.invite_link
                print(f"Invite Link One set as {self.req_link1}")
            except Exception as e:
                logging.info(f"Make Sure REQ_CHANNEL 1 ID is correct or {e}")
        if temp.REQ_CHANNEL2:
            try:
                _link = await self.create_chat_invite_link(chat_id=int(temp.REQ_CHANNEL2), creates_join_request=True)
                self.req_link2 = _link.invite_link
                print(f"Invite Link Two set as {self.req_link2}")
            except Exception as e:
                logging.info(f"Make Sure REQ_CHANNEL 2 ID is correct or {e}")

        fsub1 = await db.get_fsub_mode1()
        if fsub1:
            fsub1 = fsub1['mode']
            if fsub1 == "req":
                temp.REQ_FSUB_MODE1 = True
            else:
                temp.REQ_FSUB_MODE1 = False
        else:
            temp.REQ_FSUB_MODE1 = False
        fsub2 = await db.get_fsub_mode2()
        if fsub2:
            fsub2 = fsub2['mode']
            if fsub2 == "req":
                temp.REQ_FSUB_MODE2 = True
            else:
                temp.REQ_FSUB_MODE2 = False
        else:
            temp.REQ_FSUB_MODE2 = False
            
        await self.send_message(chat_id=int(6446790411), text="restarted ❤️‍🩹")        
        
        
    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()
