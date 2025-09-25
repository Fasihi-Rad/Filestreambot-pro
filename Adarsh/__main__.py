# (c) Fasihi-Rad
import os
import sys
import glob
import asyncio
import logging
import importlib
from pathlib import Path
from typing import List

from pyrogram import idle
from pyrogram.errors import ApiIdInvalid, ApiIdPublishedFlood, AccessTokenInvalid

from .bot import StreamBot
from .vars import Var
from .config import config
from aiohttp import web
from .server import web_server
from .utils.keepalive import ping_server

try:
    from Adarsh.bot.clients import initialize_clients
except ImportError:
    async def initialize_clients():
        """Fallback if clients module not available"""
        logger.info("Multi-client support not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

# Reduce log noise from third-party libraries
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting FileStream Bot...")

# Plugin discovery
PLUGIN_PATTERN = "Adarsh/bot/plugins/*.py"
plugin_files = glob.glob(PLUGIN_PATTERN)


async def load_plugins() -> int:
    """
    Dynamically load all bot plugins.
    
    Returns:
        Number of plugins loaded successfully
    """
    loaded_count = 0
    failed_plugins = []
    
    logger.info("📚 Loading bot plugins...")
    
    for plugin_file in plugin_files:
        try:
            # Extract plugin name from file path
            plugin_path = Path(plugin_file)
            plugin_name = plugin_path.stem
            
            # Build import path
            import_path = f".plugins.{plugin_name}"
            plugins_dir = Path(f"Adarsh/bot/plugins/{plugin_name}.py")
            
            # Load the plugin module
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            if spec and spec.loader:
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                # Register in sys.modules
                sys.modules[f"Adarsh.bot.plugins.{plugin_name}"] = plugin_module
                
                loaded_count += 1
                logger.info(f"✅ Loaded plugin: {plugin_name}")
            else:
                failed_plugins.append(plugin_name)
                logger.error(f"❌ Failed to load plugin spec: {plugin_name}")
                
        except Exception as e:
            plugin_name = Path(plugin_file).stem
            failed_plugins.append(plugin_name)
            logger.error(f"❌ Error loading plugin {plugin_name}: {e}")
    
    if failed_plugins:
        logger.warning(f"⚠️ Failed to load {len(failed_plugins)} plugins: {failed_plugins}")
    
    logger.info(f"📚 Plugin loading complete: {loaded_count} loaded, {len(failed_plugins)} failed")
    return loaded_count


async def start_services() -> None:
    """
    Start all bot services in correct order.
    """
    try:
        # Start the bot
        logger.info("🤖 Initializing Telegram Bot...")
        StreamBot.start()
        
        # Get bot info
        bot_info = await StreamBot.get_me()
        StreamBot.username = bot_info.username
        logger.info(f"✅ Bot started: @{bot_info.username}")
        
        # Initialize clients
        logger.info("👥 Initializing additional clients...")
        try:
            await initialize_clients()
            logger.info("✅ Additional clients initialized")
        except Exception as e:
            logger.warning(f"⚠️ Client initialization warning: {e}")
        
        # Load plugins
        plugin_count = await load_plugins()
        if plugin_count == 0:
            logger.error("❌ No plugins loaded - bot may not function properly")
        
        # Start keep-alive service if on Heroku
        if config.on_heroku:
            logger.info("💓 Starting keep-alive service...")
            asyncio.create_task(ping_server())
            logger.info("✅ Keep-alive service started")
        
        # Start web server
        logger.info("🌐 Starting web server...")
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        
        # Determine bind address
        bind_address = "0.0.0.0" if config.on_heroku else config.bind_address
        site = web.TCPSite(app_runner, bind_address, config.port)
        await site.start()
        
        # Log startup complete
        logger.info("🎉 All services started successfully!")
        logger.info("📊 Service Information:")
        logger.info(f"   🤖 Bot: {bot_info.first_name} (@{bot_info.username})")
        logger.info(f"   🌐 Server: {bind_address}:{config.port}")
        logger.info(f"   👑 Owner: {config.owner_username or 'Not set'}")
        logger.info(f"   📚 Plugins: {plugin_count}")
        
        if config.on_heroku:
            logger.info(f"   🚀 Heroku App: {config.app_name}")
            logger.info(f"   🔗 Public URL: https://{config.fqdn}")
        
        logger.info("💡 Repository: https://github.com/Fasihi-Rad/filestreambot-pro")
        logger.info("🌟 Give a star if you found this useful!")
        
        # Keep the bot running
        await idle()
        
    except ApiIdInvalid:
        logger.error("❌ Invalid API ID - check your configuration")
        sys.exit(1)
    except ApiIdPublishedFlood:
        logger.error("❌ API ID flood - wait before trying again")
        sys.exit(1)
    except AccessTokenInvalid:
        logger.error("❌ Invalid bot token - check your BOT_TOKEN")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start services: {e}")
        sys.exit(1)


async def shutdown_services() -> None:
    """
    Gracefully shutdown all services.
    """
    try:
        logger.info("🛑 Shutting down services...")
        
        if StreamBot.is_connected:
            await StreamBot.stop()
            logger.info("✅ Bot stopped")
        
        logger.info("👋 Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def main() -> None:
    """
    Main entry point for the application.
    """
    try:
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bot
        loop.run_until_complete(start_services())
        
    except KeyboardInterrupt:
        logger.info("⌨️ KeyboardInterrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        # Cleanup
        try:
            loop.run_until_complete(shutdown_services())
        except:
            pass
        finally:
            if not loop.is_closed():
                loop.close()
        logger.info("🏁 Application terminated")


if __name__ == '__main__':
    main()
