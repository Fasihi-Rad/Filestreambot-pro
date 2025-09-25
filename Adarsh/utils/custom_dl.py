"""
Custom ByteStreamer for efficient file streaming from Telegram.
Handles multi-client downloading with caching and session management.

Modified from: https://github.com/eyaadh/megadlbot_oss
Thanks to Eyaadh: https://github.com/eyaadh
"""
import math
import asyncio
import logging
from typing import Dict, Union, Optional, AsyncGenerator

from pyrogram import Client, utils, raw
from pyrogram.session import Session, Auth
from pyrogram.errors import AuthBytesInvalid, SessionPasswordNeeded, FloodWait
from pyrogram.file_id import FileId, FileType, ThumbnailSource

from Adarsh.vars import Var
from Adarsh.bot import work_loads
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import FileNotFound

logger = logging.getLogger(__name__)


class ByteStreamer:
    """
    Custom ByteStreamer for efficient file downloading and streaming.
    
    Features:
    - Client-specific caching for file properties
    - Automatic cache cleanup to prevent memory leaks
    - Media session management for different DCs
    - Efficient file streaming with chunked downloads
    
    Attributes:
        client: The Pyrogram client instance
        cached_file_ids: Cache of file IDs to reduce API calls
        clean_timer: Interval for cache cleanup (seconds)
    """
    
    def __init__(self, client: Client):
        """
        Initialize ByteStreamer with client and cache management.
        
        Args:
            client: Pyrogram client instance
        """
        self.client: Client = client
        self.cached_file_ids: Dict[int, FileId] = {}
        self.clean_timer: int = 30 * 60  # 30 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Start cache cleanup task
        self._cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
        logger.info(f"ByteStreamer initialized for client {client.name}")

    async def get_file_properties(self, message_id: int) -> FileId:
        """
        Get file properties with caching support.
        
        Args:
            message_id: Telegram message ID containing the file
            
        Returns:
            FileId object with file properties
            
        Raises:
            FileNotFound: If message or file not found
        """
        try:
            # Check cache first
            if message_id in self.cached_file_ids:
                logger.debug(f"Using cached file properties for message {message_id}")
                return self.cached_file_ids[message_id]
            
            # Generate and cache new properties
            file_id = await self._generate_file_properties(message_id)
            logger.debug(f"Cached new file properties for message {message_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error getting file properties for message {message_id}: {e}")
            raise

    async def _generate_file_properties(self, message_id: int) -> FileId:
        """
        Generate file properties from message ID.
        
        Args:
            message_id: Telegram message ID
            
        Returns:
            FileId object with file properties
            
        Raises:
            FileNotFound: If file not found in message
        """
        try:
            file_id = await get_file_ids(self.client, Var.BIN_CHANNEL, message_id)
            
            if not file_id:
                logger.error(f"No file found in message {message_id}")
                raise FileNotFound(f"Message {message_id} contains no downloadable file")
            
            # Cache the result
            self.cached_file_ids[message_id] = file_id
            logger.debug(f"Generated and cached file properties for message {message_id}")
            
            return file_id
            
        except Exception as e:
            logger.error(f"Error generating file properties for message {message_id}: {e}")
            raise

    async def generate_media_session(self, client: Client, file_id: FileId) -> Session:
        """
        Generate or retrieve media session for the appropriate DC.
        
        Args:
            client: Pyrogram client instance
            file_id: File ID object containing DC information
            
        Returns:
            Session object for the media file's DC
            
        Raises:
            AuthBytesInvalid: If authorization fails
            Exception: For other session creation errors
        """
        try:
            dc_id = file_id.dc_id
            
            # Check if session already exists
            media_session = client.media_sessions.get(dc_id)
            
            if media_session is not None:
                logger.debug(f"Using existing media session for DC {dc_id}")
                return media_session
            
            # Create new session if needed
            current_dc = await client.storage.dc_id()
            
            if dc_id != current_dc:
                # Create session for different DC
                media_session = await self._create_remote_session(client, dc_id)
            else:
                # Create session for current DC
                media_session = await self._create_local_session(client, dc_id)
            
            # Cache the session
            client.media_sessions[dc_id] = media_session
            logger.info(f"Created and cached media session for DC {dc_id}")
            
            return media_session
            
        except Exception as e:
            logger.error(f"Error generating media session for DC {file_id.dc_id}: {e}")
            raise

    async def _create_remote_session(self, client: Client, dc_id: int) -> Session:
        """
        Create media session for remote DC.
        
        Args:
            client: Pyrogram client
            dc_id: Data center ID
            
        Returns:
            Authorized session for the remote DC
            
        Raises:
            AuthBytesInvalid: If authorization fails after retries
        """
        test_mode = await client.storage.test_mode()
        auth = Auth(client, dc_id, test_mode)
        
        media_session = Session(
            client, dc_id, await auth.create(), test_mode, is_media=True
        )
        await media_session.start()
        
        # Export and import authorization with retries
        max_retries = 6
        for attempt in range(max_retries):
            try:
                exported_auth = await client.invoke(
                    raw.functions.auth.ExportAuthorization(dc_id=dc_id)
                )
                
                await media_session.send(
                    raw.functions.auth.ImportAuthorization(
                        id=exported_auth.id, 
                        bytes=exported_auth.bytes
                    )
                )
                
                logger.debug(f"Successfully authorized remote session for DC {dc_id}")
                break
                
            except AuthBytesInvalid as e:
                logger.warning(f"Auth attempt {attempt + 1} failed for DC {dc_id}: {e}")
                if attempt == max_retries - 1:
                    await media_session.stop()
                    raise
                await asyncio.sleep(1)  # Brief delay before retry
        
        return media_session

    async def _create_local_session(self, client: Client, dc_id: int) -> Session:
        """
        Create media session for current DC.
        
        Args:
            client: Pyrogram client
            dc_id: Data center ID
            
        Returns:
            Session for the current DC
        """
        media_session = Session(
            client,
            dc_id,
            await client.storage.auth_key(),
            await client.storage.test_mode(),
            is_media=True
        )
        await media_session.start()
        logger.debug(f"Created local media session for DC {dc_id}")
        return media_session


    @staticmethod
    async def get_location(file_id: FileId) -> Union[
        raw.types.InputPhotoFileLocation,
        raw.types.InputDocumentFileLocation,
        raw.types.InputPeerPhotoFileLocation,
    ]:
        """
        Get the appropriate input location for the file type.
        
        Args:
            file_id: FileId object containing file information
            
        Returns:
            Appropriate input location object for the file
        """
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            # Handle chat photos
            if file_id.chat_id > 0:
                # User profile photo
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, 
                    access_hash=file_id.chat_access_hash
                )
            else:
                # Chat/Channel photo
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )

            return raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )
            
        elif file_type == FileType.PHOTO:
            # Handle regular photos
            return raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        else:
            # Handle documents, videos, audio, etc.
            return raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )

    async def yield_file(
        self,
        file_id: FileId,
        client_index: int,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream file bytes with efficient chunked downloading.
        
        Args:
            file_id: FileId object for the file to stream
            client_index: Index of the client for load balancing
            offset: Starting byte offset
            first_part_cut: Bytes to cut from first chunk
            last_part_cut: Bytes to cut from last chunk  
            part_count: Total number of parts to download
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Bytes of the file content
            
        Raises:
            Exception: For download errors
        """
        client = self.client
        work_loads[client_index] += 1
        
        try:
            logger.debug(f"Starting file streaming with client {client_index}")
            
            # Get media session and location
            media_session = await self.generate_media_session(client, file_id)
            location = await self.get_location(file_id)
            
            current_part = 1
            current_offset = offset
            
            # Start downloading
            response = await media_session.send(
                raw.functions.upload.GetFile(
                    location=location, 
                    offset=current_offset, 
                    limit=chunk_size
                )
            )
            
            if not isinstance(response, raw.types.upload.File):
                logger.error(f"Unexpected response type: {type(response)}")
                return
            
            while True:
                chunk = response.bytes
                if not chunk:
                    logger.debug(f"No more data available at part {current_part}")
                    break
                
                # Apply cuts based on part position
                if part_count == 1:
                    # Single part - apply both cuts
                    yield chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    # First part - cut beginning
                    yield chunk[first_part_cut:]
                elif current_part == part_count:
                    # Last part - cut end
                    yield chunk[:last_part_cut]
                else:
                    # Middle part - no cuts
                    yield chunk
                
                current_part += 1
                current_offset += chunk_size
                
                # Check if we've downloaded all parts
                if current_part > part_count:
                    logger.debug(f"Completed all {part_count} parts")
                    break
                
                # Get next chunk
                try:
                    response = await media_session.send(
                        raw.functions.upload.GetFile(
                            location=location, 
                            offset=current_offset, 
                            limit=chunk_size
                        )
                    )
                except FloodWait as e:
                    logger.warning(f"FloodWait {e.value}s during download")
                    await asyncio.sleep(e.value)
                    continue
                except Exception as e:
                    logger.error(f"Error getting chunk at offset {current_offset}: {e}")
                    break
                    
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Network error during file streaming: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during file streaming: {e}")
        finally:
            # Always decrement workload
            work_loads[client_index] -= 1
            logger.debug(f"Finished streaming file with client {client_index}")

    async def _cache_cleanup_loop(self) -> None:
        """
        Periodic cache cleanup to prevent memory leaks.
        """
        try:
            while True:
                await asyncio.sleep(self.clean_timer)
                cache_size = len(self.cached_file_ids)
                self.cached_file_ids.clear()
                logger.info(f"Cleaned cache: removed {cache_size} entries")
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in cache cleanup loop: {e}")

    async def close(self) -> None:
        """
        Clean up resources and cancel background tasks.
        """
        try:
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            self.cached_file_ids.clear()
            logger.info(f"ByteStreamer for client {self.client.name} closed")
            
        except Exception as e:
            logger.error(f"Error closing ByteStreamer: {e}")

    def __len__(self) -> int:
        """Return number of cached file IDs."""
        return len(self.cached_file_ids)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()