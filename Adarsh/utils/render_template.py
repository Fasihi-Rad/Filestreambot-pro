"""
Template rendering utilities for web interface.
Handles video streaming, audio playbook, and file download pages.
"""
import asyncio
import urllib.parse
import logging
from typing import Optional
from pathlib import Path

import aiofiles
import aiohttp
from aiohttp import ClientTimeout

from Adarsh.vars import Var
from Adarsh.bot import StreamBot
from Adarsh.utils.human_readable import byte_to_human_read
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import InvalidHash

logger = logging.getLogger(__name__)

# Template paths
TEMPLATE_DIR = Path("Adarsh/template")
VIDEO_TEMPLATE = TEMPLATE_DIR / "req.html"
DOWNLOAD_TEMPLATE = TEMPLATE_DIR / "dl.html"

# HTTP client timeout settings
TIMEOUT = ClientTimeout(total=30, connect=10)


async def render_page(message_id: int, secure_hash: str) -> str:
    """
    Render appropriate page based on file type.
    
    Args:
        message_id: Telegram message ID
        secure_hash: Security hash for validation
        
    Returns:
        HTML content as string
        
    Raises:
        InvalidHash: If security hash validation fails
        FileNotFoundError: If template files are missing
        Exception: For other rendering errors
    """
    try:
        # Get file data and validate hash
        file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(message_id))
        
        if not file_data:
            logger.error(f"File data not found for message ID: {message_id}")
            raise FileNotFoundError(f"Message with ID {message_id} not found")
        
        # Validate security hash
        if file_data.unique_id[:6] != secure_hash:
            logger.warning(f"Hash mismatch - provided: {secure_hash}, expected: {file_data.unique_id[:6]}")
            logger.debug(f"Invalid hash for message ID: {message_id}")
            raise InvalidHash("Security hash validation failed")
        
        # Build file URL
        file_url = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(message_id)}')
        
        # Determine file type and render appropriate template
        mime_type = str(file_data.mime_type).lower()
        primary_type = mime_type.split('/')[0].strip() if '/' in mime_type else mime_type
        
        logger.info(f"Rendering page for message {message_id}, type: {primary_type}")
        
        if primary_type == 'video':
            return await render_media_template(file_data.file_name, file_url, 'video', 'Watch')
        elif primary_type == 'audio':
            return await render_media_template(file_data.file_name, file_url, 'audio', 'Listen')
        else:
            return await render_download_template(file_data.file_name, file_url)
            
    except InvalidHash:
        raise  # Re-raise InvalidHash without logging as error
    except Exception as e:
        logger.error(f"Error rendering page for message {message_id}: {e}")
        raise


async def render_media_template(filename: str, file_url: str, media_type: str, action: str) -> str:
    """
    Render template for media files (video/audio).
    
    Args:
        filename: Name of the media file
        file_url: Direct URL to the file
        media_type: Type of media ('video' or 'audio')
        action: Action word for the page ('Watch' or 'Listen')
        
    Returns:
        Rendered HTML content
        
    Raises:
        FileNotFoundError: If template file is missing
        Exception: For template rendering errors
    """
    try:
        if not VIDEO_TEMPLATE.exists():
            raise FileNotFoundError(f"Video template not found: {VIDEO_TEMPLATE}")
        
        async with aiofiles.open(VIDEO_TEMPLATE, 'r', encoding='utf-8') as template_file:
            template_content = await template_file.read()
        
        # Replace template variables
        heading = f'{action} {filename}'
        html = template_content.replace('tag', media_type) % (heading, filename, file_url)
        
        logger.debug(f"Rendered {media_type} template for: {filename}")
        return html
        
    except Exception as e:
        logger.error(f"Error rendering {media_type} template: {e}")
        raise


async def render_download_template(filename: str, file_url: str) -> str:
    """
    Render template for file downloads.
    
    Args:
        filename: Name of the file
        file_url: Direct URL to the file
        
    Returns:
        Rendered HTML content
        
    Raises:
        FileNotFoundError: If template file is missing
        Exception: For template rendering errors
    """
    try:
        if not DOWNLOAD_TEMPLATE.exists():
            raise FileNotFoundError(f"Download template not found: {DOWNLOAD_TEMPLATE}")
        
        # Get file size from headers
        file_size_str = await get_file_size_from_url(file_url)
        
        async with aiofiles.open(DOWNLOAD_TEMPLATE, 'r', encoding='utf-8') as template_file:
            template_content = await template_file.read()
        
        # Replace template variables
        heading = f'Download {filename}'
        html = template_content % (heading, filename, file_url, file_size_str)
        
        logger.debug(f"Rendered download template for: {filename}")
        return html
        
    except Exception as e:
        logger.error(f"Error rendering download template: {e}")
        raise


async def get_file_size_from_url(url: str) -> str:
    """
    Get human-readable file size from URL headers.
    
    Args:
        url: File URL to check
        
    Returns:
        Human-readable file size string
    """
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.head(url) as response:
                if response.status == 200:
                    content_length = response.headers.get('Content-Length')
                    if content_length and content_length.isdigit():
                        file_size = int(content_length)
                        return byte_to_human_read(file_size)
                
                logger.warning(f"Could not determine file size from headers for URL: {url}")
                return "Unknown size"
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout while getting file size for URL: {url}")
        return "Unknown size"
    except Exception as e:
        logger.error(f"Error getting file size from URL {url}: {e}")
        return "Unknown size"


# Template validation on import
async def validate_templates() -> bool:
    """
    Validate that all required templates exist.
    
    Returns:
        True if all templates are valid
    """
    try:
        missing_templates = []
        
        if not VIDEO_TEMPLATE.exists():
            missing_templates.append(str(VIDEO_TEMPLATE))
        if not DOWNLOAD_TEMPLATE.exists():
            missing_templates.append(str(DOWNLOAD_TEMPLATE))
            
        if missing_templates:
            logger.error(f"Missing template files: {missing_templates}")
            return False
            
        logger.info("All template files validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error validating templates: {e}")
        return False
