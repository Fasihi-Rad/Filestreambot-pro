#(c) Fasihi-Rad
import datetime
import motor.motor_asyncio
from Adarsh.vars import Var


class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name,username, link_made, status, link_date, total_download):
        return dict(
            id=id,
            name=name,
            telegram_username=username,
            status=status,# status : subscribed, free, banned
            link_made=link_made,
            link_date=link_date,
            total_download=total_download,
            join_date=datetime.date.today().isoformat(),    
        )

    async def add_user(self, id, first_name, last_name, username):
        if first_name == None : first_name = ''
        if last_name == None : last_name = ''
        user = self.new_user(id, f"{first_name} {last_name}", username, 0, "free", datetime.date.today().isoformat(), 0)
        await self.col.insert_one(user)
        
    async def login_user(self, id, first_name, last_name, username):
        if await self.is_user_exist(id):
            await self.col.update_one({'id': int(id)}, {'$set': {'status': 'subscribed'}})
        else:
            if first_name == None: first_name = ''
            if last_name == None: last_name = ''
            await self.new_user(self, id, f"{first_name} {last_name}", username, 0, 'subscribed', datetime.date.today().isoformat(), 0)

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
        await self.col.update_one({'id': int(id)}, {'$set': {'status': 'banned'}})

    async def increase_link(self, id):
        user = await self.col.find_one({'id': int(id)})
        await self.col.update_one({'id': int(id)}, {'$set': {'link_made': user['link_made']+1 }})
    
    async def add_download_size(self, id, size):
        user = await self.col.find_one({'id': int(id)})
        await self.col.update_one({'id': int(id)}, {'$set': {'total_download': user['total_download']+size }})
    
    async def user_info(self, id):
        user = False
        user = await self.col.find_one({'id': int(id)})
        return user
    
    async def check_user_link_count(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user['link_made']
    
    async def user_link_count_zero(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'link_made': 0 }})
        
    async def user_link_size_zero(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'total_download': 0 }})
        
    async def user_link_date_update(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'link_date': datetime.date.today().isoformat() }})

    async def update_user_link_limit(self, id):
        user = await self.col.find_one({'id': int(id)})
        if user['link_date'] == datetime.date.today().isoformat():
            return
        else:
            await self.user_link_count_zero(id)
            await self.user_link_size_zero(id)

    async def check_user_link_limit(self, id, file_size):
        user = await self.col.find_one({'id': int(id)})
        if user['status'] == 'free':
            if user['link_date'] == datetime.date.today().isoformat():
                if user['link_made'] >= Var.DAILY_LIMIT_FILE or user['total_download'] + file_size >= Var.DAILY_LIMIT_DOWNLOAD:
                    return False
                else:
                    return True
            elif file_size > Var.DAILY_LIMIT_DOWNLOAD:
                return 2
            else:
                await self.user_link_count_zero(id)
                await self.user_link_size_zero(id)
                await self.user_link_date_update(id)
                return True
        elif user['status'] == 'subscribed':
            await self.user_link_date_update(id)
            return True
         