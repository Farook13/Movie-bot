import logging
import logging.config
import os
import ntplib
import time
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR
from utils import temp

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

class Bot(Client):

    def __init__(self):
        super().__init__(
            session_name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        # Delete existing session file
        session_file = f"{SESSION}.session"
        if os.path.exists(session_file):
            os.remove(session_file)
            logging.info(f"Deleted old session file: {session_file}")

        # Sync time with NTP server
        try:
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request('pool.ntp.org')
            current_time = response.tx_time
            time_diff = current_time - time.time()
            if abs(time_diff) > 5:  # Adjust if drift > 5 seconds
                logging.info(f"Adjusting time by {time_diff} seconds")
                # Patch time (note: this is a hack)
                time.time = lambda: time.time() + time_diff
        except Exception as e:
            logging.warning(f"Failed to sync time: {e}")

        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

app = Bot()
app.run()