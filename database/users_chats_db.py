# https://github.com/odysseusmax/animated-lamp/blob/master/bot/database/database.py
import motor.motor_asyncio
from info import DATABASE_NAME, DATABASE_URI, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS, P_TTI_SHOW_OFF, SINGLE_BUTTON, SPELL_CHECK_REPLY, PROTECT_CONTENT
from datetime import datetime


class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.group
        self.req = self.db.requests
        self.fsub1 = self.db.fsub1
        self.fsub2 = self.db.fsub2
        self.chat_col = self.db.chatcol
        self.chat_col2 = self.db.chatcol2


    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )


    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})


    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    


    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)
    

    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    

    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        
    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})
        
    
    async def get_settings(self, id):
        default = {
            'button': SINGLE_BUTTON,
            'botpm': P_TTI_SHOW_OFF,
            'file_secure': PROTECT_CONTENT,
            'imdb': IMDB,
            'spell_check': SPELL_CHECK_REPLY,
            'welcome': MELCOW_NEW_USERS,
            'template': IMDB_TEMPLATE
        }
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', default)
        return default
    

    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
    

    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    

    async def get_all_chats(self):
        return self.grp.find({})


    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def add_req(self, user_id, chat_id):
        await self.req.update_one(
            {"user_id": user_id},
            {"$push": {"requests": {"chat_id": chat_id}}},
            upsert=True
        )
        
    async def get_req(self, user_id, chat_id):
        user = await self.req.find_one({"user_id": user_id})
        if user:
            return next((r for r in user["requests"] if r["chat_id"] == chat_id), None)

    async def delete_req(self, user_id, chat_id):
        await self.req.update_one(
            {"user_id": user_id},
            {"$pull": {"requests": {"chat_id": chat_id}}}
        )

    async def delete_all_reqs(self, chat_id=None):
        if chat_id:
            await self.req.update_many({}, {"$pull": {"requests": {"chat_id": chat_id}}})
        else:
            await self.req.delete_many({})

    async def get_all_reqs_count(self, chat_id=None):
        if chat_id:
            return await self.req.count_documents({"requests.chat_id": chat_id})
        return await self.req.count_documents({})

    async def get_loadout(self):
        chat1 = await self.chat_col.find_one({}) or {}
        chat2 = await self.chat_col2.find_one({}) or {}

        return {
            "channel1": {
                "id": chat1.get("chat_id"),
                "link": chat1.get("invite_link"),
            },
            "channel2": {
                "id": chat2.get("chat_id"),
                "link": chat2.get("invite_link"),
            }
        }
    
    async def add_fsub_chat(self, chat_id, link):
        try:
            await self.chat_col.delete_many({})
            await db.delete_all_reqs(chat_id)
            # Save the timestamp along with the chat_id
            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.chat_col.insert_one({"chat_id": chat_id, "invite_link": link, "switch_time": switch_time})
        except Exception as e:
            pass
            
    async def get_fsub_chat(self):
        return await self.chat_col.find_one({})

    async def delete_fsub_chat(self):
        await self.chat_col.delete_many({})
        await db.delete_all_reqs(chat_id)

    async def add_fsub_chat2(self, chat_id, link):
        try:
            await self.chat_col2.delete_many({})
            await self.req_two.delete_many({})
            switch_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            await self.chat_col2.insert_one({"chat_id": chat_id, "invite_link": link, "switch_time": switch_time})
        except Exception as e:
            pass

    async def get_fsub_chat2(self):
        return await self.chat_col2.find_one({})

    async def delete_fsub_chat2(self):
        await self.chat_col2.delete_many({})
        await self.req_two.delete_many({})

    async def update_fsub_link1(self, chat_id, new_link):
        try:
            result = await self.chat_col.update_one(
                {"chat_id": chat_id},  # Find the document by chat_id
                {"$set": {"invite_link": new_link}}  # Update the invite link
            )
            return result.modified_count > 0  # Return True if updated
        except Exception as e:
            print(f"Error updating invite link: {e}")
            return False

    async def update_fsub_link2(self, chat_id, new_link):
        try:
            result = await self.chat_col2.update_one(
                {"chat_id": chat_id},  # Find the document by chat_id
                {"$set": {"invite_link": new_link}}  # Update the invite link
            )
            return result.modified_count > 0  # Return True if updated
        except Exception as e:
            print(f"Error updating invite link: {e}")
            return False
        
    async def get_fsub_mode1(self):
        return await self.fsub1.find_one({})

    async def add_fsub_mode1(self, mode):
        try:
            await self.fsub1.delete_many({})
            await self.fsub1.insert_one({"mode": mode})
        except:
            pass

    async def get_fsub_mode2(self):
        return await self.fsub2.find_one({})

    async def add_fsub_mode2(self, mode):
        try:
            await self.fsub2.delete_many({})
            await self.fsub2.insert_one({"mode": mode})
        except:
            pass
        
        
db = Database(DATABASE_URI, DATABASE_NAME)
