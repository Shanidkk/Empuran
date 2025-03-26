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
from database.fsub_db import db as fsub_db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL
from utils import temp, load_fsub
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
        await load_fsub(self)
        # Start the bot and set up a periodic restart
        await super().start()
        
        # Load banned users and chats, set up other startup configurations
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)

        fsub_data = await fsub_db.get_all_fsub_chats()
        temp.REQ_FSUB_MODE1 = (await fsub_db.get_fsub_mode1()) == "req"
        temp.REQ_FSUB_MODE2 = (await fsub_db.get_fsub_mode2()) == "req" 
        if not self.req_link1 and temp.REQ_CHANNEL1:
            try:
                self.req_link1 = (await self.create_chat_invite_link(
                    int(temp.REQ_CHANNEL1), creates_join_request=temp.REQ_FSUB_MODE1
                )).invite_link
                await fsub_db.update_fsub_link1(temp.REQ_CHANNEL1, self.req_link1)
                print(f"Invite Link One set as {self.req_link1}")
            except Exception as e:
                logging.info(f"Check REQ_CHANNEL1 ID: {e}")

        if not self.req_link2 and temp.REQ_CHANNEL2:
            try:
                self.req_link2 = (await self.create_chat_invite_link(
                    int(temp.REQ_CHANNEL2), creates_join_request=temp.REQ_FSUB_MODE2
                )).invite_link
                await fsub_db.update_fsub_link2(temp.REQ_CHANNEL2, self.req_link2)
                print(f"Invite Link Two set as {self.req_link2}")
            except Exception as e:
                logging.info(f"Check REQ_CHANNEL2 ID: {e}")
            
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


if __name__ == "__main__":
    app = Bot()
    app.run()
