#(c) Fasihi-Rad
import datetime
import logging
from typing import Optional, Dict, AsyncIterator, Any
from contextlib import asynccontextmanager
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
import asyncio
from Adarsh.vars import Var

logger = logging.getLogger(__name__)


class Database:
    """Modern async database interface for user management with race condition protection"""
    
    def __init__(self, uri: str, database_name: str):
        """Initialize database connection with MongoDB"""
        self._client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col: AsyncIOMotorCollection = self.db.users
        self._user_locks: Dict[int, asyncio.Lock] = {}  # Store locks per user to prevent race conditions
        self._logger = logger.getChild(self.__class__.__name__)

    @asynccontextmanager
    async def _get_user_lock(self, user_id: int) -> AsyncIterator[asyncio.Lock]:
        """Get or create a lock for a specific user to prevent race conditions"""
        if user_id not in self._user_locks:
            self._user_locks[user_id] = asyncio.Lock()
        
        lock = self._user_locks[user_id]
        try:
            await lock.acquire()
            yield lock
        finally:
            lock.release()

    def new_user(self, user_id: int, name: str, username: Optional[str], 
                 link_made: int, status: str, link_date: str, total_download: int) -> Dict[str, Any]:
        """Create a new user document with proper structure"""
        return {
            'id': user_id,
            'name': name,
            'telegram_username': username,
            'status': status,  # status: subscribed, free, banned
            'link_made': link_made,
            'link_date': link_date,
            'total_download': total_download,
            'join_date': datetime.date.today().isoformat(),    
        }

    async def add_user(self, user_id: int, first_name: Optional[str], 
                       last_name: Optional[str], username: Optional[str]) -> None:
        """Add a new user to the database"""
        try:
            first_name = first_name or ''
            last_name = last_name or ''
            full_name = f"{first_name} {last_name}".strip()
            
            user = self.new_user(
                user_id, full_name, username, 0, "free", 
                datetime.date.today().isoformat(), 0
            )
            await self.col.insert_one(user)
            self._logger.info(f"Added new user: {user_id}")
        except Exception as e:
            self._logger.error(f"Failed to add user {user_id}: {e}")
            raise
        
    async def login_user(self, user_id: int, first_name: Optional[str], 
                        last_name: Optional[str], username: Optional[str]) -> None:
        """Login user - add if doesn't exist or update status to subscribed"""
        try:
            if await self.is_user_exist(user_id):
                await self.col.update_one(
                    {'id': user_id}, 
                    {'$set': {'status': 'subscribed'}}
                )
                self._logger.info(f"Updated user {user_id} to subscribed")
            else:
                first_name = first_name or ''
                last_name = last_name or ''
                full_name = f"{first_name} {last_name}".strip()
                
                user = self.new_user(
                    user_id, full_name, username, 0, 'subscribed', 
                    datetime.date.today().isoformat(), 0
                )
                await self.col.insert_one(user)
                self._logger.info(f"Added new subscribed user: {user_id}")
        except Exception as e:
            self._logger.error(f"Failed to login user {user_id}: {e}")
            raise

    async def check_user_status(self, user_id: int) -> Optional[str]:
        """Get user status (free, subscribed, banned)"""
        try:
            user = await self.col.find_one({'id': int(user_id)})
            return user['status'] if user else None
        except Exception as e:
            self._logger.error(f"Failed to check user status for {user_id}: {e}")
            return None
    
    async def is_user_exist(self, user_id: int) -> bool:
        """Check if user exists in database"""
        try:
            user = await self.col.find_one({'id': int(user_id)})
            return bool(user)
        except Exception as e:
            self._logger.error(f"Failed to check user existence for {user_id}: {e}")
            return False

    async def total_users_count(self) -> int:
        """Get total number of users"""
        try:
            return await self.col.count_documents({})
        except Exception as e:
            self._logger.error(f"Failed to count users: {e}")
            return 0

    async def get_all_users(self):
        """Get all users cursor - returns AsyncIOMotorCursor"""
        try:
            return self.col.find({})
        except Exception as e:
            self._logger.error(f"Failed to get all users: {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        """Delete user from database"""
        try:
            result = await self.col.delete_many({'id': int(user_id)})
            success = result.deleted_count > 0
            if success:
                self._logger.info(f"Deleted user: {user_id}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    async def ban_user(self, user_id: int) -> bool:
        """Ban user by setting status to banned"""
        try:
            result = await self.col.update_one(
                {'id': int(user_id)}, 
                {'$set': {'status': 'banned'}}
            )
            success = result.modified_count > 0
            if success:
                self._logger.info(f"Banned user: {user_id}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to ban user {user_id}: {e}")
            return False
        
    async def change_user_status(self, user_id: int, status: str) -> bool:
        """Change user status"""
        try:
            result = await self.col.update_one(
                {'id': int(user_id)}, 
                {'$set': {'status': status}}
            )
            success = result.modified_count > 0
            if success:
                self._logger.info(f"Changed user {user_id} status to {status}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to change user {user_id} status: {e}")
            return False

    async def increase_link(self, user_id: int) -> None:
        """Deprecated - use consume_user_limits instead"""
        self._logger.warning("increase_link is deprecated - use consume_user_limits instead")
    
    async def add_download_size(self, user_id: int, size: int) -> None:
        """Deprecated - use consume_user_limits instead"""
        self._logger.warning("add_download_size is deprecated - use consume_user_limits instead")
    
    async def user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get complete user information"""
        try:
            user = await self.col.find_one({'id': int(user_id)})
            return user
        except Exception as e:
            self._logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    async def check_user_link_count(self, user_id: int) -> int:
        """Get user's current link count for today"""
        try:
            user = await self.col.find_one({'id': int(user_id)})
            return user['link_made'] if user else 0
        except Exception as e:
            self._logger.error(f"Failed to check link count for {user_id}: {e}")
            return 0
    
    async def user_link_count_zero(self, user_id: int) -> bool:
        """Reset user's link count to zero"""
        try:
            result = await self.col.update_one(
                {'id': int(user_id)}, 
                {'$set': {'link_made': 0}}
            )
            return result.modified_count > 0
        except Exception as e:
            self._logger.error(f"Failed to reset link count for {user_id}: {e}")
            return False
        
    async def user_link_size_zero(self, user_id: int) -> bool:
        """Reset user's download size to zero"""
        try:
            result = await self.col.update_one(
                {'id': int(user_id)}, 
                {'$set': {'total_download': 0}}
            )
            return result.modified_count > 0
        except Exception as e:
            self._logger.error(f"Failed to reset download size for {user_id}: {e}")
            return False
    async def user_link_date_update(self, user_id: int) -> bool:
        """Update user's link date to today"""
        try:
            result = await self.col.update_one(
                {'id': int(user_id)}, 
                {'$set': {'link_date': datetime.date.today().isoformat()}}
            )
            return result.modified_count > 0
        except Exception as e:
            self._logger.error(f"Failed to update link date for {user_id}: {e}")
            return False

    async def update_user_link_limit(self, user_id: int) -> None:
        """Reset user limits if it's a new day - DEPRECATED, limits are auto-reset in check_user_link_limit"""
        try:
            user = await self.col.find_one({'id': int(user_id)})
            if not user:
                return
                
            if user['link_date'] != datetime.date.today().isoformat():
                await self.user_link_count_zero(user_id)
                await self.user_link_size_zero(user_id)
                await self.user_link_date_update(user_id)
        except Exception as e:
            self._logger.error(f"Failed to update link limit for {user_id}: {e}")

    async def check_user_link_limit(self, user_id: int, file_size: int) -> bool | int:
        """Thread-safe method to check and update user limits atomically
        
        Returns:
            True: User can download the file
            False: User has exceeded daily limits
            2: File is too large (exceeds daily limit entirely)
        """
        user_id = int(user_id)
        
        try:
            # Use user-specific lock to prevent race conditions
            async with self._get_user_lock(user_id):
                user = await self.col.find_one({'id': user_id})
                if not user:
                    self._logger.warning(f"User {user_id} not found during limit check")
                    return False
                    
                if user['status'] != 'free':
                    # Subscribed users have no limits
                    return True
                    
                today = datetime.date.today().isoformat()
                
                # Check if it's a new day - reset limits
                if user['link_date'] != today:
                    # Reset daily limits for new day
                    await self.col.update_one(
                        {'id': user_id},
                        {
                            '$set': {
                                'link_made': 0,
                                'total_download': 0,
                                'link_date': today
                            }
                        }
                    )
                    user['link_made'] = 0
                    user['total_download'] = 0
                    self._logger.info(f"Reset daily limits for user {user_id}")
                
                # Check if file is too big (exceeds daily limit entirely)
                if file_size > Var.DAILY_LIMIT_DOWNLOAD:
                    self._logger.info(f"File too large for user {user_id}: {file_size} > {Var.DAILY_LIMIT_DOWNLOAD}")
                    return 2
                    
                # Check daily limits
                if user['link_made'] >= Var.DAILY_LIMIT_FILE:
                    self._logger.info(f"User {user_id} exceeded file count limit: {user['link_made']} >= {Var.DAILY_LIMIT_FILE}")
                    return False
                    
                if user['total_download'] + file_size > Var.DAILY_LIMIT_DOWNLOAD:
                    self._logger.info(f"User {user_id} would exceed download limit: {user['total_download']} + {file_size} > {Var.DAILY_LIMIT_DOWNLOAD}")
                    return False
                    
                return True
                
        except Exception as e:
            self._logger.error(f"Failed to check user limits for {user_id}: {e}")
            return False
    
    async def consume_user_limits(self, user_id: int, file_size: int) -> bool:
        """Atomically consume user limits - call this after successful file processing
        
        Args:
            user_id: User ID to update limits for
            file_size: Size of file that was processed
            
        Returns:
            bool: True if limits were successfully consumed
        """
        user_id = int(user_id)
        
        try:
            async with self._get_user_lock(user_id):
                result = await self.col.update_one(
                    {'id': user_id},
                    {
                        '$inc': {
                            'link_made': 1,
                            'total_download': file_size
                        },
                        '$set': {
                            'link_date': datetime.date.today().isoformat()
                        }
                    }
                )
                
                success = result.modified_count > 0
                if success:
                    self._logger.info(f"Consumed limits for user {user_id}: +1 file, +{file_size} bytes")
                else:
                    self._logger.warning(f"Failed to consume limits for user {user_id} - user not found")
                    
                return success
                
        except Exception as e:
            self._logger.error(f"Failed to consume limits for user {user_id}: {e}")
            return False
            
    async def close(self) -> None:
        """Close database connection and cleanup resources"""
        try:
            if self._client:
                self._client.close()
                self._logger.info("Database connection closed")
        except Exception as e:
            self._logger.error(f"Error closing database connection: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        await self.close()
         