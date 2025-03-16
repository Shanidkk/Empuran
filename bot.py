import logging
import logging.config
import asyncio
import os
import sys
from datetime import timedelta
import pymongo

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
from dotenv import load_dotenv
from pyromod import listen 
from pyrogram import utils as pyroutils

load_dotenv("./dynamic.env", override=True, encoding="utf-8")

pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

# Define the restart interval in hours (e.g., 5 hours)
RESTART_INTERVAL_HOURS = 168

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
        self.restart_task = None  # Background task for scheduled restarts

    async def start(self, **kwargs):
        # Start the bot and set up a periodic restart
        await super().start()
        await self.setup_periodic_restart()
        
        # Load banned users and chats, set up other startup configurations
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
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
                logging.info(f"Make sure REQ_CHANNEL 1 ID is correct or {e}")

        if temp.REQ_CHANNEL2:
            try:
                _link = await self.create_chat_invite_link(chat_id=int(temp.REQ_CHANNEL2), creates_join_request=True)
                self.req_link2 = _link.invite_link
                print(f"Invite Link Two set as {self.req_link2}")
            except Exception as e:
                logging.info(f"Make sure REQ_CHANNEL 2 ID is correct or {e}")

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

    async def setup_periodic_restart(self):
        # Cancel any existing restart task and start a new one
        if self.restart_task:
            self.restart_task.cancel()
        self.restart_task = asyncio.create_task(self.periodic_restart())

    async def periodic_restart(self):
        # Periodic restart logic
        while True:
            logging.info(f"Scheduled restart in {RESTART_INTERVAL_HOURS} hours.")
            await asyncio.sleep(RESTART_INTERVAL_HOURS * 3600)  # Convert hours to seconds
            await self.restart_bot()

    async def restart_bot(self):
        # Restart the bot
        logging.info("Restarting bot as scheduled.")
        os.execl(sys.executable, sys.executable, "bot.py")  # Restart the bot

    async def stop(self, *args):
        # Cancel the periodic restart task when stopping the bot
        if self.restart_task:
            self.restart_task.cancel()
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially."""
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1

# Run the bot
app = Bot()
app.run()
