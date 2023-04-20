#(c) Adarsh-Goel
import datetime
import motor.motor_asyncio


class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name,username, link_made, status):
        return dict(
            id=id,
            name=name,
            telegram_username=username,
            status=status,# status : login, ban, none
            link_made=link_made,
            join_date=datetime.date.today().isoformat()
        )

    async def add_user(self, id, first_name, last_name,username):
        if first_name == 'None': first_name = ''
        if last_name == 'None': last_name = ''
        user = self.new_user(id, f"{first_name} {last_name}", username, 0, "none")
        await self.col.insert_one(user)
        
    async def login_user(self, id, first_name, last_name, username):
        if await self.is_user_exist(id):
            await self.col.update_one({'id': int(id)}, {'$set': {'status': 'login'}})
        else:
            if first_name == 'None': first_name = ''
            if last_name == 'None': last_name = ''
            await self.new_user(self, id, f"{first_name} {last_name}", username, 0, 'login')

    async def check_user_status(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user['status']
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return True if user else False

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, id):
        await self.col.delete_many({'id': int(id)})
    
    async def ban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'status': 'ban'}})

    async def increase_link(self, id):
        user = await self.col.find_one({'id': int(id)})
        await self.col.update_one({'id': int(id)}, {'$set': {'link_made': user['link_made']+1 }})
    
    async def user_info(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user