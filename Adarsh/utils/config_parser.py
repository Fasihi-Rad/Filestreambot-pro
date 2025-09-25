"""
Advanced configuration parser for multi-token and environment management.
Supports parsing tokens from environment variables and config files.
"""
import os
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class TokenParser:
    """Enhanced token parser with support for multiple configuration sources."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize TokenParser.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.tokens: Dict[int, str] = {}
        self.config_file = Path(config_file) if config_file else None
        logger.debug(f"TokenParser initialized with config file: {self.config_file}")

    def parse_from_env(self) -> Dict[int, str]:
        """
        Parse multi-client tokens from environment variables.
        
        Looks for environment variables matching pattern: MULTI_TOKEN*
        Example: MULTI_TOKEN1, MULTI_TOKEN2, etc.
        
        Returns:
            Dict mapping client index to bot token
        """
        try:
            # Get all environment variables starting with MULTI_TOKEN
            multi_token_vars = [
                (key, value) for key, value in os.environ.items() 
                if key.startswith("MULTI_TOKEN") and value.strip()
            ]
            
            # Sort by variable name to ensure consistent ordering
            multi_token_vars.sort(key=lambda x: x[0])
            
            # Create mapping with 1-based indexing
            self.tokens = {
                index + 1: token.strip()
                for index, (_, token) in enumerate(multi_token_vars)
            }
            
            logger.info(f"Parsed {len(self.tokens)} tokens from environment variables")
            if self.tokens:
                logger.debug(f"Token indices: {list(self.tokens.keys())}")
                
            return self.tokens
            
        except Exception as e:
            logger.error(f"Error parsing tokens from environment: {e}")
            return {}

    def parse_from_file(self) -> Dict[int, str]:
        """
        Parse tokens from configuration file.
        
        Expected format (one token per line):
        token1_here
        token2_here
        
        Returns:
            Dict mapping client index to bot token
        """
        if not self.config_file or not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            tokens = {}
            for index, line in enumerate(lines, 1):
                token = line.strip()
                if token and not token.startswith('#'):  # Skip empty lines and comments
                    tokens[index] = token
                    
            logger.info(f"Parsed {len(tokens)} tokens from config file: {self.config_file}")
            self.tokens = tokens
            return tokens
            
        except Exception as e:
            logger.error(f"Error parsing tokens from file {self.config_file}: {e}")
            return {}

    def get_all_tokens(self) -> Dict[int, str]:
        """
        Get all parsed tokens.
        
        Returns:
            Dict mapping client index to bot token
        """
        return self.tokens.copy()

    def get_token(self, index: int) -> Optional[str]:
        """
        Get specific token by index.
        
        Args:
            index: Token index (1-based)
            
        Returns:
            Bot token string or None if not found
        """
        return self.tokens.get(index)

    def get_primary_token(self) -> Optional[str]:
        """
        Get the primary (first) token.
        
        Returns:
            Primary bot token or None if no tokens available
        """
        return self.tokens.get(1)

    def validate_tokens(self) -> List[int]:
        """
        Validate all parsed tokens.
        
        Returns:
            List of valid token indices
        """
        valid_indices = []
        
        for index, token in self.tokens.items():
            if self._is_valid_token(token):
                valid_indices.append(index)
            else:
                logger.warning(f"Invalid token format at index {index}")
                
        logger.info(f"Validated {len(valid_indices)} out of {len(self.tokens)} tokens")
        return valid_indices

    @staticmethod
    def _is_valid_token(token: str) -> bool:
        """
        Basic validation for Telegram bot token format.
        
        Args:
            token: Bot token to validate
            
        Returns:
            True if token format appears valid
        """
        if not token or not isinstance(token, str):
            return False
            
        # Basic Telegram bot token format: digits:alphanumeric
        parts = token.split(':')
        if len(parts) != 2:
            return False
            
        bot_id, auth_token = parts
        return (bot_id.isdigit() and 
                len(auth_token) >= 35 and 
                auth_token.replace('_', '').replace('-', '').isalnum())

    def clear_tokens(self) -> None:
        """Clear all cached tokens."""
        self.tokens.clear()
        logger.debug("Cleared all cached tokens")

    def __len__(self) -> int:
        """Return number of parsed tokens."""
        return len(self.tokens)

    def __bool__(self) -> bool:
        """Return True if any tokens are available."""
        return bool(self.tokens)

    def __repr__(self) -> str:
        """String representation of TokenParser."""
        return f"TokenParser(tokens={len(self.tokens)}, config_file={self.config_file})"


# Convenience function for quick token parsing
def get_multi_tokens() -> Dict[int, str]:
    """
    Quick function to get multi-client tokens from environment.
    
    Returns:
        Dict mapping client index to bot token
    """
    parser = TokenParser()
    return parser.parse_from_env()
