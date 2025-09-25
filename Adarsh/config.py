"""
Configuration management with type safety and validation.
Modern approach to handling environment variables and bot settings.
"""

import os
from typing import List, Optional, Union
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """Type-safe bot configuration with validation."""
    
    # Required Telegram API credentials
    api_id: int
    api_hash: str
    bot_token: str
    bin_channel: int
    database_url: str
    
    # Bot behavior settings
    name: str = "FileStreamBot"
    sleep_threshold: int = 60
    workers: int = 4
    # max_concurrent_transmissions removed - not supported in current Pyrogram version
    
    # Web server settings
    port: int = 8080
    bind_address: str = "0.0.0.0"
    has_ssl: bool = False
    no_port: bool = False
    fqdn: Optional[str] = None
    
    # Admin and ownership
    owner_ids: List[int] = field(default_factory=list)
    owner_username: str = ""
    
    # Channel and subscription settings
    updates_channel: Optional[str] = None
    banned_channels: List[int] = field(default_factory=list)
    private_mode: bool = True
    subscription_password: Optional[str] = None
    
    # Usage limits for free users
    daily_file_limit: int = 5
    daily_download_limit: int = 4 * 1024 * 1024 * 1024  # 4GB in bytes
    
    # Heroku deployment
    on_heroku: bool = False
    app_name: Optional[str] = None
    
    # Monitoring
    ping_interval: int = 1200  # 20 minutes
    
    # Multi-client support
    multi_client: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_required_fields()
        self._setup_urls()
        self._parse_lists()
        
    def _validate_required_fields(self):
        """Validate that all required fields are properly set."""
        if not self.api_id or self.api_id == 0:
            raise ValueError("API_ID is required and must be a valid integer")
        if not self.api_hash:
            raise ValueError("API_HASH is required")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not self.bin_channel or self.bin_channel == 0:
            raise ValueError("BIN_CHANNEL is required and must be a valid channel ID")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
            
    def _setup_urls(self):
        """Setup web URLs based on configuration."""
        if not self.fqdn:
            self.fqdn = self.bind_address
            
        if self.on_heroku and self.app_name:
            self.fqdn = f"{self.app_name}.herokuapp.com"
            
        # Construct base URL
        if self.has_ssl:
            self.base_url = f"https://{self.fqdn}/"
        else:
            if self.on_heroku or self.no_port:
                self.base_url = f"https://{self.fqdn}/"
            else:
                self.base_url = f"http://{self.fqdn}:{self.port}/"
                
    def _parse_lists(self):
        """Parse string-based lists from environment variables."""
        # Already handled in from_env classmethod
        pass
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Create configuration from environment variables."""
        
        def get_required(key: str) -> str:
            value = os.getenv(key)
            if not value:
                raise ValueError(f"Required environment variable {key} is not set")
            return value
        
        def get_int(key: str, default: Optional[int] = None) -> int:
            value = os.getenv(key)
            if value:
                try:
                    return int(value)
                except ValueError:
                    if default is not None:
                        logger.warning(f"Invalid integer for {key}, using default: {default}")
                        return default
                    raise ValueError(f"Environment variable {key} must be an integer")
            if default is not None:
                return default
            raise ValueError(f"Required environment variable {key} is not set")
        
        def get_bool(key: str, default: bool = False) -> bool:
            value = os.getenv(key, "").lower()
            return value in ("true", "1", "yes", "on")
        
        def get_list_int(key: str, default: Optional[List[int]] = None) -> List[int]:
            value = os.getenv(key, "")
            if not value:
                return default or []
            try:
                return [int(x.strip()) for x in value.split() if x.strip().lstrip('-').isdigit()]
            except ValueError:
                logger.warning(f"Invalid integer list for {key}, using default")
                return default or []
        
        def parse_size(size_str: str) -> int:
            """Parse human-readable size to bytes."""
            if not size_str:
                return 4 * 1024 * 1024 * 1024  # 4GB default
                
            size_str = size_str.upper().strip()
            multipliers = {
                'B': 1,
                'KB': 1024,
                'MB': 1024 * 1024,
                'GB': 1024 * 1024 * 1024,
                'TB': 1024 * 1024 * 1024 * 1024
            }
            
            # Check for each suffix
            for suffix, multiplier in multipliers.items():
                if size_str.endswith(suffix):
                    try:
                        # Extract the numeric part
                        number_part = size_str[:-len(suffix)].strip()
                        if number_part:  # Make sure there's a number
                            number = float(number_part)
                            result = int(number * multiplier)
                            logger.info(f"✅ Parsed size '{size_str}' as {result} bytes")
                            return result
                    except ValueError as e:
                        logger.warning(f"Invalid number in size format: {size_str} - {e}")
                        break
            
            # Try to parse as plain number (bytes)
            try:
                result = int(size_str)
                logger.info(f"✅ Parsed size '{size_str}' as {result} bytes (plain number)")
                return result
            except ValueError:
                logger.warning(f"Invalid size format: {size_str}, using 4GB default")
                return 4 * 1024 * 1024 * 1024
        
        # Check for Heroku
        on_heroku = 'DYNO' in os.environ
        
        return cls(
            # Required fields
            api_id=get_int('API_ID'),
            api_hash=get_required('API_HASH'),
            bot_token=get_required('BOT_TOKEN'),
            bin_channel=get_int('BIN_CHANNEL'),
            database_url=get_required('DATABASE_URL'),
            
            # Optional fields with defaults
            name=os.getenv('BOT_NAME', 'FileStreamBot'),
            sleep_threshold=get_int('SLEEP_THRESHOLD', 60),
            workers=get_int('WORKERS', 4),
            # max_concurrent_transmissions removed - not supported
            
            # Web server
            port=get_int('PORT', 8080),
            bind_address=os.getenv('WEB_SERVER_BIND_ADDRESS', '0.0.0.0'),
            has_ssl=get_bool('HAS_SSL'),
            no_port=get_bool('NO_PORT'),
            fqdn=os.getenv('FQDN'),
            
            # Admin
            owner_ids=get_list_int('OWNER_ID'),
            owner_username=os.getenv('OWNER_USERNAME', ''),
            
            # Channel settings
            updates_channel=os.getenv('UPDATES_CHANNEL') if os.getenv('UPDATES_CHANNEL', 'None') != 'None' else None,
            banned_channels=get_list_int('BANNED_CHANNELS'),
            private_mode=get_bool('PRIVATE_MODE', True),
            subscription_password=os.getenv('SUB_PASS') if os.getenv('SUB_PASS', 'None') != 'None' else None,
            
            # Limits
            daily_file_limit=get_int('DAILY_LIMIT_FILE', 5),
            daily_download_limit=parse_size(os.getenv('DAILY_LIMIT_DOWNLOAD', '2GB')),  # Default to 2GB to match user's setting
            
            # Heroku
            on_heroku=on_heroku,
            app_name=os.getenv('APP_NAME') if on_heroku else None,
            
            # Monitoring
            ping_interval=get_int('PING_INTERVAL', 1200),
        )


# Global configuration instance
try:
    config = BotConfig.from_env()
    logger.info("✅ Configuration loaded successfully")
except Exception as e:
    logger.error(f"❌ Configuration error: {e}")
    raise


# Backward compatibility - maintain old Var class for existing code
class Var:
    """Backward compatibility wrapper."""
    
    def __getattr__(self, name: str):
        # Map old attribute names to new config
        mapping = {
            'API_ID': 'api_id',
            'API_HASH': 'api_hash',
            'BOT_TOKEN': 'bot_token',
            'BIN_CHANNEL': 'bin_channel',
            'DATABASE_URL': 'database_url',
            'NAME': 'name',
            'SLEEP_THRESHOLD': 'sleep_threshold',
            'WORKERS': 'workers',
            'PORT': 'port',
            'BIND_ADRESS': 'bind_address',  # Note: keeping the typo for compatibility
            'OWNER_ID': 'owner_ids',
            'OWNER_USERNAME': 'owner_username',
            'UPDATES_CHANNEL': 'updates_channel',
            'BANNED_CHANNELS': 'banned_channels',
            'PERIVEAT': 'private_mode',  # Note: keeping the typo
            'SUB_PASS': 'subscription_password',
            'DAILY_LIMIT_FILE': 'daily_file_limit',
            'DAILY_LIMIT_DOWNLOAD': 'daily_download_limit',
            'ON_HEROKU': 'on_heroku',
            'APP_NAME': 'app_name',
            'PING_INTERVAL': 'ping_interval',
            'MULTI_CLIENT': 'multi_client',
            'URL': 'base_url',
            'FQDN': 'fqdn',
            'HAS_SSL': 'has_ssl',
            'NO_PORT': 'no_port',
        }
        
        if name in mapping:
            return getattr(config, mapping[name])
        
        # Handle special cases
        if name == 'BIND_ADRESS':  # Typo in original code
            return config.bind_address
            
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# Maintain backward compatibility
Var = Var()