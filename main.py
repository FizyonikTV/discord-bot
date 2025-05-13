import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime, timezone
from config.config import get_token, INTENTS, IZIN_VERILEN_ROLLER
from utils.helpers import command_check, COMMAND_CHANNELS
from webdashboard import Dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class LunarisBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=INTENTS,
            case_insensitive=True
        )
        self.start_time = datetime.now(timezone.utc)

    async def add_cog(self, cog):
        """Add checks to all commands in a cog."""
        for cmd in cog.get_commands():
            cmd.add_check(command_check())
        await super().add_cog(cog)

    async def setup_hook(self):
        """Initial setup and loading cogs."""
        # Önce hangi cog'lar var görelim
        cogs_to_load = [f for f in os.listdir('./cogs') if f.endswith('.py') and not f.startswith('__')]
        
        # Sorunlu cog'ları atla
        skip_cogs = ['image_mod.py']
        cogs_to_load = [cog for cog in cogs_to_load if cog not in skip_cogs]
        
        print(f"Yüklenecek {len(cogs_to_load)} cog bulundu: {cogs_to_load}")
        
        for filename in cogs_to_load:
            try:
                print(f"Yüklemeye çalışılıyor: {filename}...")
                await self.load_extension(f'cogs.{filename[:-3]}')
                logging.info(f'✅ Loaded cog: {filename}')
                print(f'✅ Loaded cog: {filename}')
            except Exception as e:
                logging.error(f'❌ Failed to load cog {filename}: {e}')
                print(f'❌ Failed to load cog {filename}: {e}')
                # Hata ayrıntılarını göster
                import traceback
                traceback.print_exc()
        
        # Dashboard başlatma
        try:
            # Config'den client ID ve secret değerlerini alın
            from config.config import DASHBOARD_CLIENT_ID, DASHBOARD_CLIENT_SECRET
            
            if not DASHBOARD_CLIENT_ID or not DASHBOARD_CLIENT_SECRET or DASHBOARD_CLIENT_ID == "YOUR_CLIENT_ID_HERE":
                logging.warning("Discord OAuth2 credentials not configured correctly. Dashboard will not be started.")
                print("⚠️ Dashboard not started: OAuth2 credentials missing. Update config.py with your credentials.")
                return
                
            self.dashboard = Dashboard(self, DASHBOARD_CLIENT_ID, DASHBOARD_CLIENT_SECRET)
            await self.dashboard.start()
        except ImportError:
            logging.error("Could not import dashboard configuration from config.py")
            print("❌ Dashboard not started: Missing configuration in config.py")
        except Exception as e:
            logging.error(f"Failed to start dashboard: {e}")
            print(f"❌ Failed to start dashboard: {e}")

    async def on_ready(self):
        """Triggered when the bot is ready."""
        logging.info(f"✅ Bot is ready as {self.user}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.streaming,
                name="🦊 LunarisBot | Moderasyon Botu",
                url="https://www.twitch.tv/eonjinwoo"
            )
        )
        print(f'✅ Bot {self.user} olarak giriş yaptı!')

async def main():
    """Main entry point for the bot."""
    token = get_token()

    async with LunarisBot() as bot:
        # Start the bot
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())